"""
Ingest MIMIC-IV Demo v2.2 CSV files into a SQLite database.
Creates mimic4demo.db with all tables, proper types, and indexes.
"""
import os
import sys
import gzip
import sqlite3
import csv
import time

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
MIMIC_DIR = os.path.join(DATA_DIR, "mimic-iv-demo")
DB_PATH = os.path.join(DATA_DIR, "mimic4demo.db")

# Columns that should be parsed as INTEGER
INT_COLUMNS = {
    "subject_id", "hadm_id", "stay_id", "itemid", "labevent_id",
    "seq_num", "drg_severity", "drg_mortality", "caregiver_id",
    "pharmacy_id", "poe_id", "link_orderid", "order_provider_id",
    "provider_id", "transfer_id", "emar_id", "micro_specimen_id",
}

# Columns that should be parsed as REAL (float)
FLOAT_COLUMNS = {
    "value", "valuenum", "ref_range_lower", "ref_range_upper",
    "amount", "originalamount", "rate", "originalrate",
    "totalamount", "patientweight", "anchor_age",
    "dilute_amount",
}

# Modules and their tables
MODULES = {
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

# Indexes to create for faster queries
INDEXES = [
    ("idx_admissions_subject", "admissions", "subject_id"),
    ("idx_admissions_hadm", "admissions", "hadm_id"),
    ("idx_transfers_subject", "transfers", "subject_id"),
    ("idx_transfers_hadm", "transfers", "hadm_id"),
    ("idx_labevents_subject", "labevents", "subject_id"),
    ("idx_labevents_hadm", "labevents", "hadm_id"),
    ("idx_labevents_itemid", "labevents", "itemid"),
    ("idx_diagnoses_subject", "diagnoses_icd", "subject_id"),
    ("idx_diagnoses_hadm", "diagnoses_icd", "hadm_id"),
    ("idx_diagnoses_icd_code", "diagnoses_icd", "icd_code"),
    ("idx_procedures_subject", "procedures_icd", "subject_id"),
    ("idx_procedures_hadm", "procedures_icd", "hadm_id"),
    ("idx_prescriptions_subject", "prescriptions", "subject_id"),
    ("idx_prescriptions_hadm", "prescriptions", "hadm_id"),
    ("idx_emar_subject", "emar", "subject_id"),
    ("idx_emar_hadm", "emar", "hadm_id"),
    ("idx_pharmacy_subject", "pharmacy", "subject_id"),
    ("idx_pharmacy_hadm", "pharmacy", "hadm_id"),
    ("idx_micro_subject", "microbiologyevents", "subject_id"),
    ("idx_micro_hadm", "microbiologyevents", "hadm_id"),
    ("idx_poe_subject", "poe", "subject_id"),
    ("idx_poe_hadm", "poe", "hadm_id"),
    ("idx_icustays_subject", "icustays", "subject_id"),
    ("idx_icustays_hadm", "icustays", "hadm_id"),
    ("idx_icustays_stay", "icustays", "stay_id"),
    ("idx_chartevents_subject", "chartevents", "subject_id"),
    ("idx_chartevents_hadm", "chartevents", "hadm_id"),
    ("idx_chartevents_stay", "chartevents", "stay_id"),
    ("idx_chartevents_itemid", "chartevents", "itemid"),
    ("idx_inputevents_subject", "inputevents", "subject_id"),
    ("idx_inputevents_hadm", "inputevents", "hadm_id"),
    ("idx_inputevents_stay", "inputevents", "stay_id"),
    ("idx_outputevents_subject", "outputevents", "subject_id"),
    ("idx_outputevents_hadm", "outputevents", "hadm_id"),
    ("idx_outputevents_stay", "outputevents", "stay_id"),
    ("idx_procedureevents_subject", "procedureevents", "subject_id"),
    ("idx_procedureevents_hadm", "procedureevents", "hadm_id"),
    ("idx_procedureevents_stay", "procedureevents", "stay_id"),
    ("idx_datetimeevents_subject", "datetimeevents", "subject_id"),
    ("idx_datetimeevents_stay", "datetimeevents", "stay_id"),
    ("idx_ingredientevents_subject", "ingredientevents", "subject_id"),
    ("idx_ingredientevents_stay", "ingredientevents", "stay_id"),
    ("idx_services_subject", "services", "subject_id"),
    ("idx_services_hadm", "services", "hadm_id"),
    ("idx_drgcodes_subject", "drgcodes", "subject_id"),
    ("idx_drgcodes_hadm", "drgcodes", "hadm_id"),
    ("idx_hcpcsevents_subject", "hcpcsevents", "subject_id"),
    ("idx_hcpcsevents_hadm", "hcpcsevents", "hadm_id"),
    ("idx_omr_subject", "omr", "subject_id"),
    ("idx_patients_subject", "patients", "subject_id"),
]


def get_csv_path(module, table):
    """Find the CSV file path, handling both .csv and .csv.gz."""
    csv_path = os.path.join(MIMIC_DIR, module, "%s.csv" % table)
    gz_path = os.path.join(MIMIC_DIR, module, "%s.csv.gz" % table)
    if os.path.exists(csv_path):
        return csv_path, False
    elif os.path.exists(gz_path):
        return gz_path, True
    return None, False


def infer_column_type(col_name):
    """Infer SQLite column type from column name."""
    col_lower = col_name.lower()
    if col_lower in INT_COLUMNS:
        return "INTEGER"
    if col_lower in FLOAT_COLUMNS:
        return "REAL"
    return "TEXT"


def read_csv_file(filepath, is_gzipped):
    """Read CSV file, handling gzipped files."""
    if is_gzipped:
        f = gzip.open(filepath, 'rt', encoding='utf-8', errors='replace')
    else:
        f = open(filepath, 'r', encoding='utf-8', errors='replace')
    reader = csv.reader(f)
    return f, reader


def ingest_table(conn, module, table):
    """Ingest a single CSV table into SQLite."""
    filepath, is_gzipped = get_csv_path(module, table)
    if filepath is None:
        print("    [SKIP] %s/%s - file not found" % (module, table))
        return 0

    file_handle, reader = read_csv_file(filepath, is_gzipped)

    try:
        # Read header
        headers = next(reader)
        headers = [h.strip().lower() for h in headers]

        # Determine column types
        col_defs = []
        for h in headers:
            col_type = infer_column_type(h)
            col_defs.append('"%s" %s' % (h, col_type))

        # Create table
        create_sql = 'CREATE TABLE IF NOT EXISTS "%s" (%s)' % (table, ", ".join(col_defs))
        conn.execute(create_sql)

        # Insert rows
        placeholders = ", ".join(["?"] * len(headers))
        insert_sql = 'INSERT INTO "%s" VALUES (%s)' % (table, placeholders)

        row_count = 0
        batch = []
        for row in reader:
            # Convert empty strings to None, and cast types
            processed = []
            for i, val in enumerate(row):
                if val == '' or val is None:
                    processed.append(None)
                else:
                    col_type = infer_column_type(headers[i])
                    if col_type == "INTEGER":
                        try:
                            processed.append(int(float(val)))
                        except (ValueError, OverflowError):
                            processed.append(val)
                    elif col_type == "REAL":
                        try:
                            processed.append(float(val))
                        except ValueError:
                            processed.append(val)
                    else:
                        processed.append(val)
            batch.append(processed)
            row_count += 1

            if len(batch) >= 5000:
                conn.executemany(insert_sql, batch)
                batch = []

        if batch:
            conn.executemany(insert_sql, batch)

        conn.commit()
        print("    [OK] %s/%s: %d rows, %d columns" % (module, table, row_count, len(headers)))
        return row_count

    finally:
        file_handle.close()


def create_indexes(conn):
    """Create indexes for faster queries."""
    print("\n[..] Creating indexes...")
    created = 0
    for idx_name, table, column in INDEXES:
        try:
            # Check if table and column exist
            cursor = conn.execute('PRAGMA table_info("%s")' % table)
            columns = [row[1] for row in cursor.fetchall()]
            if column in columns:
                conn.execute('CREATE INDEX IF NOT EXISTS "%s" ON "%s"("%s")' % (idx_name, table, column))
                created += 1
        except sqlite3.OperationalError:
            pass  # Table doesn't exist, skip
    conn.commit()
    print("    [OK] Created %d indexes" % created)


def print_summary(conn):
    """Print a summary of all tables in the database."""
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    total_rows = 0
    for table in tables:
        count = conn.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
        total_rows += count
        print("  %-30s %8d rows" % (table, count))

    print("-" * 60)
    print("  %-30s %8d rows" % ("TOTAL", total_rows))
    print("  %-30s %8d tables" % ("", len(tables)))

    # Patient count
    try:
        patient_count = conn.execute("SELECT COUNT(DISTINCT subject_id) FROM patients").fetchone()[0]
        print("  %-30s %8d patients" % ("", patient_count))
    except sqlite3.OperationalError:
        pass

    db_size = os.path.getsize(DB_PATH)
    print("  %-30s %8.1f MB" % ("Database size:", db_size / (1024 * 1024)))


def main():
    print("=" * 60)
    print("MIMIC-IV Demo v2.2 - SQLite Ingestion")
    print("=" * 60)
    print()

    # Check that data exists
    if not os.path.isdir(MIMIC_DIR):
        print("[FAIL] MIMIC data directory not found at: %s" % MIMIC_DIR)
        print("       Run download_mimic.py first.")
        sys.exit(1)

    # Remove existing database
    if os.path.exists(DB_PATH):
        print("[..] Removing existing database...")
        os.remove(DB_PATH)

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    start_time = time.time()
    total_tables = 0
    total_rows = 0

    for module, tables in MODULES.items():
        print("\n[>>] Ingesting module: %s" % module)
        for table in tables:
            rows = ingest_table(conn, module, table)
            total_rows += rows
            total_tables += 1

    create_indexes(conn)
    print_summary(conn)

    elapsed = time.time() - start_time
    print("\n[OK] Ingestion complete in %.1f seconds" % elapsed)
    print("     Database: %s" % DB_PATH)

    conn.close()


if __name__ == "__main__":
    main()
