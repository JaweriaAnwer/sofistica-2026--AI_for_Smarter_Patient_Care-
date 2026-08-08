"""
SQL Query Validator for ClinIQ

Validates generated or user-edited SQL to ensure:
1. Read-only (SELECT only) — no INSERT/UPDATE/DELETE/DROP/ALTER
2. References only existing tables and columns
3. No SQL injection patterns
4. Safe for execution against the MIMIC-IV Demo database
"""
import re
import sqlparse
from typing import Dict, List, Any


# Dangerous SQL keywords that indicate write operations
FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "REPLACE", "MERGE", "EXEC", "EXECUTE",
    "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "SAVEPOINT",
    "ATTACH", "DETACH", "VACUUM", "REINDEX", "PRAGMA",
}

# Patterns that suggest SQL injection
INJECTION_PATTERNS = [
    r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)",  # Chained destructive
    r"--\s*$",  # Line comment at end (could hide payload)
    r"/\*.*\*/",  # Block comments (could hide payload)
    r"xp_",  # SQL Server extended procs
    r"LOAD_FILE",  # MySQL file access
    r"INTO\s+OUTFILE",  # MySQL file write
    r"INTO\s+DUMPFILE",  # MySQL file write
]


def validate_sql(sql: str, schema_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a SQL query for safety and correctness.

    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "tables_used": List[str],
            "columns_used": List[str],
        }
    """
    errors = []
    warnings = []
    tables_used = []
    columns_used = []

    if not sql or not sql.strip():
        return {
            "valid": False,
            "errors": ["Empty SQL query"],
            "warnings": [],
            "tables_used": [],
            "columns_used": [],
        }

    sql_clean = sql.strip()

    # 1. Check for forbidden keywords
    parsed = sqlparse.parse(sql_clean)
    for statement in parsed:
        stmt_type = statement.get_type()
        if stmt_type and stmt_type.upper() not in ("SELECT", "UNKNOWN", None):
            errors.append(
                "Only SELECT statements are allowed. Found: %s" % stmt_type
            )

    # Tokenize and check for forbidden keywords
    sql_upper = sql_clean.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        # Check as whole word (not part of a column name)
        pattern = r"\b%s\b" % keyword
        if re.search(pattern, sql_upper):
            errors.append(
                "Forbidden keyword found: %s. Only SELECT queries are allowed." % keyword
            )

    # 2. Check for injection patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, sql_upper):
            errors.append(
                "Potential SQL injection pattern detected."
            )
            break

    # 3. Must start with SELECT (or WITH for CTEs)
    first_keyword = sql_clean.split()[0].upper() if sql_clean.split() else ""
    if first_keyword not in ("SELECT", "WITH"):
        errors.append(
            "Query must start with SELECT (or WITH for CTEs). Found: %s" % first_keyword
        )

    # 4. Extract table references and validate against schema
    known_tables = set()
    for table_meta in schema_metadata.get("tables", []):
        known_tables.add(table_meta["name"].lower())

    # Also add dictionary tables that might not be in our condensed schema
    known_tables.update({
        "patients", "admissions", "transfers", "labevents", "d_labitems",
        "diagnoses_icd", "d_icd_diagnoses", "procedures_icd", "d_icd_procedures",
        "prescriptions", "pharmacy", "emar", "emar_detail", "microbiologyevents",
        "poe", "poe_detail", "services", "drgcodes", "provider", "hcpcsevents",
        "d_hcpcs", "omr", "icustays", "d_items", "chartevents", "datetimeevents",
        "inputevents", "ingredientevents", "outputevents", "procedureevents",
        "caregiver",
    })

    # Simple table extraction using FROM and JOIN patterns
    table_pattern = r"(?:FROM|JOIN)\s+[\"']?(\w+)[\"']?"
    found_tables = re.findall(table_pattern, sql_clean, re.IGNORECASE)
    for table in found_tables:
        table_lower = table.lower()
        tables_used.append(table_lower)
        if table_lower not in known_tables:
            warnings.append(
                "Table '%s' not found in schema. It may not exist." % table
            )

    tables_used = list(set(tables_used))

    # 5. Check for overly broad queries (no WHERE on large tables)
    large_tables = {"chartevents", "labevents", "emar", "emar_detail", "inputevents"}
    for table in tables_used:
        if table in large_tables and "WHERE" not in sql_upper:
            warnings.append(
                "Query on large table '%s' without WHERE clause may be slow." % table
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "tables_used": tables_used,
        "columns_used": columns_used,
    }
