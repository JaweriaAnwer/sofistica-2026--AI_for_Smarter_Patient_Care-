"""
Clinical plausibility ranges for vital signs and common laboratory tests.

These ranges define the physiologically possible (not normal) boundaries.
Values outside these ranges are almost certainly data errors.
Values inside may still be clinically extreme but are physiologically possible.

Sources:
- Merck Manual reference ranges
- Clinical laboratory reference intervals
- ICU monitoring device specifications

Note: These are PLAUSIBILITY ranges, not NORMAL ranges.
A glucose of 800 mg/dL is extreme but possible (DKA).
A heart rate of -5 is a data error.
"""

# Vital signs plausibility ranges (ICU chartevents via d_items)
# Key: label pattern (lowercase), Value: {min, max, unit, source}
VITAL_SIGN_RANGES = {
    "heart rate": {
        "min": 0, "max": 350, "unit": "bpm",
        "source": "Physiological limits of cardiac monitoring"
    },
    "respiratory rate": {
        "min": 0, "max": 80, "unit": "insp/min",
        "source": "Clinical respiratory monitoring"
    },
    "o2 saturation": {
        "min": 0, "max": 100, "unit": "%",
        "source": "Pulse oximetry limits"
    },
    "spo2": {
        "min": 0, "max": 100, "unit": "%",
        "source": "Pulse oximetry limits"
    },
    "temperature": {
        "min": 25.0, "max": 45.0, "unit": "C",
        "source": "Survivable core body temperature range"
    },
    "temperature fahrenheit": {
        "min": 77.0, "max": 113.0, "unit": "F",
        "source": "Survivable core body temperature range (Fahrenheit)"
    },
    "systolic blood pressure": {
        "min": 0, "max": 350, "unit": "mmHg",
        "source": "Blood pressure monitoring limits"
    },
    "diastolic blood pressure": {
        "min": 0, "max": 250, "unit": "mmHg",
        "source": "Blood pressure monitoring limits"
    },
    "mean blood pressure": {
        "min": 0, "max": 300, "unit": "mmHg",
        "source": "Derived from systolic/diastolic"
    },
    "arterial blood pressure systolic": {
        "min": 0, "max": 350, "unit": "mmHg",
        "source": "Arterial line monitoring"
    },
    "arterial blood pressure diastolic": {
        "min": 0, "max": 250, "unit": "mmHg",
        "source": "Arterial line monitoring"
    },
    "arterial blood pressure mean": {
        "min": 0, "max": 300, "unit": "mmHg",
        "source": "Arterial line monitoring"
    },
    "non invasive blood pressure systolic": {
        "min": 0, "max": 350, "unit": "mmHg",
        "source": "NIBP monitoring"
    },
    "non invasive blood pressure diastolic": {
        "min": 0, "max": 250, "unit": "mmHg",
        "source": "NIBP monitoring"
    },
    "non invasive blood pressure mean": {
        "min": 0, "max": 300, "unit": "mmHg",
        "source": "NIBP monitoring"
    },
    "weight": {
        "min": 0.5, "max": 500, "unit": "kg",
        "source": "Human weight plausibility"
    },
    "height": {
        "min": 30, "max": 250, "unit": "cm",
        "source": "Human height plausibility"
    },
    "gcs total": {
        "min": 3, "max": 15, "unit": "score",
        "source": "Glasgow Coma Scale definition"
    },
}

# Lab test plausibility ranges (labevents via d_labitems)
# Key: label pattern (lowercase), Value: {min, max, unit, source}
LAB_RANGES = {
    "glucose": {
        "min": 1, "max": 2000, "unit": "mg/dL",
        "source": "Clinical glucose limits (DKA can reach >1000)"
    },
    "creatinine": {
        "min": 0.01, "max": 50, "unit": "mg/dL",
        "source": "Renal failure can reach 20+"
    },
    "potassium": {
        "min": 1.0, "max": 12.0, "unit": "mEq/L",
        "source": "Severe hypo/hyperkalemia limits"
    },
    "sodium": {
        "min": 100, "max": 200, "unit": "mEq/L",
        "source": "Severe hypo/hypernatremia limits"
    },
    "hemoglobin": {
        "min": 1.0, "max": 25.0, "unit": "g/dL",
        "source": "Severe anemia to polycythemia"
    },
    "hematocrit": {
        "min": 5.0, "max": 75.0, "unit": "%",
        "source": "Extreme anemia to polycythemia"
    },
    "white blood cells": {
        "min": 0, "max": 500, "unit": "K/uL",
        "source": "Leukemia can produce very high WBC"
    },
    "wbc": {
        "min": 0, "max": 500, "unit": "K/uL",
        "source": "Leukemia can produce very high WBC"
    },
    "platelet count": {
        "min": 0, "max": 2000, "unit": "K/uL",
        "source": "Thrombocytopenia to thrombocytosis"
    },
    "platelets": {
        "min": 0, "max": 2000, "unit": "K/uL",
        "source": "Thrombocytopenia to thrombocytosis"
    },
    "bilirubin": {
        "min": 0, "max": 100, "unit": "mg/dL",
        "source": "Severe liver failure"
    },
    "alanine aminotransferase": {
        "min": 0, "max": 30000, "unit": "IU/L",
        "source": "Acute liver failure can reach very high levels"
    },
    "alt": {
        "min": 0, "max": 30000, "unit": "IU/L",
        "source": "Acute liver failure"
    },
    "aspartate aminotransferase": {
        "min": 0, "max": 30000, "unit": "IU/L",
        "source": "Acute liver/cardiac damage"
    },
    "ast": {
        "min": 0, "max": 30000, "unit": "IU/L",
        "source": "Acute liver/cardiac damage"
    },
    "ph": {
        "min": 6.5, "max": 8.0, "unit": "",
        "source": "Arterial blood gas pH limits"
    },
    "pco2": {
        "min": 5, "max": 200, "unit": "mmHg",
        "source": "Blood gas CO2 limits"
    },
    "po2": {
        "min": 5, "max": 700, "unit": "mmHg",
        "source": "Blood gas O2 limits (high FiO2 can push >500)"
    },
    "lactate": {
        "min": 0, "max": 50, "unit": "mmol/L",
        "source": "Severe lactic acidosis"
    },
    "troponin": {
        "min": 0, "max": 500, "unit": "ng/mL",
        "source": "Acute MI can produce very high troponin"
    },
    "inr": {
        "min": 0.1, "max": 30, "unit": "",
        "source": "Anticoagulation and liver failure"
    },
    "blood urea nitrogen": {
        "min": 0, "max": 300, "unit": "mg/dL",
        "source": "Renal failure"
    },
    "bun": {
        "min": 0, "max": 300, "unit": "mg/dL",
        "source": "Renal failure"
    },
    "calcium": {
        "min": 1, "max": 25, "unit": "mg/dL",
        "source": "Hypo/hypercalcemia"
    },
    "magnesium": {
        "min": 0.5, "max": 15, "unit": "mg/dL",
        "source": "Severe hypo/hypermagnesemia"
    },
    "chloride": {
        "min": 60, "max": 160, "unit": "mEq/L",
        "source": "Electrolyte disorders"
    },
    "bicarbonate": {
        "min": 1, "max": 60, "unit": "mEq/L",
        "source": "Severe acidosis/alkalosis"
    },
    "albumin": {
        "min": 0.5, "max": 7, "unit": "g/dL",
        "source": "Malnutrition to dehydration"
    },
}


def get_vital_range(label):
    """Look up plausibility range for a vital sign by label (case-insensitive partial match)."""
    label_lower = label.lower().strip()
    for pattern, ranges in VITAL_SIGN_RANGES.items():
        if pattern in label_lower or label_lower in pattern:
            return ranges
    return None


def get_lab_range(label):
    """Look up plausibility range for a lab test by label (case-insensitive partial match)."""
    label_lower = label.lower().strip()
    for pattern, ranges in LAB_RANGES.items():
        if pattern in label_lower or label_lower in pattern:
            return ranges
    return None
