# Safety & Responsible Use Statement

> **ClinIQ — Cohort & Data Quality Explorer**  
> Sofstica Hackathon 2026 · Track 2: Smarter Patient Care

---

## Intended Use

ClinIQ is a **research and educational prototype** designed exclusively for:

- Clinical-data researchers exploring structured hospital data
- Educators teaching data science with real-world clinical datasets
- Healthcare data teams assessing data quality before downstream analysis

The tool helps users define patient cohorts, inspect data quality, and understand measurement coverage across the MIMIC-IV Clinical Database Demo v2.2.

---

## Prohibited Use

> **ClinIQ is NOT a clinical decision-support system.**

This tool must **never** be used for:

| Prohibited Activity | Reason |
|---------------------|--------|
| **Diagnosis** of any patient or condition | The tool queries de-identified demo data; it has no diagnostic capability |
| **Treatment decisions** or drug prescriptions | The AI model translates questions to SQL — it does not have medical reasoning |
| **Triage or emergency decisions** | Response latency, data limitations, and lack of real-time data make this unsafe |
| **Patient identification** | MIMIC-IV data is de-identified; attempting re-identification violates the data use agreement |
| **Population-level clinical conclusions** | The 100-patient demo subset is not representative of any real population |
| **Automated clinical workflows** | No API output should feed directly into patient care systems without human review |

The system enforces this through:
- A **persistent, non-dismissible safety banner** on every page
- **Keyword-based abstention**: queries containing clinical action words ("prescribe", "treat", "diagnose patient", "best treatment", "triage") are automatically blocked before reaching the LLM
- Every AI-generated output is marked with a visible **"AI Generated" badge**

---

## Data Lineage & Privacy

### Source Data

| Property | Value |
|----------|-------|
| Dataset | MIMIC-IV Clinical Database Demo v2.2 |
| Source | PhysioNet (https://physionet.org/content/mimic-iv-demo/2.2/) |
| DOI | 10.13026/dp1f-ex47 |
| Patients | 100 (de-identified) |
| Institution | Beth Israel Deaconess Medical Center |
| De-identification | All dates shifted; no free-text clinical notes; no direct identifiers |

### Data Flow

```
PhysioNet CSV files (public, de-identified)
    ↓ download_mimic.py
Local CSV files (data/mimic-iv-demo/)
    ↓ ingest_to_sqlite.py
Local SQLite database (data/mimic4demo.db)
    ↓ FastAPI backend (read-only mode)
API responses → React frontend (browser only)
```

### What Is Sent to the LLM

| Sent to OpenAI | NOT Sent to OpenAI |
|-----------------|---------------------|
| Table names and descriptions | Patient identifiers (subject_id) |
| Column names and data types | Any cell values, lab results, or vitals |
| Foreign key relationships | Dates, timestamps, or demographic values |
| Clinical notes about schema meaning | Query results or row data |
| The user's natural-language question | The SQLite database itself |

**The LLM receives only the database schema structure and the user's question.** All data processing, filtering, joining, and aggregation happens locally in Python/SQLite. The LLM's sole job is to translate natural language into SQL syntax.

---

## Failure Modes & Limitations

### Known Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| **LLM generates incorrect SQL** | Wrong patient count or criteria | SQL is visible and editable; user can review and re-run. Validator blocks dangerous SQL. |
| **LLM hallucinates table/column names** | Query fails with SQL error | Validator checks against known schema. Error message shown to user. |
| **DQ engine false positives** | A valid clinical value flagged as implausible | Engine uses wide physiological plausibility ranges (not normal ranges) and marks borderline cases as "Possible Clinical Finding" instead of "Data Quality Error" |
| **DQ engine false negatives** | A real data error not detected | Rules cover 8 categories but cannot catch every possible error type. Rule coverage is documented. |
| **Template fallback produces poor matches** | When LLM API is down, keyword matching is imprecise | Fallback clearly states it is template-based; user can edit the SQL |
| **Date-shifting artifacts** | Some temporal checks may flag shifted dates as anomalies | Noted in DQ flag descriptions; users are warned about date shifting |
| **Small sample size** | 100 patients is not statistically representative | Stated prominently in the UI and documentation |

### What the System Cannot Do

- **Cannot access clinical notes** — MIMIC-IV Demo does not include free-text notes
- **Cannot link to imaging or waveform data** — only structured tabular data
- **Cannot perform causal inference** — cohort queries are observational, not experimental
- **Cannot guarantee LLM consistency** — even at temperature 0.1, responses may vary slightly across runs

---

## Human Review Boundary

Every output of this system requires human review before use:

1. **AI-generated SQL**: Always displayed, always editable. The user must review the query logic before trusting the results.
2. **Data quality flags**: Each flag includes a suggested fix, but no fix is applied automatically. The "Mark as Reviewed" toggle is local-only — it does not modify the source data.
3. **Demographic summaries**: Computed by deterministic Python code (not the LLM), but the user should verify that the SQL criteria match their research intent before interpreting demographics.
4. **Provenance tooltips**: Every value in the results table shows its source table, column, and patient ID on hover — enabling manual verification against the raw data.

---

## Transparency Measures

| Measure | Implementation |
|---------|----------------|
| Persistent safety banner | Non-dismissible, present on every page |
| AI-Generated badge | Sparkle icon + label on all LLM outputs |
| Visible SQL | Generated SQL is shown and editable, never hidden |
| Inclusion/exclusion criteria cards | Structured breakdown of query logic |
| Provenance tooltips | Source table + column on every data cell |
| Clinical finding distinction | Orange border = data error, Blue border = possible clinical finding |
| Abstention | System refuses to answer clinical treatment questions |
| Export capability | All quality flags exportable as JSON/CSV for external review |

---

## Regulatory & Ethical Considerations

- This is a **hackathon prototype** and is not subject to FDA regulation, HIPAA, or any clinical certification framework.
- The MIMIC-IV data is publicly available under the Open Database License v1.0 (ODbL) and has been approved for research use by the Beth Israel Deaconess Medical Center IRB.
- No additional patient consent is required for this de-identified demo dataset.
- The system does not store user queries or results beyond the browser session.

---

## Contact

For questions about this prototype, contact the team through the Sofstica Hackathon 2026 submission portal.
