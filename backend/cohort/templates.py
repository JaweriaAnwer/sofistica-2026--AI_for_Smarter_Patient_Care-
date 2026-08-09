"""
Pre-built cohort query templates for common clinical research scenarios.

These serve as:
1. Quick-start templates for users
2. Few-shot examples for the LLM prompt
3. Baseline comparison for evaluation
"""

TEMPLATES = [
    {
        "id": "t1",
        "name": "Elderly ICU patients",
        "description": "Adults over 65 years old with at least one ICU stay",
        "natural_language": "Adults over 65 with at least one ICU stay",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age
FROM patients p
JOIN icustays i ON p.subject_id = i.subject_id
WHERE p.anchor_age > 65
ORDER BY p.subject_id""",
        "tables_used": ["patients", "icustays"],
        "inclusion_criteria": [
            {"description": "Age over 65 years", "table": "patients", "condition": "anchor_age > 65"},
            {"description": "At least one ICU stay", "table": "icustays", "condition": "EXISTS in icustays"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t2",
        "name": "Sepsis patients",
        "description": "Patients with a sepsis diagnosis (ICD-9: 995.91, 995.92; ICD-10: R65.20, R65.21)",
        "natural_language": "Patients diagnosed with sepsis",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age, d.icd_code, dd.long_title
FROM patients p
JOIN admissions a ON p.subject_id = a.subject_id
JOIN diagnoses_icd d ON a.hadm_id = d.hadm_id
JOIN d_icd_diagnoses dd ON d.icd_code = dd.icd_code AND d.icd_version = dd.icd_version
WHERE (d.icd_code IN ('99591', '99592') AND d.icd_version = 9)
   OR (d.icd_code IN ('R6520', 'R6521') AND d.icd_version = 10)
ORDER BY p.subject_id""",
        "tables_used": ["patients", "admissions", "diagnoses_icd", "d_icd_diagnoses"],
        "inclusion_criteria": [
            {"description": "Sepsis diagnosis (ICD-9: 995.91/995.92 or ICD-10: R65.20/R65.21)",
             "table": "diagnoses_icd",
             "condition": "icd_code IN ('99591','99592','R6520','R6521')"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t3",
        "name": "Long hospital stay",
        "description": "Patients with hospital length of stay greater than 7 days",
        "natural_language": "Patients who stayed in the hospital for more than 7 days",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age,
       a.hadm_id, a.admittime, a.dischtime,
       ROUND(JULIANDAY(a.dischtime) - JULIANDAY(a.admittime), 1) as los_days
FROM patients p
JOIN admissions a ON p.subject_id = a.subject_id
WHERE JULIANDAY(a.dischtime) - JULIANDAY(a.admittime) > 7
ORDER BY los_days DESC""",
        "tables_used": ["patients", "admissions"],
        "inclusion_criteria": [
            {"description": "Hospital LOS > 7 days", "table": "admissions",
             "condition": "JULIANDAY(dischtime) - JULIANDAY(admittime) > 7"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t4",
        "name": "Patients on vasopressors",
        "description": "ICU patients who received vasopressor medications (norepinephrine, vasopressin, epinephrine, dopamine, phenylephrine)",
        "natural_language": "Patients who received vasopressors in the ICU",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age, di.label as vasopressor
FROM patients p
JOIN icustays icu ON p.subject_id = icu.subject_id
JOIN inputevents ie ON icu.stay_id = ie.stay_id
JOIN d_items di ON ie.itemid = di.itemid
WHERE LOWER(di.label) LIKE '%norepinephrine%'
   OR LOWER(di.label) LIKE '%vasopressin%'
   OR LOWER(di.label) LIKE '%epinephrine%'
   OR LOWER(di.label) LIKE '%dopamine%'
   OR LOWER(di.label) LIKE '%phenylephrine%'
ORDER BY p.subject_id""",
        "tables_used": ["patients", "icustays", "inputevents", "d_items"],
        "inclusion_criteria": [
            {"description": "Received vasopressor medication in ICU",
             "table": "inputevents",
             "condition": "d_items.label LIKE vasopressor names"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t5",
        "name": "Female patients with cardiac diagnoses",
        "description": "Female patients with any cardiac-related ICD diagnosis",
        "natural_language": "Female patients with cardiac diagnoses",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age, dd.long_title
FROM patients p
JOIN admissions a ON p.subject_id = a.subject_id
JOIN diagnoses_icd d ON a.hadm_id = d.hadm_id
JOIN d_icd_diagnoses dd ON d.icd_code = dd.icd_code AND d.icd_version = dd.icd_version
WHERE p.gender = 'F'
  AND (LOWER(dd.long_title) LIKE '%heart%'
    OR LOWER(dd.long_title) LIKE '%cardiac%'
    OR LOWER(dd.long_title) LIKE '%myocardial%'
    OR LOWER(dd.long_title) LIKE '%atrial%'
    OR LOWER(dd.long_title) LIKE '%ventricular%')
ORDER BY p.subject_id""",
        "tables_used": ["patients", "admissions", "diagnoses_icd", "d_icd_diagnoses"],
        "inclusion_criteria": [
            {"description": "Female gender", "table": "patients", "condition": "gender = 'F'"},
            {"description": "Cardiac-related diagnosis", "table": "d_icd_diagnoses",
             "condition": "long_title contains cardiac terms"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t6",
        "name": "Patients with abnormal labs",
        "description": "Patients with at least one flagged abnormal lab result",
        "natural_language": "Patients who have abnormal lab results",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age,
       COUNT(DISTINCT l.labevent_id) as abnormal_count
FROM patients p
JOIN labevents l ON p.subject_id = l.subject_id
WHERE l.flag IS NOT NULL AND TRIM(l.flag) != ''
GROUP BY p.subject_id, p.gender, p.anchor_age
HAVING COUNT(DISTINCT l.labevent_id) > 0
ORDER BY abnormal_count DESC""",
        "tables_used": ["patients", "labevents"],
        "inclusion_criteria": [
            {"description": "At least one abnormal lab flag", "table": "labevents",
             "condition": "flag IS NOT NULL"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t7",
        "name": "Emergency admissions",
        "description": "Patients admitted through the emergency department",
        "natural_language": "Patients who were admitted as emergency cases",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age,
       a.admission_type, a.admission_location
FROM patients p
JOIN admissions a ON p.subject_id = a.subject_id
WHERE a.admission_type LIKE '%EMERGENCY%'
   OR a.admission_type LIKE '%URGENT%'
ORDER BY p.subject_id""",
        "tables_used": ["patients", "admissions"],
        "inclusion_criteria": [
            {"description": "Emergency or urgent admission type", "table": "admissions",
             "condition": "admission_type LIKE '%EMERGENCY%' OR '%URGENT%'"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t8",
        "name": "Patients with multiple admissions",
        "description": "Patients who were admitted to the hospital more than once",
        "natural_language": "Patients with multiple hospital admissions",
        "sql": """SELECT p.subject_id, p.gender, p.anchor_age,
       COUNT(DISTINCT a.hadm_id) as admission_count
FROM patients p
JOIN admissions a ON p.subject_id = a.subject_id
GROUP BY p.subject_id, p.gender, p.anchor_age
HAVING COUNT(DISTINCT a.hadm_id) > 1
ORDER BY admission_count DESC""",
        "tables_used": ["patients", "admissions"],
        "inclusion_criteria": [
            {"description": "More than one hospital admission", "table": "admissions",
             "condition": "COUNT(DISTINCT hadm_id) > 1"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t9",
        "name": "In-hospital mortality",
        "description": "Patients who died during their hospital stay",
        "natural_language": "Patients who died in the hospital",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age,
       a.hadm_id, a.admittime, a.dischtime, a.deathtime,
       ROUND(JULIANDAY(a.dischtime) - JULIANDAY(a.admittime), 1) as los_days
FROM patients p
JOIN admissions a ON p.subject_id = a.subject_id
WHERE a.hospital_expire_flag = 1
ORDER BY p.subject_id""",
        "tables_used": ["patients", "admissions"],
        "inclusion_criteria": [
            {"description": "Died during hospital stay", "table": "admissions",
             "condition": "hospital_expire_flag = 1"}
        ],
        "exclusion_criteria": []
    },
    {
        "id": "t10",
        "name": "Patients with microbiology cultures",
        "description": "Patients who had microbiology culture tests ordered",
        "natural_language": "Patients with microbiology culture results",
        "sql": """SELECT DISTINCT p.subject_id, p.gender, p.anchor_age,
       COUNT(DISTINCT m.micro_specimen_id) as culture_count
FROM patients p
JOIN microbiologyevents m ON p.subject_id = m.subject_id
GROUP BY p.subject_id, p.gender, p.anchor_age
ORDER BY culture_count DESC""",
        "tables_used": ["patients", "microbiologyevents"],
        "inclusion_criteria": [
            {"description": "Has microbiology culture data", "table": "microbiologyevents",
             "condition": "EXISTS in microbiologyevents"}
        ],
        "exclusion_criteria": []
    },
]
