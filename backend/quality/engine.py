"""
Data Quality Engine for MIMIC-IV Demo v2.2

Scans tables for: missing data, duplicates, implausible values,
temporal misalignments, unit inconsistencies, and orphaned foreign keys.

Key design principles:
- NEVER modifies source data
- Distinguishes data-quality flags from possible clinical findings
- All suggested corrections are documented and reversible
- Rules are explicit and auditable
"""
import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel

from backend.quality.clinical_ranges import get_vital_range, get_lab_range


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    MISSING = "MISSING"
    DUPLICATE = "DUPLICATE"
    IMPLAUSIBLE = "IMPLAUSIBLE"
    TEMPORAL = "TEMPORAL"
    UNIT_INCONSISTENCY = "UNIT_INCONSISTENCY"
    ORPHAN_FK = "ORPHAN_FK"
    CODING_PATTERN = "CODING_PATTERN"


class QualityFlag(BaseModel):
    """A single data quality issue detected by the engine."""
    id: str
    rule_id: str
    table: str
    column: Optional[str] = None
    issue_type: IssueCategory
    severity: IssueSeverity
    description: str
    affected_row_count: int = 0
    sample_values: List[str] = []
    suggested_fix: str = ""
    is_clinical_finding: bool = False
    reversible: bool = True


class DataQualityEngine:
    """
    Scans MIMIC-IV Demo SQLite database for data quality issues.
    All checks are read-only. No data is modified.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def scan_all(self) -> List[QualityFlag]:
        """Run all quality checks across all tables."""
        flags = []
        flags.extend(self._check_missing_data())
        flags.extend(self._check_duplicates())
        flags.extend(self._check_temporal_issues())
        flags.extend(self._check_implausible_vitals())
        flags.extend(self._check_implausible_labs())
        flags.extend(self._check_unit_inconsistencies())
        flags.extend(self._check_orphan_foreign_keys())
        flags.extend(self._check_icd_coding_patterns())
        return flags

    def scan_table(self, table_name: str) -> List[QualityFlag]:
        """Run quality checks for a specific table only."""
        all_flags = self.scan_all()
        return [f for f in all_flags if f.table == table_name]

    def get_summary(self, flags: List[QualityFlag]) -> Dict[str, Any]:
        """Aggregate flags into a summary."""
        by_severity = {"critical": 0, "warning": 0, "info": 0}
        by_category = {}
        by_table = {}

        for f in flags:
            by_severity[f.severity.value] += 1
            by_category[f.issue_type.value] = by_category.get(f.issue_type.value, 0) + 1
            by_table[f.table] = by_table.get(f.table, 0) + 1

        return {
            "total_flags": len(flags),
            "by_severity": by_severity,
            "by_category": by_category,
            "by_table": by_table,
            "clinical_findings": sum(1 for f in flags if f.is_clinical_finding),
            "data_quality_flags": sum(1 for f in flags if not f.is_clinical_finding),
        }

    # ─── Missing Data Checks ────────────────────────────────

    def _check_missing_data(self) -> List[QualityFlag]:
        """Check for high null rates in key columns."""
        flags = []
        conn = self._connect()

        # Define critical columns that should rarely be null
        critical_columns = [
            ("admissions", "admittime", 0.0),
            ("admissions", "dischtime", 0.0),
            ("admissions", "admission_type", 0.0),
            ("labevents", "value", 0.05),  # Allow up to 5% null (pending results)
            ("labevents", "charttime", 0.0),
            ("labevents", "itemid", 0.0),
            ("prescriptions", "drug", 0.05),
            ("prescriptions", "starttime", 0.1),
            ("chartevents", "value", 0.05),
            ("chartevents", "charttime", 0.0),
            ("icustays", "intime", 0.0),
            ("icustays", "outtime", 0.0),
            ("diagnoses_icd", "icd_code", 0.0),
            ("patients", "gender", 0.0),
            ("patients", "anchor_age", 0.0),
        ]

        for table, column, threshold in critical_columns:
            try:
                total = conn.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
                if total == 0:
                    continue
                null_count = conn.execute(
                    'SELECT COUNT(*) FROM "%s" WHERE "%s" IS NULL OR TRIM("%s") = \'\'' % (table, column, column)
                ).fetchone()[0]
                null_rate = null_count / total

                if null_rate > threshold:
                    severity = IssueSeverity.CRITICAL if null_rate > 0.2 else (
                        IssueSeverity.WARNING if null_rate > 0.05 else IssueSeverity.INFO
                    )
                    flags.append(QualityFlag(
                        id=str(uuid.uuid4())[:8],
                        rule_id="MISSING_001",
                        table=table,
                        column=column,
                        issue_type=IssueCategory.MISSING,
                        severity=severity,
                        description="%d of %d rows (%.1f%%) have NULL or empty '%s'" % (
                            null_count, total, null_rate * 100, column
                        ),
                        affected_row_count=null_count,
                        sample_values=["NULL rate: %.2f%%" % (null_rate * 100)],
                        suggested_fix="Investigate why '%s' is missing. Do not impute without documenting the rule." % column,
                        is_clinical_finding=False,
                    ))
            except sqlite3.OperationalError:
                pass  # Table or column doesn't exist

        conn.close()
        return flags

    # ─── Duplicate Checks ───────────────────────────────────

    def _check_duplicates(self) -> List[QualityFlag]:
        """Check for exact duplicate rows in key tables."""
        flags = []
        conn = self._connect()

        # Tables and their uniqueness key columns
        dup_checks = [
            ("labevents", ["subject_id", "hadm_id", "itemid", "charttime", "value"]),
            ("diagnoses_icd", ["subject_id", "hadm_id", "icd_code", "icd_version"]),
            ("prescriptions", ["subject_id", "hadm_id", "drug", "starttime"]),
            ("chartevents", ["subject_id", "stay_id", "itemid", "charttime", "value"]),
        ]

        for table, key_cols in dup_checks:
            try:
                col_list = ", ".join(['"%s"' % c for c in key_cols])
                sql = (
                    'SELECT COUNT(*) as cnt FROM (SELECT %s, COUNT(*) as n FROM "%s" '
                    'WHERE %s GROUP BY %s HAVING COUNT(*) > 1)'
                ) % (
                    col_list, table,
                    " AND ".join(['"%s" IS NOT NULL' % c for c in key_cols]),
                    col_list
                )
                dup_count = conn.execute(sql).fetchone()[0]

                if dup_count > 0:
                    # Get sample duplicates
                    sample_sql = (
                        'SELECT %s, COUNT(*) as n FROM "%s" '
                        'WHERE %s GROUP BY %s HAVING COUNT(*) > 1 LIMIT 3'
                    ) % (col_list, table,
                         " AND ".join(['"%s" IS NOT NULL' % c for c in key_cols]),
                         col_list)
                    samples = conn.execute(sample_sql).fetchall()
                    sample_strs = []
                    for s in samples:
                        parts = ["%s=%s" % (key_cols[i], str(s[i])) for i in range(len(key_cols))]
                        sample_strs.append(", ".join(parts) + " (x%d)" % s[-1])

                    flags.append(QualityFlag(
                        id=str(uuid.uuid4())[:8],
                        rule_id="DUP_001",
                        table=table,
                        issue_type=IssueCategory.DUPLICATE,
                        severity=IssueSeverity.WARNING,
                        description="%d groups of duplicate rows found in '%s' on key (%s)" % (
                            dup_count, table, ", ".join(key_cols)
                        ),
                        affected_row_count=dup_count,
                        sample_values=sample_strs,
                        suggested_fix="Review duplicates. If genuine (e.g., repeated measurements), document. Otherwise, deduplicate for analysis.",
                        is_clinical_finding=False,
                    ))
            except sqlite3.OperationalError:
                pass

        conn.close()
        return flags

    # ─── Temporal Consistency Checks ────────────────────────

    def _check_temporal_issues(self) -> List[QualityFlag]:
        """Check for temporal misalignments across tables."""
        flags = []
        conn = self._connect()

        # 1. Discharge before admission
        try:
            sql = """
                SELECT COUNT(*), GROUP_CONCAT(subject_id || '/' || hadm_id, '; ')
                FROM admissions
                WHERE dischtime < admittime
            """
            row = conn.execute(sql).fetchone()
            count = row[0]
            if count > 0:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="TEMP_001",
                    table="admissions",
                    column="dischtime",
                    issue_type=IssueCategory.TEMPORAL,
                    severity=IssueSeverity.CRITICAL,
                    description="%d admissions have discharge time before admission time" % count,
                    affected_row_count=count,
                    sample_values=(row[1] or "").split("; ")[:5],
                    suggested_fix="Verify admission and discharge timestamps. Possible data entry error.",
                    is_clinical_finding=False,
                ))
        except sqlite3.OperationalError:
            pass

        # 2. ICU stay outside hospital admission window
        try:
            sql = """
                SELECT COUNT(*), GROUP_CONCAT(i.subject_id || '/' || i.stay_id, '; ')
                FROM icustays i
                JOIN admissions a ON i.hadm_id = a.hadm_id
                WHERE i.intime < a.admittime OR i.outtime > a.dischtime
            """
            row = conn.execute(sql).fetchone()
            count = row[0]
            if count > 0:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="TEMP_002",
                    table="icustays",
                    column="intime/outtime",
                    issue_type=IssueCategory.TEMPORAL,
                    severity=IssueSeverity.WARNING,
                    description="%d ICU stays fall outside their hospital admission window" % count,
                    affected_row_count=count,
                    sample_values=(row[1] or "").split("; ")[:5],
                    suggested_fix="ICU times may be recorded with slightly different clocks. Review margin of error.",
                    is_clinical_finding=False,
                ))
        except sqlite3.OperationalError:
            pass

        # 3. Lab results before admission
        try:
            sql = """
                SELECT COUNT(*)
                FROM labevents l
                JOIN admissions a ON l.hadm_id = a.hadm_id
                WHERE l.charttime < a.admittime
            """
            count = conn.execute(sql).fetchone()[0]
            if count > 0:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="TEMP_003",
                    table="labevents",
                    column="charttime",
                    issue_type=IssueCategory.TEMPORAL,
                    severity=IssueSeverity.WARNING,
                    description="%d lab results recorded before the associated admission time" % count,
                    affected_row_count=count,
                    suggested_fix="Pre-admission labs (e.g., ED) are common. Distinguish from data errors by checking if within 24h before admission.",
                    is_clinical_finding=True,  # Pre-admission labs are often legitimate
                ))
        except sqlite3.OperationalError:
            pass

        # 4. Death time inconsistency
        try:
            sql = """
                SELECT COUNT(*)
                FROM admissions
                WHERE hospital_expire_flag = 1 AND deathtime IS NULL
            """
            count = conn.execute(sql).fetchone()[0]
            if count > 0:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="TEMP_004",
                    table="admissions",
                    column="deathtime",
                    issue_type=IssueCategory.TEMPORAL,
                    severity=IssueSeverity.WARNING,
                    description="%d admissions flagged as hospital death but missing deathtime" % count,
                    affected_row_count=count,
                    suggested_fix="Verify death records. Missing deathtime with expire_flag=1 suggests incomplete documentation.",
                    is_clinical_finding=False,
                ))
        except sqlite3.OperationalError:
            pass

        # 5. Transfer times outside admission window
        try:
            sql = """
                SELECT COUNT(*)
                FROM transfers t
                JOIN admissions a ON t.hadm_id = a.hadm_id
                WHERE t.intime < a.admittime
                AND t.hadm_id IS NOT NULL
            """
            count = conn.execute(sql).fetchone()[0]
            if count > 0:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="TEMP_005",
                    table="transfers",
                    column="intime",
                    issue_type=IssueCategory.TEMPORAL,
                    severity=IssueSeverity.INFO,
                    description="%d transfers have start time before hospital admission" % count,
                    affected_row_count=count,
                    suggested_fix="Transfer records may include ED or pre-admission holds. Review context.",
                    is_clinical_finding=True,
                ))
        except sqlite3.OperationalError:
            pass

        conn.close()
        return flags

    # ─── Implausible Vital Signs ────────────────────────────

    def _check_implausible_vitals(self) -> List[QualityFlag]:
        """Check chartevents for values outside physiological plausibility."""
        flags = []
        conn = self._connect()

        try:
            # Get distinct items with numeric values
            sql = """
                SELECT DISTINCT di.itemid, di.label
                FROM d_items di
                JOIN chartevents ce ON di.itemid = ce.itemid
                WHERE ce.valuenum IS NOT NULL
            """
            items = conn.execute(sql).fetchall()

            for item in items:
                itemid = item[0]
                label = item[1]
                ranges = get_vital_range(label)
                if ranges is None:
                    continue

                # Count values outside range
                sql = """
                    SELECT COUNT(*), MIN(valuenum), MAX(valuenum)
                    FROM chartevents
                    WHERE itemid = ? AND valuenum IS NOT NULL
                    AND (valuenum < ? OR valuenum > ?)
                """
                row = conn.execute(sql, (itemid, ranges["min"], ranges["max"])).fetchone()
                outlier_count = row[0]

                if outlier_count > 0:
                    total = conn.execute(
                        "SELECT COUNT(*) FROM chartevents WHERE itemid = ? AND valuenum IS NOT NULL",
                        (itemid,)
                    ).fetchone()[0]

                    # Get sample outlier values
                    samples = conn.execute(
                        "SELECT subject_id, valuenum, charttime FROM chartevents "
                        "WHERE itemid = ? AND valuenum IS NOT NULL "
                        "AND (valuenum < ? OR valuenum > ?) LIMIT 3",
                        (itemid, ranges["min"], ranges["max"])
                    ).fetchall()
                    sample_strs = [
                        "subject_id=%s, value=%.2f, time=%s" % (s[0], s[1], s[2])
                        for s in samples
                    ]

                    # Determine if this is likely a data error or extreme clinical value
                    min_val, max_val = row[1], row[2]
                    is_extreme = (
                        (min_val is not None and min_val < 0) or
                        (max_val is not None and max_val > ranges["max"] * 2)
                    )

                    flags.append(QualityFlag(
                        id=str(uuid.uuid4())[:8],
                        rule_id="IMPLAUS_VITAL_001",
                        table="chartevents",
                        column="valuenum (itemid=%d: %s)" % (itemid, label),
                        issue_type=IssueCategory.IMPLAUSIBLE,
                        severity=IssueSeverity.CRITICAL if is_extreme else IssueSeverity.WARNING,
                        description="%d of %d '%s' values outside plausible range [%s, %s] %s" % (
                            outlier_count, total, label,
                            str(ranges["min"]), str(ranges["max"]), ranges.get("unit", "")
                        ),
                        affected_row_count=outlier_count,
                        sample_values=sample_strs,
                        suggested_fix="Negative or extreme values are likely data entry errors. Review and exclude from analysis.",
                        is_clinical_finding=not is_extreme,
                    ))
        except sqlite3.OperationalError:
            pass

        conn.close()
        return flags

    # ─── Implausible Lab Values ─────────────────────────────

    def _check_implausible_labs(self) -> List[QualityFlag]:
        """Check labevents for values outside physiological plausibility."""
        flags = []
        conn = self._connect()

        try:
            sql = """
                SELECT DISTINCT dl.itemid, dl.label
                FROM d_labitems dl
                JOIN labevents le ON dl.itemid = le.itemid
                WHERE le.valuenum IS NOT NULL
            """
            items = conn.execute(sql).fetchall()

            for item in items:
                itemid = item[0]
                label = item[1]
                ranges = get_lab_range(label)
                if ranges is None:
                    continue

                sql = """
                    SELECT COUNT(*), MIN(valuenum), MAX(valuenum)
                    FROM labevents
                    WHERE itemid = ? AND valuenum IS NOT NULL
                    AND (valuenum < ? OR valuenum > ?)
                """
                row = conn.execute(sql, (itemid, ranges["min"], ranges["max"])).fetchone()
                outlier_count = row[0]

                if outlier_count > 0:
                    total = conn.execute(
                        "SELECT COUNT(*) FROM labevents WHERE itemid = ? AND valuenum IS NOT NULL",
                        (itemid,)
                    ).fetchone()[0]

                    samples = conn.execute(
                        "SELECT subject_id, valuenum, charttime FROM labevents "
                        "WHERE itemid = ? AND valuenum IS NOT NULL "
                        "AND (valuenum < ? OR valuenum > ?) LIMIT 3",
                        (itemid, ranges["min"], ranges["max"])
                    ).fetchall()
                    sample_strs = [
                        "subject_id=%s, value=%.2f, time=%s" % (s[0], s[1], s[2])
                        for s in samples
                    ]

                    min_val = row[1]
                    is_extreme = min_val is not None and min_val < 0

                    flags.append(QualityFlag(
                        id=str(uuid.uuid4())[:8],
                        rule_id="IMPLAUS_LAB_001",
                        table="labevents",
                        column="valuenum (itemid=%d: %s)" % (itemid, label),
                        issue_type=IssueCategory.IMPLAUSIBLE,
                        severity=IssueSeverity.CRITICAL if is_extreme else IssueSeverity.WARNING,
                        description="%d of %d '%s' values outside plausible range [%s, %s] %s" % (
                            outlier_count, total, label,
                            str(ranges["min"]), str(ranges["max"]), ranges.get("unit", "")
                        ),
                        affected_row_count=outlier_count,
                        sample_values=sample_strs,
                        suggested_fix="Review lab values outside plausibility range. Negative values are errors; extreme positives may be clinically real.",
                        is_clinical_finding=not is_extreme,
                    ))
        except sqlite3.OperationalError:
            pass

        conn.close()
        return flags

    # ─── Unit Inconsistency Checks ──────────────────────────

    def _check_unit_inconsistencies(self) -> List[QualityFlag]:
        """Check for multiple units of measurement for the same item."""
        flags = []
        conn = self._connect()

        # Check labevents
        try:
            sql = """
                SELECT le.itemid, dl.label, COUNT(DISTINCT le.valueuom) as unit_count,
                       GROUP_CONCAT(DISTINCT le.valueuom) as units
                FROM labevents le
                JOIN d_labitems dl ON le.itemid = dl.itemid
                WHERE le.valueuom IS NOT NULL AND TRIM(le.valueuom) != ''
                GROUP BY le.itemid, dl.label
                HAVING COUNT(DISTINCT le.valueuom) > 1
            """
            rows = conn.execute(sql).fetchall()

            for row in rows:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="UNIT_001",
                    table="labevents",
                    column="valueuom (itemid=%d: %s)" % (row[0], row[1]),
                    issue_type=IssueCategory.UNIT_INCONSISTENCY,
                    severity=IssueSeverity.WARNING,
                    description="Lab '%s' (itemid=%d) has %d different units: %s" % (
                        row[1], row[0], row[2], row[3]
                    ),
                    affected_row_count=0,
                    sample_values=[row[3]],
                    suggested_fix="Standardize units before analysis. Convert all measurements to a single unit with documented conversion factor.",
                    is_clinical_finding=False,
                ))
        except sqlite3.OperationalError:
            pass

        # Check chartevents
        try:
            sql = """
                SELECT ce.itemid, di.label, COUNT(DISTINCT ce.valueuom) as unit_count,
                       GROUP_CONCAT(DISTINCT ce.valueuom) as units
                FROM chartevents ce
                JOIN d_items di ON ce.itemid = di.itemid
                WHERE ce.valueuom IS NOT NULL AND TRIM(ce.valueuom) != ''
                GROUP BY ce.itemid, di.label
                HAVING COUNT(DISTINCT ce.valueuom) > 1
            """
            rows = conn.execute(sql).fetchall()

            for row in rows:
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="UNIT_002",
                    table="chartevents",
                    column="valueuom (itemid=%d: %s)" % (row[0], row[1]),
                    issue_type=IssueCategory.UNIT_INCONSISTENCY,
                    severity=IssueSeverity.WARNING,
                    description="Chart item '%s' (itemid=%d) has %d different units: %s" % (
                        row[1], row[0], row[2], row[3]
                    ),
                    affected_row_count=0,
                    sample_values=[row[3]],
                    suggested_fix="Standardize units before analysis.",
                    is_clinical_finding=False,
                ))
        except sqlite3.OperationalError:
            pass

        conn.close()
        return flags

    # ─── Orphan Foreign Key Checks ──────────────────────────

    def _check_orphan_foreign_keys(self) -> List[QualityFlag]:
        """Check for foreign key references to non-existent parent rows."""
        flags = []
        conn = self._connect()

        fk_checks = [
            ("labevents", "hadm_id", "admissions", "hadm_id"),
            ("diagnoses_icd", "hadm_id", "admissions", "hadm_id"),
            ("procedures_icd", "hadm_id", "admissions", "hadm_id"),
            ("prescriptions", "hadm_id", "admissions", "hadm_id"),
            ("icustays", "hadm_id", "admissions", "hadm_id"),
            ("chartevents", "stay_id", "icustays", "stay_id"),
            ("inputevents", "stay_id", "icustays", "stay_id"),
            ("outputevents", "stay_id", "icustays", "stay_id"),
        ]

        for child_table, child_col, parent_table, parent_col in fk_checks:
            try:
                sql = """
                    SELECT COUNT(*)
                    FROM "%s" c
                    LEFT JOIN "%s" p ON c."%s" = p."%s"
                    WHERE c."%s" IS NOT NULL AND p."%s" IS NULL
                """ % (child_table, parent_table, child_col, parent_col, child_col, parent_col)

                count = conn.execute(sql).fetchone()[0]
                if count > 0:
                    flags.append(QualityFlag(
                        id=str(uuid.uuid4())[:8],
                        rule_id="FK_001",
                        table=child_table,
                        column=child_col,
                        issue_type=IssueCategory.ORPHAN_FK,
                        severity=IssueSeverity.WARNING,
                        description="%d rows in '%s.%s' reference non-existent '%s.%s'" % (
                            count, child_table, child_col, parent_table, parent_col
                        ),
                        affected_row_count=count,
                        suggested_fix="Orphaned references may indicate filtered data in the demo subset. Exclude these rows from joins.",
                        is_clinical_finding=False,
                    ))
            except sqlite3.OperationalError:
                pass

        conn.close()
        return flags

    # ─── ICD Coding Pattern Checks ──────────────────────────

    def _check_icd_coding_patterns(self) -> List[QualityFlag]:
        """Check for ICD version mixing and coding patterns."""
        flags = []
        conn = self._connect()

        # Check for patients with mixed ICD versions
        try:
            sql = """
                SELECT COUNT(DISTINCT subject_id)
                FROM (
                    SELECT subject_id, COUNT(DISTINCT icd_version) as ver_count
                    FROM diagnoses_icd
                    GROUP BY subject_id
                    HAVING COUNT(DISTINCT icd_version) > 1
                )
            """
            count = conn.execute(sql).fetchone()[0]
            if count > 0:
                # This is actually expected (patients spanning ICD-9 and ICD-10 eras)
                flags.append(QualityFlag(
                    id=str(uuid.uuid4())[:8],
                    rule_id="CODE_001",
                    table="diagnoses_icd",
                    column="icd_version",
                    issue_type=IssueCategory.CODING_PATTERN,
                    severity=IssueSeverity.INFO,
                    description="%d patients have diagnoses coded in both ICD-9 and ICD-10" % count,
                    affected_row_count=count,
                    suggested_fix="Expected for patients spanning coding transition (~2015). Map codes using crosswalk tables for consistent analysis.",
                    is_clinical_finding=True,
                ))
        except sqlite3.OperationalError:
            pass

        # Check ICD version distribution
        try:
            sql = """
                SELECT icd_version, COUNT(*) as cnt
                FROM diagnoses_icd
                GROUP BY icd_version
            """
            rows = conn.execute(sql).fetchall()
            version_info = ["%s: %d codes" % (r[0], r[1]) for r in rows]
            flags.append(QualityFlag(
                id=str(uuid.uuid4())[:8],
                rule_id="CODE_002",
                table="diagnoses_icd",
                column="icd_version",
                issue_type=IssueCategory.CODING_PATTERN,
                severity=IssueSeverity.INFO,
                description="ICD version distribution: %s" % ", ".join(version_info),
                affected_row_count=0,
                sample_values=version_info,
                suggested_fix="Be aware of ICD version when filtering diagnoses. Always specify icd_version in queries.",
                is_clinical_finding=True,
            ))
        except sqlite3.OperationalError:
            pass

        conn.close()
        return flags
