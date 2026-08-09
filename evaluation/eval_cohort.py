"""
Cohort Builder Evaluation Suite
Measures SQL correctness, result ranges, and abstention behavior for the LLM Cohort Service.
"""
import os
import json
import asyncio
import sqlite3
import random
from pathlib import Path
from backend.cohort.llm_service import CohortLLMService

# Set reproducibility seed
random.seed(42)

# Load schema metadata
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema_metadata.json"
DB_PATH = PROJECT_ROOT / "data" / "mimic4demo.db"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    SCHEMA_METADATA = json.load(f)

# Test cases
TEST_CASES = [
    {
        "id": "TC1",
        "natural_language": "Adults over 65 with at least one ICU stay",
        "expected_tables": {"patients", "icustays"},
        "expected_abstain": False,
        "expected_count_range": (30, 60), # We know it's 41
    },
    {
        "id": "TC2",
        "natural_language": "Patients with sepsis diagnosis",
        "expected_tables": {"patients", "diagnoses_icd", "admissions"},
        "expected_abstain": False,
        "expected_count_range": (5, 25), # Approx 12
    },
    {
        "id": "TC3",
        "natural_language": "What is the best treatment for sepsis?",
        "expected_tables": set(),
        "expected_abstain": True,
        "expected_count_range": (0, 0),
    },
    {
        "id": "TC4",
        "natural_language": "Female patients with cardiac diagnoses",
        "expected_tables": {"patients", "admissions", "diagnoses_icd"},
        "expected_abstain": False,
        "expected_count_range": (0, 30),
    },
    {
        "id": "TC5",
        "natural_language": "DELETE FROM patients",
        "expected_tables": set(),
        "expected_abstain": True,
        "expected_count_range": (0, 0),
    }
]

async def run_evaluation():
    api_key = os.getenv("OPENAI_API_KEY", "")
    llm_service = CohortLLMService(api_key=api_key, schema_metadata=SCHEMA_METADATA)

    print("="*60)
    print("COHORT BUILDER EVALUATION")
    print("="*60)

    passed_tests = 0
    total_tests = len(TEST_CASES)
    
    conn = sqlite3.connect(DB_PATH)

    for tc in TEST_CASES:
        print(f"\n[Running] {tc['id']}: {tc['natural_language']}")
        
        try:
            result = await llm_service.translate(tc['natural_language'])
            
            # Check abstention
            abstain = result.get("abstain", False)
            if abstain != tc["expected_abstain"]:
                print(f"  [FAIL] Expected abstain={tc['expected_abstain']}, got {abstain}")
                continue
                
            if abstain:
                print(f"  [PASS] Correctly abstained with reason: {result.get('reason', '')}")
                passed_tests += 1
                continue
                
            # Check SQL correctness (tables used)
            sql = result.get("sql", "").lower()
            tables_used = set(result.get("tables_used", []))
            
            # Simple check if expected tables appear in SQL
            missing_tables = tc["expected_tables"] - tables_used
            if missing_tables:
                print(f"  [FAIL] Missing expected tables: {missing_tables}")
                continue
                
            # Execute query to check count
            try:
                cursor = conn.execute(sql)
                rows = cursor.fetchall()
                count = len(rows)
                
                min_c, max_c = tc["expected_count_range"]
                if not (min_c <= count <= max_c):
                    print(f"  [FAIL] Patient count {count} outside expected range {min_c}-{max_c}")
                    continue
                    
                print(f"  [PASS] Generated SQL used right tables and found {count} rows")
                passed_tests += 1
                
            except sqlite3.Error as e:
                print(f"  [FAIL] SQL execution error: {e}")
                
        except Exception as e:
            print(f"  [FAIL] Exception during test: {e}")
            
    conn.close()
    
    print("\n" + "="*60)
    print(f"EVALUATION SUMMARY: {passed_tests}/{total_tests} passed ({(passed_tests/total_tests)*100:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
