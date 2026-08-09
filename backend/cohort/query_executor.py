"""
Query Executor for ClinIQ

Executes **validated SQL queries** on the MIMIC-IV Demo database and supplements the results with **demographic insights**.

"""
import sqlite3
import time
from typing import Dict, Any, List


def execute_cohort_query(sql: str, db_path: str) -> Dict[str, Any]:
    """
    Execute a validated SQL query and return enriched results.

    Returns:
        {
            "patient_count": int,
            "patient_ids": List[int],
            "sample_rows": List[dict],
            "execution_time_ms": float,
            "demographics": {
                "age_distribution": [...],
                "gender_counts": {...},
                "mortality_rate": float
            },
            "columns": List[str]
        }
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    start_time = time.time()

    try:
        # Execute the query
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        execution_time_ms = (time.time() - start_time) * 1000

        # Convert to list of dicts
        result_rows = [dict(row) for row in rows]

        # Extract unique patient IDs
        patient_ids = set()
        for row in result_rows:
            if "subject_id" in row and row["subject_id"] is not None:
                patient_ids.add(int(row["subject_id"]))

        patient_ids = sorted(patient_ids)

        # Limit sample rows for response size
        sample_rows = result_rows[:50]

        # Compute demographics if we have patient IDs
        demographics = _compute_demographics(conn, patient_ids)

        return {
            "patient_count": len(patient_ids) if patient_ids else len(result_rows),
            "patient_ids": patient_ids,
            "total_rows": len(result_rows),
            "sample_rows": sample_rows,
            "execution_time_ms": round(execution_time_ms, 1),
            "demographics": demographics,
            "columns": columns,
        }
    except Exception as e:
        raise Exception("Query execution failed: %s" % str(e))
    finally:
        conn.close()


def _compute_demographics(conn: sqlite3.Connection, patient_ids: List[int]) -> Dict[str, Any]:
    """Compute demographic summary for a set of patient IDs."""
    if not patient_ids:
        return {
            "age_distribution": [],
            "gender_counts": {},
            "mortality_rate": 0.0,
            "insurance_counts": {},
            "admission_type_counts": {},
        }

    placeholders = ",".join(["?"] * len(patient_ids))

    # Age distribution
    age_distribution = []
    try:
        rows = conn.execute(
            "SELECT anchor_age FROM patients WHERE subject_id IN (%s)" % placeholders,
            patient_ids
        ).fetchall()

        ages = [r[0] for r in rows if r[0] is not None]
        if ages:
            age_bins = [
                ("18-29", 18, 30),
                ("30-44", 30, 45),
                ("45-59", 45, 60),
                ("60-74", 60, 75),
                ("75-89", 75, 90),
                ("90+", 90, 200),
            ]
            for label, low, high in age_bins:
                count = sum(1 for a in ages if low <= a < high)
                if count > 0:
                    age_distribution.append({"range": label, "count": count})
    except sqlite3.OperationalError:
        pass

    # Gender counts
    gender_counts = {}
    try:
        rows = conn.execute(
            "SELECT gender, COUNT(*) FROM patients WHERE subject_id IN (%s) GROUP BY gender" % placeholders,
            patient_ids
        ).fetchall()
        gender_counts = {r[0]: r[1] for r in rows}
    except sqlite3.OperationalError:
        pass

    # Mortality rate
    mortality_rate = 0.0
    try:
        total = conn.execute(
            "SELECT COUNT(DISTINCT a.subject_id) FROM admissions a WHERE a.subject_id IN (%s)" % placeholders,
            patient_ids
        ).fetchone()[0]
        deaths = conn.execute(
            "SELECT COUNT(DISTINCT a.subject_id) FROM admissions a WHERE a.subject_id IN (%s) AND a.hospital_expire_flag = 1" % placeholders,
            patient_ids
        ).fetchone()[0]
        mortality_rate = round(deaths / total * 100, 1) if total > 0 else 0.0
    except sqlite3.OperationalError:
        pass

    # Insurance distribution
    insurance_counts = {}
    try:
        rows = conn.execute(
            "SELECT insurance, COUNT(DISTINCT subject_id) FROM admissions WHERE subject_id IN (%s) GROUP BY insurance" % placeholders,
            patient_ids
        ).fetchall()
        insurance_counts = {r[0]: r[1] for r in rows if r[0]}
    except sqlite3.OperationalError:
        pass

    # Admission type distribution
    admission_type_counts = {}
    try:
        rows = conn.execute(
            "SELECT admission_type, COUNT(*) FROM admissions WHERE subject_id IN (%s) GROUP BY admission_type" % placeholders,
            patient_ids
        ).fetchall()
        admission_type_counts = {r[0]: r[1] for r in rows if r[0]}
    except sqlite3.OperationalError:
        pass

    return {
        "age_distribution": age_distribution,
        "gender_counts": gender_counts,
        "mortality_rate": mortality_rate,
        "insurance_counts": insurance_counts,
        "admission_type_counts": admission_type_counts,
    }
