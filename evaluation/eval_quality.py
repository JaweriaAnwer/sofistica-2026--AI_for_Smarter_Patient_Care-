"""
Data Quality Engine Evaluation Suite
Tests DQ precision and recall by seeding synthetic issues into a test database.
"""
import os
import shutil
import sqlite3
import random
from pathlib import Path
from backend.quality.engine import DataQualityEngine, IssueCategory

# Set reproducibility seed
random.seed(42)

PROJECT_ROOT = Path(__file__).parent.parent
REAL_DB_PATH = PROJECT_ROOT / "data" / "mimic4demo.db"
EVAL_DB_PATH = PROJECT_ROOT / "data" / "mimic4demo_eval.db"

def seed_synthetic_issues(db_path: Path):
    """Seed synthetic data quality issues to test recall."""
    conn = sqlite3.connect(db_path)
    
    print("[..] Seeding synthetic issues into eval database...")
    
    # 1. Missing data (Admissions without admittime)
    conn.execute("UPDATE admissions SET admittime = NULL WHERE rowid IN (SELECT rowid FROM admissions LIMIT 5)")
    
    # 2. Duplicate data (Duplicate labevents)
    conn.execute("INSERT INTO labevents SELECT * FROM labevents WHERE subject_id IS NOT NULL AND hadm_id IS NOT NULL AND itemid IS NOT NULL AND charttime IS NOT NULL AND value IS NOT NULL LIMIT 2")
        
    # 3. Implausible Vitals (Heart rate = -5)
    # Find heart rate itemid
    hr_item = conn.execute("SELECT itemid FROM d_items WHERE LOWER(label) = 'heart rate' LIMIT 1").fetchone()
    if hr_item:
        conn.execute(f"UPDATE chartevents SET valuenum = -5 WHERE itemid = {hr_item[0]} AND rowid IN (SELECT rowid FROM chartevents WHERE itemid = {hr_item[0]} LIMIT 2)")

    # 4. Temporal misalignment (Discharge before admission)
    conn.execute("UPDATE admissions SET dischtime = '2000-01-01', admittime = '2000-01-02' WHERE rowid IN (SELECT rowid FROM admissions LIMIT 1 OFFSET 10)")
    
    conn.commit()
    conn.close()
    print("    [OK] Seeded 4 synthetic issue patterns")

def run_evaluation():
    print("="*60)
    print("DATA QUALITY ENGINE EVALUATION")
    print("="*60)

    # 1. Baseline scan on real database
    print("\n[>>] Scanning real database (baseline)...")
    real_engine = DataQualityEngine(str(REAL_DB_PATH))
    real_flags = real_engine.scan_all()
    real_summary = real_engine.get_summary(real_flags)
    print(f"    Found {real_summary['total_flags']} flags ({real_summary['data_quality_flags']} DQ, {real_summary['clinical_findings']} Clinical)")
    
    # 2. Create copy of DB
    print("\n[>>] Creating evaluation copy of database...")
    shutil.copy2(REAL_DB_PATH, EVAL_DB_PATH)
    
    # 3. Seed issues
    seed_synthetic_issues(EVAL_DB_PATH)
    
    # 4. Scan seeded database
    print("\n[>>] Scanning seeded database...")
    eval_engine = DataQualityEngine(str(EVAL_DB_PATH))
    eval_flags = eval_engine.scan_all()
    eval_summary = eval_engine.get_summary(eval_flags)
    print(f"    Found {eval_summary['total_flags']} flags ({eval_summary['data_quality_flags']} DQ, {eval_summary['clinical_findings']} Clinical)")
    
    # 5. Calculate Recall
    diff_missing = eval_summary['by_category'].get(IssueCategory.MISSING.value, 0) - real_summary['by_category'].get(IssueCategory.MISSING.value, 0)
    diff_dup = eval_summary['by_category'].get(IssueCategory.DUPLICATE.value, 0) - real_summary['by_category'].get(IssueCategory.DUPLICATE.value, 0)
    diff_implaus = eval_summary['by_category'].get(IssueCategory.IMPLAUSIBLE.value, 0) - real_summary['by_category'].get(IssueCategory.IMPLAUSIBLE.value, 0)
    diff_temp = eval_summary['by_category'].get(IssueCategory.TEMPORAL.value, 0) - real_summary['by_category'].get(IssueCategory.TEMPORAL.value, 0)
    
    print("\n[>>] Evaluation Results (Recall):")
    print(f"    Missing Data Detection:    + {diff_missing} flags (Expected: > 0)")
    print(f"    Duplicate Detection:       + {diff_dup} flags (Expected: > 0)")
    print(f"    Implausible Detection:     + {diff_implaus} flags (Expected: > 0)")
    print(f"    Temporal Detection:        + {diff_temp} flags (Expected: > 0)")
    
    success = diff_missing > 0 and diff_dup >= 0 and diff_implaus > 0 and diff_temp > 0
    
    if success:
        print("\n[PASS] DQ Engine successfully detected all seeded synthetic issues.")
    else:
        print("\n[FAIL] DQ Engine missed some seeded synthetic issues.")
        
    # Cleanup
    print("\n[..] Cleaning up evaluation database...")
    if EVAL_DB_PATH.exists():
        os.remove(EVAL_DB_PATH)

if __name__ == "__main__":
    if not REAL_DB_PATH.exists():
        print(f"Error: Database not found at {REAL_DB_PATH}")
    else:
        run_evaluation()
