"""
ClinIQ Backend — FastAPI server for Cohort & Data Quality Explorer
MIMIC-IV Clinical Database Demo v2.2

Research and educational prototype only. Not for clinical use.
"""
import os
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "data" / "mimic4demo.db"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", str(PROJECT_ROOT / "data" / "schema_metadata.json"))

# Load schema metadata once at startup
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    SCHEMA_METADATA = json.load(f)

# ─── App Setup ───────────────────────────────────────────────
# This code configures the FastAPI backend for ClinIQ and enables CORS access from the frontend.
app = FastAPI(
    title="ClinIQ - Cohort & Data Quality Explorer",
    description=(
        "AI-powered tool for cohort definition and data quality inspection "
        "on MIMIC-IV Clinical Database Demo v2.2. "
        "Research and educational prototype only. Not for clinical use."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Database Helper ────────────────────────────────────────

@contextmanager
def get_db():
    """Get a read-only SQLite connection."""
    conn = sqlite3.connect(DB_PATH, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")  # Read-only safety
    try:
        yield conn
    finally:
        conn.close()


def get_table_counts():
    """Get row counts for all tables."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        counts = {}
        for table in tables:
            count = conn.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
            counts[table] = count
        return counts


# ─── Request/Response Models ────────────────────────────────

class CohortQueryRequest(BaseModel):
    text: str


class CohortExecuteRequest(BaseModel):
    sql: str


class HealthResponse(BaseModel):
    status: str
    tables_loaded: int
    patient_count: int
    database_path: str


# ─── Endpoints ──────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Health check — confirms database is loaded and accessible."""
    try:
        with get_db() as conn:
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            patients = conn.execute(
                "SELECT COUNT(DISTINCT subject_id) FROM patients"
            ).fetchone()[0]
        return HealthResponse(
            status="ok",
            tables_loaded=tables,
            patient_count=patients,
            database_path=DB_PATH,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: %s" % str(e))


@app.get("/api/schema")
def get_schema():
    """Return the full schema metadata for frontend display."""
    # Add live row counts
    counts = get_table_counts()
    tables_with_counts = []
    for table_meta in SCHEMA_METADATA.get("tables", []):
        table_copy = dict(table_meta)
        table_copy["row_count"] = counts.get(table_meta["name"], 0)
        tables_with_counts.append(table_copy)

    return {
        "database": SCHEMA_METADATA.get("database"),
        "patient_count": SCHEMA_METADATA.get("patient_count"),
        "description": SCHEMA_METADATA.get("description"),
        "tables": tables_with_counts,
        "key_relationships": SCHEMA_METADATA.get("key_relationships", []),
        "important_notes": SCHEMA_METADATA.get("important_notes", []),
    }


# ─── Quality Endpoints (Phase 2) ───────────────────────────

@app.get("/api/quality/summary")
def quality_summary():
    """Run data quality scan and return summary."""
    from backend.quality.engine import DataQualityEngine
    engine = DataQualityEngine(DB_PATH)
    flags = engine.scan_all()
    summary = engine.get_summary(flags)
    return summary


@app.get("/api/quality/scan")
def quality_scan():
    """Run full data quality scan and return all flags."""
    from backend.quality.engine import DataQualityEngine
    engine = DataQualityEngine(DB_PATH)
    flags = engine.scan_all()
    return {"flags": [f.model_dump() for f in flags], "total": len(flags)}


@app.get("/api/quality/scan/{table_name}")
def quality_scan_table(table_name: str):
    """Scan a specific table for data quality issues."""
    from backend.quality.engine import DataQualityEngine
    engine = DataQualityEngine(DB_PATH)
    flags = engine.scan_table(table_name)
    return {"flags": [f.model_dump() for f in flags], "total": len(flags)}


# ─── Coverage Endpoints (Phase 2) ──────────────────────────

@app.get("/api/coverage/summary")
def coverage_summary():
    """Return per-table coverage statistics."""
    from backend.coverage.analyzer import CoverageAnalyzer
    analyzer = CoverageAnalyzer(DB_PATH)
    return analyzer.get_summary()


@app.get("/api/coverage/patient/{subject_id}")
def coverage_patient(subject_id: int):
    """Return data coverage for a specific patient."""
    from backend.coverage.analyzer import CoverageAnalyzer
    analyzer = CoverageAnalyzer(DB_PATH)
    return analyzer.get_patient_coverage(subject_id)


# ─── Cohort Endpoints (Phase 3) ────────────────────────────

@app.get("/api/cohort/templates")
def cohort_templates():
    """Return pre-built cohort query templates."""
    from backend.cohort.templates import TEMPLATES
    return {"templates": TEMPLATES}


@app.post("/api/cohort/query")
async def cohort_query(request: CohortQueryRequest):
    """Translate natural language to SQL, validate, execute, and return results."""
    from backend.cohort.llm_service import CohortLLMService
    from backend.cohort.query_validator import validate_sql
    from backend.cohort.query_executor import execute_cohort_query

    # 1. Translate NL to structured query via GPT-5 mini
    llm_service = CohortLLMService(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        schema_metadata=SCHEMA_METADATA,
        model=os.getenv("LLM_MODEL", "gpt-5-mini"),
    )

    try:
        llm_result = await llm_service.translate(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="LLM service error: %s" % str(e))

    # Check for abstention
    if llm_result.get("abstain"):
        return {
            "abstain": True,
            "reason": llm_result.get("reason", "Cannot answer from available data."),
            "ai_generated": True,
        }

    # 2. Validate the generated SQL
    sql = llm_result.get("sql", "")
    validation = validate_sql(sql, SCHEMA_METADATA)
    if not validation["valid"]:
        return {
            "abstain": True,
            "reason": "Generated SQL failed validation: %s" % "; ".join(validation["errors"]),
            "sql": sql,
            "ai_generated": True,
        }

    # 3. Execute the query
    try:
        results = execute_cohort_query(sql, DB_PATH)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Query execution error: %s" % str(e))

    return {
        "sql": sql,
        "inclusion_criteria": llm_result.get("inclusion_criteria", []),
        "exclusion_criteria": llm_result.get("exclusion_criteria", []),
        "tables_used": llm_result.get("tables_used", validation.get("tables_used", [])),
        "explanation": llm_result.get("explanation", ""),
        "results": results,
        "ai_generated": True,
        "abstain": False,
    }


@app.post("/api/cohort/execute")
def cohort_execute(request: CohortExecuteRequest):
    """Execute a user-provided or edited SQL query."""
    from backend.cohort.query_validator import validate_sql
    from backend.cohort.query_executor import execute_cohort_query

    validation = validate_sql(request.sql, SCHEMA_METADATA)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail="SQL validation failed: %s" % "; ".join(validation["errors"]),
        )

    try:
        results = execute_cohort_query(request.sql, DB_PATH)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Query execution error: %s" % str(e))

    return {
        "sql": request.sql,
        "tables_used": validation.get("tables_used", []),
        "results": results,
        "ai_generated": False,
        "abstain": False,
    }


# ─── Run ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
