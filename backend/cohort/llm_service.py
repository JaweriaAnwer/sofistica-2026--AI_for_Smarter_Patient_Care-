"""
GPT-5 Mini Cohort LLM Service for ClinIQ

Architecture:
- GPT-5 mini: Understands NL questions -> translates to structured cohort criteria
- Python/SQL: Performs the actual data processing, joins, and calculations
- The LLM NEVER sees patient data, only the schema metadata
- Results are computed by the backend, then optionally explained by the LLM

This design is:
- Reliable: deterministic SQL for data operations
- Transparent: generated SQL is visible and editable
- Efficient: minimal token usage (schema only, not data)
- Safe: no patient data leaves the system
"""
import os
import json
import re
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from backend.cohort.templates import TEMPLATES


# Build few-shot examples from templates
def _build_few_shot_examples() -> str:
    examples = []
    for t in TEMPLATES[:5]:  # Use first 5 templates as examples
        examples.append(
            'User: "%s"\nResponse:\n```json\n%s\n```'
            % (
                t["natural_language"],
                json.dumps(
                    {
                        "sql": t["sql"].strip(),
                        "inclusion_criteria": t["inclusion_criteria"],
                        "exclusion_criteria": t["exclusion_criteria"],
                        "tables_used": t["tables_used"],
                        "explanation": t.get("description", ""),
                        "abstain": False,
                    },
                    indent=2,
                ),
            )
        )
    return "\n\n".join(examples)


def _build_schema_context(schema_metadata: Dict[str, Any]) -> str:
    """Build a concise schema context string for the LLM prompt."""
    lines = []
    lines.append("DATABASE: %s" % schema_metadata.get("database", "MIMIC-IV"))
    lines.append("PATIENTS: %d" % schema_metadata.get("patient_count", 100))
    lines.append("")

    for table in schema_metadata.get("tables", []):
        cols = ", ".join(
            ["%s (%s)" % (c["name"], c["type"]) for c in table.get("columns", [])]
        )
        lines.append("TABLE: %s - %s" % (table["name"], table.get("description", "")))
        lines.append("  COLUMNS: %s" % cols)
        if table.get("foreign_keys"):
            fks = ", ".join(
                [
                    "%s -> %s" % (fk["column"], fk["references"])
                    for fk in table["foreign_keys"]
                ]
            )
            lines.append("  FOREIGN KEYS: %s" % fks)
        lines.append("")

    lines.append("KEY RELATIONSHIPS:")
    for rel in schema_metadata.get("key_relationships", []):
        lines.append("  - %s" % rel)

    lines.append("")
    lines.append("IMPORTANT NOTES:")
    for note in schema_metadata.get("important_notes", []):
        lines.append("  - %s" % note)

    return "\n".join(lines)


SYSTEM_PROMPT = """You are ClinIQ, an AI assistant that translates natural language cohort definitions into SQL queries for the MIMIC-IV Clinical Database Demo v2.2.

ROLE: You ONLY translate researcher questions into structured SQL. You do NOT execute queries, analyze data, or provide clinical recommendations.

RULES:
1. Generate ONLY SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, or ALTER.
2. Always include subject_id in the SELECT for patient identification.
3. Use proper JOIN syntax with explicit ON conditions.
4. For ICD diagnoses, always specify icd_version (9 or 10). Include both versions when appropriate.
5. Use JULIANDAY() for date arithmetic in SQLite.
6. For age calculations, use anchor_age from the patients table directly (it represents age at anchor_year).
7. Join to dictionary tables (d_labitems, d_items, d_icd_diagnoses, d_icd_procedures) to get human-readable labels.
8. Always ORDER BY subject_id for consistent results.
9. If the question CANNOT be answered from the structured data (e.g., requires clinical notes, imaging, or data not in the schema), set "abstain": true and provide a reason.
10. If the question asks for clinical recommendations, diagnosis, or treatment, set "abstain": true with reason: "This is a research tool. It cannot provide clinical recommendations."
11. Do NOT send any patient data in your reasoning. Only reference schema structure.

OUTPUT FORMAT: Return a JSON object with exactly these fields:
{
  "sql": "SELECT ...",
  "inclusion_criteria": [{"description": "...", "table": "...", "condition": "..."}],
  "exclusion_criteria": [{"description": "...", "table": "...", "condition": "..."}],
  "tables_used": ["table1", "table2"],
  "explanation": "Brief explanation of the query logic",
  "abstain": false
}

If abstaining:
{
  "abstain": true,
  "reason": "Explanation of why the question cannot be answered"
}

DATABASE SCHEMA:
{schema_context}

EXAMPLES:
{few_shot_examples}
"""


class CohortLLMService:
    """
    Translates natural language cohort definitions into SQL using GPT-5 mini.
    Only schema metadata is sent to the LLM — never patient data.
    """

    def __init__(
        self, api_key: str, schema_metadata: Dict[str, Any], model: str = "gpt-5-mini"
    ):
        self.api_key = api_key
        self.schema_metadata = schema_metadata
        self.model = model
        self.schema_context = _build_schema_context(schema_metadata)
        self.few_shot_examples = _build_few_shot_examples()

        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None

    async def translate(self, natural_language: str) -> Dict[str, Any]:
        """
        Translate a natural language cohort definition to SQL.

        If the LLM API is unavailable, falls back to template matching.
        """
        # Safety check: refuse clinical recommendations
        clinical_keywords = [
            "prescribe", "treat", "diagnose patient", "best treatment",
            "should I give", "recommend", "what drug",
            "emergency", "triage",
        ]
        nl_lower = natural_language.lower()
        for kw in clinical_keywords:
            if kw in nl_lower:
                return {
                    "abstain": True,
                    "reason": (
                        "This is a research and education tool. "
                        "It cannot provide clinical recommendations, "
                        "treatment suggestions, or diagnostic guidance."
                    ),
                }

        # Try LLM first
        if self.client and self.api_key:
            try:
                return await self._call_llm(natural_language)
            except Exception as e:
                # Fall back to template matching
                print("LLM call failed, falling back to templates: %s" % str(e))

        # Fallback: template matching
        return self._template_fallback(natural_language)

    async def _call_llm(self, natural_language: str) -> Dict[str, Any]:
        """Call GPT-5 mini to translate NL to SQL."""
        system_message = SYSTEM_PROMPT.format(
            schema_context=self.schema_context,
            few_shot_examples=self.few_shot_examples,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": natural_language},
            ],
            temperature=0.1,  # Low temperature for deterministic SQL generation
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            return {
                "abstain": True,
                "reason": "LLM returned empty response.",
            }

        # Parse JSON response
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                return {
                    "abstain": True,
                    "reason": "Could not parse LLM response as JSON.",
                }

        return result

    def _template_fallback(self, natural_language: str) -> Dict[str, Any]:
        """
        Match the user's question to the closest template using keyword overlap.
        Used when the LLM API is unavailable.
        """
        nl_lower = natural_language.lower()
        nl_words = set(re.findall(r"\w+", nl_lower))

        best_match = None
        best_score = 0

        for template in TEMPLATES:
            # Compare against template name, description, and natural_language
            template_text = " ".join([
                template["name"].lower(),
                template["description"].lower(),
                template["natural_language"].lower(),
            ])
            template_words = set(re.findall(r"\w+", template_text))

            # Calculate Jaccard-like overlap
            overlap = len(nl_words & template_words)
            if overlap > best_score:
                best_score = overlap
                best_match = template

        if best_match and best_score >= 2:
            return {
                "sql": best_match["sql"],
                "inclusion_criteria": best_match["inclusion_criteria"],
                "exclusion_criteria": best_match["exclusion_criteria"],
                "tables_used": best_match["tables_used"],
                "explanation": (
                    "Matched to template: '%s'. %s "
                    "(Note: LLM API was unavailable, using template fallback)"
                    % (best_match["name"], best_match["description"])
                ),
                "abstain": False,
            }

        return {
            "abstain": True,
            "reason": (
                "Could not match your question to a known cohort pattern. "
                "LLM API is unavailable. Please try rephrasing or use one of the template queries."
            ),
        }
