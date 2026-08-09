"""
Download and extract MIMIC-IV Clinical Database Demo v2.2
Source: https://physionet.org/content/mimic-iv-demo/2.2/
License: Open Data Commons Open Database License v1.0
"""
import os
import sys
import zipfile
import urllib.request

DATASET_URL = "https://physionet.org/content/mimic-iv-demo/get-zip/2.2/"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(DATA_DIR, "mimic-iv-demo-2.2.zip")
EXTRACT_DIR = os.path.join(DATA_DIR, "mimic-iv-demo")

EXPECTED_TABLES = {
    "hosp": [
        "admissions", "d_hcpcs", "d_icd_diagnoses", "d_icd_procedures",
        "d_labitems", "diagnoses_icd", "drgcodes", "emar", "emar_detail",
        "hcpcsevents", "labevents", "microbiologyevents", "omr",
        "patients", "pharmacy", "poe", "poe_detail", "prescriptions",
        "procedures_icd", "provider", "services", "transfers"
    ],
    "icu": [
        "caregiver", "chartevents", "d_items", "datetimeevents",
        "icustays", "ingredientevents", "inputevents", "outputevents",
        "procedureevents"
    ]
}


def download_dataset():
    """Download the MIMIC-IV Demo ZIP from PhysioNet."""
    if os.path.exists(ZIP_PATH):
        print("[OK] ZIP already exists at %s" % ZIP_PATH)
        return

    print("[>>] Downloading MIMIC-IV Demo v2.2 from PhysioNet...")
    print("    URL: %s" % DATASET_URL)
    print("    This may take a minute (~15 MB)...")

    try:
        urllib.request.urlretrieve(DATASET_URL, ZIP_PATH, _progress_hook)
        print("\n[OK] Downloaded to %s" % ZIP_PATH)
    except Exception as e:
        print("\n[FAIL] Download failed: %s" % str(e))
        print("    Please download manually from:")
        print("    %s" % DATASET_URL)
        sys.exit(1)


def _progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 // total_size)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write("\r    Progress: %d%% (%.1f/%.1f MB)" % (percent, mb_down, mb_total))
        sys.stdout.flush()


def extract_dataset():
    """Extract the ZIP file."""
    if os.path.exists(EXTRACT_DIR):
        print("[OK] Dataset already extracted at %s" % EXTRACT_DIR)
        return

    print("[>>] Extracting to %s..." % EXTRACT_DIR)
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        zf.extractall(DATA_DIR)

    # The ZIP extracts to a folder like 'mimic-iv-clinical-database-demo-2.2'
    # Rename to our expected 'mimic-iv-demo' for consistency
    extracted_folders = [
        d for d in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, d)) and "mimic" in d.lower() and d != "mimic-iv-demo"
    ]
    if extracted_folders:
        src = os.path.join(DATA_DIR, extracted_folders[0])
        os.rename(src, EXTRACT_DIR)
        print("    Renamed %s -> mimic-iv-demo" % extracted_folders[0])

    print("[OK] Extracted successfully")


def verify_dataset():
    """Verify that all expected CSV files are present."""
    print("\n[..] Verifying dataset structure...")
    missing = []
    found = []

    for module, tables in EXPECTED_TABLES.items():
        module_dir = os.path.join(EXTRACT_DIR, module)
        if not os.path.isdir(module_dir):
            print("    [FAIL] Missing module directory: %s/" % module)
            missing.extend(["%s/%s" % (module, t) for t in tables])
            continue

        for table in tables:
            # Check for both .csv and .csv.gz
            csv_path = os.path.join(module_dir, "%s.csv" % table)
            gz_path = os.path.join(module_dir, "%s.csv.gz" % table)
            if os.path.exists(csv_path):
                size = os.path.getsize(csv_path)
                found.append(("%s/%s.csv" % (module, table), size))
            elif os.path.exists(gz_path):
                size = os.path.getsize(gz_path)
                found.append(("%s/%s.csv.gz" % (module, table), size))
            else:
                missing.append("%s/%s" % (module, table))

    print("\n    Found %d tables:" % len(found))
    for name, size in sorted(found):
        if size < 1024 * 1024:
            size_str = "%.1f KB" % (size / 1024)
        else:
            size_str = "%.1f MB" % (size / (1024 * 1024))
        print("      %s (%s)" % (name, size_str))

    if missing:
        print("\n    [!] Missing %d tables:" % len(missing))
        for name in missing:
            print("      %s" % name)
    else:
        print("\n    [OK] All %d expected tables present" % len(found))

    return len(missing) == 0


if __name__ == "__main__":
    print("=" * 60)
    print("MIMIC-IV Clinical Database Demo v2.2 - Downloader")
    print("=" * 60)
    print()

    download_dataset()
    extract_dataset()
    success = verify_dataset()

    print()
    if success:
        print("[OK] Dataset ready. Run ingest_to_sqlite.py next.")
    else:
        print("[!] Some files are missing. Check the extraction.")

    sys.exit(0 if success else 1)
