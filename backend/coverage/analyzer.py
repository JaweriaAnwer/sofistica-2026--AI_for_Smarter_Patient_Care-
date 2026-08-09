"""
Coverage & Provenance Analyzer for MIMIC-IV Demo v2.2

Provides per-table statistics, per-patient measurement coverage,
and data provenance tracing back to source tables/columns/rows.
"""
import sqlite3
from typing import Dict, Any, List


class CoverageAnalyzer:
    """Analyzes measurement availability and data completeness patterns."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_summary(self) -> Dict[str, Any]:
        """Return per-table coverage statistics."""
        conn = self._connect()
        tables_info = []

        # Get all tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row[0] for row in cursor.fetchall()]

        for table in table_names:
            try:
                # Row count
                row_count = conn.execute(
                    'SELECT COUNT(*) FROM "%s"' % table
                ).fetchone()[0]

                # Column info
                pragma = conn.execute('PRAGMA table_info("%s")' % table).fetchall()
                columns = [{"name": col[1], "type": col[2]} for col in pragma]
                column_count = len(columns)

                # Null rates per column
                null_rates = {}
                for col in columns:
                    if row_count > 0:
                        null_count = conn.execute(
                            'SELECT COUNT(*) FROM "%s" WHERE "%s" IS NULL' % (table, col["name"])
                        ).fetchone()[0]
                        null_rates[col["name"]] = round(null_count / row_count, 4)
                    else:
                        null_rates[col["name"]] = 0.0

                # Patient count (if subject_id exists)
                patient_count = 0
                col_names = [c["name"] for c in columns]
                if "subject_id" in col_names:
                    patient_count = conn.execute(
                        'SELECT COUNT(DISTINCT subject_id) FROM "%s"' % table
                    ).fetchone()[0]

                # Unique value counts for key columns
                unique_counts = {}
                for col in columns:
                    if col["name"] in ("subject_id", "hadm_id", "stay_id", "itemid", "icd_code"):
                        unique_counts[col["name"]] = conn.execute(
                            'SELECT COUNT(DISTINCT "%s") FROM "%s" WHERE "%s" IS NOT NULL' % (
                                col["name"], table, col["name"]
                            )
                        ).fetchone()[0]

                tables_info.append({
                    "table": table,
                    "row_count": row_count,
                    "column_count": column_count,
                    "columns": columns,
                    "null_rates": null_rates,
                    "patient_count": patient_count,
                    "unique_counts": unique_counts,
                })
            except sqlite3.OperationalError:
                tables_info.append({
                    "table": table,
                    "row_count": 0,
                    "column_count": 0,
                    "columns": [],
                    "null_rates": {},
                    "patient_count": 0,
                    "unique_counts": {},
                })

        conn.close()
        return {"tables": tables_info}

    def get_patient_coverage(self, subject_id: int) -> Dict[str, Any]:
        """Return data coverage for a specific patient across all tables."""
        conn = self._connect()

        # Tables that contain patient-level data
        patient_tables = [
            ("admissions", "subject_id"),
            ("transfers", "subject_id"),
            ("diagnoses_icd", "subject_id"),
            ("procedures_icd", "subject_id"),
            ("labevents", "subject_id"),
            ("prescriptions", "subject_id"),
            ("emar", "subject_id"),
            ("pharmacy", "subject_id"),
            ("microbiologyevents", "subject_id"),
            ("poe", "subject_id"),
            ("services", "subject_id"),
            ("drgcodes", "subject_id"),
            ("icustays", "subject_id"),
            ("chartevents", "subject_id"),
            ("inputevents", "subject_id"),
            ("outputevents", "subject_id"),
            ("procedureevents", "subject_id"),
            ("datetimeevents", "subject_id"),
            ("ingredientevents", "subject_id"),
            ("omr", "subject_id"),
            ("hcpcsevents", "subject_id"),
        ]

        coverage = []
        for table, id_col in patient_tables:
            try:
                count = conn.execute(
                    'SELECT COUNT(*) FROM "%s" WHERE "%s" = ?' % (table, id_col),
                    (subject_id,)
                ).fetchone()[0]
                coverage.append({
                    "table": table,
                    "row_count": count,
                    "has_data": count > 0,
                })
            except sqlite3.OperationalError:
                coverage.append({
                    "table": table,
                    "row_count": 0,
                    "has_data": False,
                })

        # Get patient demographics
        patient_info = {}
        try:
            row = conn.execute(
                "SELECT * FROM patients WHERE subject_id = ?", (subject_id,)
            ).fetchone()
            if row:
                patient_info = dict(row)
        except sqlite3.OperationalError:
            pass

        # Get admission count
        admission_count = 0
        try:
            admission_count = conn.execute(
                "SELECT COUNT(*) FROM admissions WHERE subject_id = ?", (subject_id,)
            ).fetchone()[0]
        except sqlite3.OperationalError:
            pass

        # Get list of all patient IDs for the dropdown
        all_patients = []
        try:
            rows = conn.execute(
                "SELECT subject_id, gender, anchor_age FROM patients ORDER BY subject_id"
            ).fetchall()
            all_patients = [dict(r) for r in rows]
        except sqlite3.OperationalError:
            pass

        conn.close()
        return {
            "subject_id": subject_id,
            "patient_info": patient_info,
            "admission_count": admission_count,
            "coverage": coverage,
            "all_patients": all_patients,
        }

    def get_provenance(self, table: str, column: str, row_id: int) -> Dict[str, Any]:
        """Trace a value back to its source."""
        conn = self._connect()
        try:
            # Get the primary key column for this table
            pragma = conn.execute('PRAGMA table_info("%s")' % table).fetchall()
            columns = [col[1] for col in pragma]

            # Try to fetch the row by rowid
            row = conn.execute(
                'SELECT * FROM "%s" WHERE rowid = ?' % table, (row_id,)
            ).fetchone()

            if row:
                return {
                    "source_table": table,
                    "source_column": column,
                    "row_id": row_id,
                    "value": dict(row).get(column),
                    "full_row": dict(row),
                    "csv_file": "mimic-iv-demo/%s/%s.csv.gz" % (
                        "icu" if table in (
                            "chartevents", "d_items", "icustays", "inputevents",
                            "outputevents", "procedureevents", "datetimeevents",
                            "ingredientevents", "caregiver"
                        ) else "hosp",
                        table
                    ),
                }
            return {"error": "Row not found"}
        except sqlite3.OperationalError as e:
            return {"error": str(e)}
        finally:
            conn.close()
