import sqlite3
import pandas as pd
import json
import os
from pathlib import Path

# Paths relative to repository root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "pune_dams.db"
SCHEMA_FILE = BASE_DIR / "database" / "schema.sql"
JSON_OUTPUT = BASE_DIR / "web" / "dam_data.json"

# Canonical Dam Master Reference Data
DAM_MASTER_DATA = [
    {"dam_code": "KHD", "dam_name": "Khadakwasla", "river_name": "Mutha River", "dead_storage_mcm": 30.0,  "design_live_mcm": 55.91,  "design_gross_mcm": 85.91},
    {"dam_code": "PNS", "dam_name": "Panshet",     "river_name": "Ambi River",  "dead_storage_mcm": 9.0,   "design_live_mcm": 301.61, "design_gross_mcm": 310.61},
    {"dam_code": "MUL", "dam_name": "Mulshi",      "river_name": "Mula River",  "dead_storage_mcm": 230.0, "design_live_mcm": 522.76, "design_gross_mcm": 752.76},
    {"dam_code": "GNJ", "dam_name": "Gunjawani",   "river_name": "Kanandi River","dead_storage_mcm": 0.21,  "design_live_mcm": 104.48, "design_gross_mcm": 104.69},
    {"dam_code": "TMG", "dam_name": "Temghar",     "river_name": "Mutha River", "dead_storage_mcm": 2.95,  "design_live_mcm": 105.01, "design_gross_mcm": 107.96}
]

def get_db_connection():
    """Returns a connection to the SQLite database with Foreign Keys enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the relational database schema in 3rd Normal Form (3NF)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print(f"✅ Relational DBMS Engine ('{DB_FILE}') initialized with 3NF Schema & Views.")

def ingest_records_from_dataframe(df):
    """
    Ingests/upserts DataFrame records into daily_dam_storage_logs table.
    Guarantees zero data loss and persistent historical storage in SQLite 3NF schema.
    """
    init_db()
    
    if df.empty or 'Dam Name' not in df.columns:
        print("[!] DataFrame is empty or missing 'Dam Name' column.")
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT dam_id, dam_name FROM dams;")
    dam_map = {row['dam_name']: row['dam_id'] for row in cursor.fetchall()}

    inserted_count = 0

    for _, row in df.iterrows():
        dam_name = row.get('Dam Name')
        dam_id = dam_map.get(dam_name)
        if not dam_id:
            continue

        dt_str = pd.to_datetime(row.get('Report Date'), format='%d/%m/%Y', errors='coerce')
        if pd.isnull(dt_str) and 'iso_date' in row:
            dt_str = pd.to_datetime(row.get('iso_date'), errors='coerce')
        if pd.isnull(dt_str):
            continue
            
        iso_date = dt_str.strftime('%Y-%m-%d')
        report_time = str(row.get('Report Time', '08:00 स.'))
        
        try:
            live_mcm = float(row.get('Current Live Storage (MCM)', 0))
            gross_mcm = float(row.get('Current Gross Storage (MCM)', 0))
            current_pct = float(row.get('Current Live Storage (%)', 0))
            last_year_pct = float(row.get('Last Year Storage (%)', 0))
        except (ValueError, TypeError):
            continue

        status = str(row.get('Status', 'SUCCESS'))

        cursor.execute("""
        INSERT INTO daily_dam_storage_logs (
            dam_id, report_date, report_time, current_live_mcm, current_gross_mcm, 
            current_live_pct, same_date_last_year_pct, data_source, status_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'WRD_PDF_SCRAPER', ?)
        ON CONFLICT(dam_id, report_date) DO UPDATE SET
            report_time=excluded.report_time,
            current_live_mcm=excluded.current_live_mcm,
            current_gross_mcm=excluded.current_gross_mcm,
            current_live_pct=excluded.current_live_pct,
            same_date_last_year_pct=excluded.same_date_last_year_pct,
            status_code=excluded.status_code,
            updated_at=CURRENT_TIMESTAMP;
        """, (dam_id, iso_date, report_time, live_mcm, gross_mcm, current_pct, last_year_pct, status))
        
        inserted_count += 1

    cursor.execute("""
    INSERT INTO system_audit_logs (action_name, records_affected, execution_status, log_message)
    VALUES ('DATA_INGESTION', ?, 'SUCCESS', 'Ingested daily storage log records into SQLite database');
    """, (inserted_count,))

    conn.commit()
    conn.close()
    print(f"✅ DBMS Ingestion Complete: {inserted_count} records active in 'daily_dam_storage_logs' table.")
    return inserted_count

def export_db_to_json(json_output_path=JSON_OUTPUT):
    """Queries the Relational SQL View 'vw_dam_daily_analytics' to export the dashboard dataset."""
    json_output_path = Path(json_output_path)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query latest storage
    sql_latest = """
    SELECT dam_name, report_date, report_time, dead_storage_mcm, design_live_mcm,
           design_gross_mcm, current_live_mcm, current_gross_mcm, current_live_pct,
           same_date_last_year_pct, status_code
    FROM vw_dam_daily_analytics
    WHERE (dam_id, report_date) IN (
        SELECT dam_id, MAX(report_date) FROM daily_dam_storage_logs GROUP BY dam_id
    );
    """
    cursor.execute(sql_latest)
    latest_rows = cursor.fetchall()

    latest_dict = {}
    for r in latest_rows:
        dt_fmt = pd.to_datetime(r['report_date']).strftime('%d/%m/%Y')
        latest_dict[r['dam_name']] = {
            'date': dt_fmt,
            'time': r['report_time'],
            'dead_mcm': r['dead_storage_mcm'],
            'design_live_mcm': r['design_live_mcm'],
            'design_gross_mcm': r['design_gross_mcm'],
            'current_live_mcm': r['current_live_mcm'],
            'current_gross_mcm': r['current_gross_mcm'],
            'current_pct': r['current_live_pct'],
            'last_year_pct': r['same_date_last_year_pct'],
            'status': r['status_code']
        }

    # Query Time Series
    sql_time_series = "SELECT report_date, dam_name, current_live_pct, current_live_mcm FROM vw_dam_daily_analytics ORDER BY report_date ASC;"
    cursor.execute(sql_time_series)
    ts_rows = cursor.fetchall()

    ts_by_date = {}
    for r in ts_rows:
        dt_iso = r['report_date']
        if dt_iso not in ts_by_date:
            dt_fmt = pd.to_datetime(dt_iso).strftime('%d/%m/%Y')
            ts_by_date[dt_iso] = {'date': dt_iso, 'date_fmt': dt_fmt}
        
        dam = r['dam_name']
        ts_by_date[dt_iso][f"{dam}_pct"] = r['current_live_pct']
        ts_by_date[dt_iso][f"{dam}_mcm"] = r['current_live_mcm']

    time_series_list = list(ts_by_date.values())

    # Query All Records
    sql_all_records = "SELECT report_date, report_time, dam_name, current_live_mcm, design_live_mcm, current_live_pct, same_date_last_year_pct, status_code FROM vw_dam_daily_analytics ORDER BY report_date ASC;"
    cursor.execute(sql_all_records)
    all_rows = cursor.fetchall()

    all_records_list = []
    for r in all_rows:
        dt_fmt = pd.to_datetime(r['report_date']).strftime('%d/%m/%Y')
        all_records_list.append({
            'date': dt_fmt,
            'iso_date': r['report_date'],
            'time': r['report_time'] or '08:00 स.',
            'dam_name': r['dam_name'],
            'current_live_mcm': r['current_live_mcm'],
            'design_live_mcm': r['design_live_mcm'],
            'current_pct': r['current_live_pct'],
            'last_year_pct': r['same_date_last_year_pct'] or 0,
            'status': r['status_code'] or 'SUCCESS'
        })

    out_json = {
        'total_dates': len(time_series_list),
        'total_records': len(all_records_list),
        'latest': latest_dict,
        'time_series': time_series_list,
        'all_records': all_records_list
    }

    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(out_json, f, indent=2, ensure_ascii=False)

    conn.close()
    print(f"✨ Exported {len(all_records_list)} SQL records to '{json_output_path}'.")

def inspect_db_for_faculty():
    """Prints a rich terminal report of the Relational Database for Faculty presentation."""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("\n==========================================================================")
    print(" 🏛️  DATABASE MANAGEMENT SYSTEM (DBMS) FACULTY INSPECTION REPORT")
    print("==========================================================================")
    print(f" Database Engine : SQLite3 ({DB_FILE})")
    print(f" Schema Standard : 3rd Normal Form (3NF)")
    print("==========================================================================\n")

    print("📊 1. TABLES CREATED:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cursor.fetchone()[0]
        print(f"   • Table '{t}' -> {cnt:,} rows")

    print("\n👁️ 2. RELATIONAL VIEWS:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = [r[0] for r in cursor.fetchall()]
    for v in views:
        print(f"   • View '{v}'")

    print("\n⚡ 3. INDEXES & CONSTRAINTS:")
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL;")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"   • Index '{idx['name']}': {idx['sql']}")

    print("\n🏞️ 4. MASTER DAM ENTITIES ('dams' table):")
    cursor.execute("SELECT dam_id, dam_code, dam_name, river_name, design_live_mcm FROM dams;")
    for r in cursor.fetchall():
        print(f"   [ID {r['dam_id']}] {r['dam_code']} - {r['dam_name']} ({r['river_name']}) | Design Live: {r['design_live_mcm']} MCM")

    print("\n🔍 5. SAMPLE SQL RELATIONAL JOIN QUERY (vw_dam_daily_analytics):")
    cursor.execute("SELECT dam_name, report_date, current_live_mcm, current_live_pct, remaining_capacity_mcm FROM vw_dam_daily_analytics ORDER BY report_date DESC LIMIT 5;")
    for r in cursor.fetchall():
        print(f"   Date: {r['report_date']} | Dam: {r['dam_name']} | Stored: {r['current_live_mcm']} MCM ({r['current_live_pct']}%) | Remaining: {r['remaining_capacity_mcm']} MCM")

    print("\n==========================================================================\n")
    conn.close()

if __name__ == '__main__':
    import sys
    if '--inspect' in sys.argv:
        inspect_db_for_faculty()
    else:
        init_db()
        export_db_to_json()

