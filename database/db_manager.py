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
    Dynamically auto-registers new state dams into 3NF master tables.
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
        dam_name = str(row.get('Dam Name', '')).strip()
        if not dam_name:
            continue
            
        dam_id = dam_map.get(dam_name)
        if not dam_id:
            # Auto-register new state dam into dams master table
            division_name = str(row.get('Division', 'Pune')).strip()
            district_name = str(row.get('District', division_name)).strip()
            
            cursor.execute("SELECT district_id FROM districts WHERE district_name LIKE ? OR district_name_mr LIKE ?;", (f"%{district_name}%", f"%{district_name}%"))
            dist_row = cursor.fetchone()
            dist_id = dist_row['district_id'] if dist_row else 1 # Default Pune district (id=1)
            
            dam_code = f"MH_{abs(hash(dam_name)) % 1000000:06d}"
            try:
                dead_val = float(row.get('Dead Storage (MCM)', 0.0))
            except Exception: dead_val = 0.0
            
            try:
                design_live_val = float(row.get('Design Live Storage (MCM)', 100.0))
            except Exception: design_live_val = 100.0
            if design_live_val <= 0: design_live_val = 100.0

            try:
                design_gross_val = float(row.get('Design Gross Storage (MCM)', dead_val + design_live_val))
            except Exception: design_gross_val = dead_val + design_live_val
            
            dam_name_mr = str(row.get('Dam Name MR', dam_name)).strip()
            
            cursor.execute("""
            INSERT OR IGNORE INTO dams (dam_code, dam_name, dam_name_mr, district_id, basin_id, river_name, dead_storage_mcm, design_live_mcm, design_gross_mcm)
            VALUES (?, ?, ?, ?, 1, 'State River', ?, ?, ?);
            """, (dam_code, dam_name, dam_name_mr, dist_id, dead_val, design_live_val, design_gross_val))
            
            cursor.execute("SELECT dam_id FROM dams WHERE dam_name = ?;", (dam_name,))
            new_dam_row = cursor.fetchone()
            if new_dam_row:
                dam_id = new_dam_row['dam_id']
                dam_map[dam_name] = dam_id

        if not dam_id:
            continue

        dt_str = pd.to_datetime(row.get('Report Date'), format='%d/%m/%Y', errors='coerce')
        if pd.isnull(dt_str) and 'iso_date' in row:
            dt_str = pd.to_datetime(row.get('iso_date'), errors='coerce')
        if pd.isnull(dt_str):
            continue
            
        iso_date = dt_str.strftime('%Y-%m-%d')
        report_time = str(row.get('Report Time', '08:00 AM'))
        
        try:
            live_mcm = float(row.get('Current Live Storage (MCM)', 0))
            gross_mcm = float(row.get('Current Gross Storage (MCM)', 0))
            
            cursor.execute("SELECT design_live_mcm FROM dams WHERE dam_id = ?;", (dam_id,))
            dam_res = cursor.fetchone()
            design_live_mcm = dam_res['design_live_mcm'] if dam_res else 100.0

            raw_pct = row.get('Current Live Storage (%)')
            if raw_pct is not None and str(raw_pct).strip() != '' and float(raw_pct) > 0:
                current_pct = float(raw_pct)
            elif design_live_mcm > 0 and live_mcm >= 0:
                current_pct = round((live_mcm / design_live_mcm) * 100, 2)
            else:
                current_pct = 0.0
                
            current_pct = min(150.0, max(0.0, current_pct))
            last_year_pct = min(150.0, max(0.0, float(row.get('Last Year Storage (%)', 0))))
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
    VALUES ('STATE_DATA_INGESTION', ?, 'SUCCESS', 'Ingested Maharashtra dam storage records into 3NF DBMS');
    """, (inserted_count,))

    conn.commit()
    conn.close()
    print(f"✅ DBMS State Ingestion Complete: {inserted_count} records active in 'daily_dam_storage_logs' table.")
    return inserted_count

def export_db_to_json(json_output_path=JSON_OUTPUT):
    """Queries the Relational SQL View 'vw_dam_daily_analytics' to export the dashboard dataset."""
    json_output_path = Path(json_output_path)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query Divisions & Districts list
    cursor.execute("SELECT division_name FROM divisions ORDER BY division_id ASC;")
    divisions = [r['division_name'] for r in cursor.fetchall()]

    cursor.execute("SELECT district_name FROM districts ORDER BY district_name ASC;")
    districts = [r['district_name'] for r in cursor.fetchall()]

    # Query latest storage for all dams in state
    sql_latest = """
    SELECT dam_name, dam_name_mr, district_name, division_name, basin_name, project_type,
           report_date, report_time, dead_storage_mcm, design_live_mcm,
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
            'district': r['district_name'],
            'division': r['division_name'],
            'basin': r['basin_name'],
            'type': r['project_type'],
            'dead_mcm': r['dead_storage_mcm'],
            'design_live_mcm': r['design_live_mcm'],
            'design_gross_mcm': r['design_gross_mcm'],
            'current_live_mcm': r['current_live_mcm'],
            'current_gross_mcm': r['current_gross_mcm'],
            'current_pct': r['current_live_pct'],
            'last_year_pct': r['same_date_last_year_pct'] or 0,
            'status': r['status_code'] or 'SUCCESS'
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
    sql_all_records = """
    SELECT report_date, report_time, dam_name, district_name, division_name, 
           current_live_mcm, design_live_mcm, current_live_pct, same_date_last_year_pct, status_code 
    FROM vw_dam_daily_analytics 
    ORDER BY report_date DESC, dam_name ASC;
    """
    cursor.execute(sql_all_records)
    all_rows = cursor.fetchall()

    all_records_list = []
    for r in all_rows:
        dt_fmt = pd.to_datetime(r['report_date']).strftime('%d/%m/%Y')
        all_records_list.append({
            'date': dt_fmt,
            'iso_date': r['report_date'],
            'time': r['report_time'] or '08:00 AM',
            'dam_name': r['dam_name'],
            'district': r['district_name'],
            'division': r['division_name'],
            'current_live_mcm': r['current_live_mcm'],
            'design_live_mcm': r['design_live_mcm'],
            'current_pct': r['current_live_pct'],
            'last_year_pct': r['same_date_last_year_pct'] or 0,
            'status': r['status_code'] or 'SUCCESS'
        })

    out_json = {
        'total_dams': len(latest_dict),
        'total_dates': len(time_series_list),
        'total_records': len(all_records_list),
        'divisions': divisions,
        'districts': districts,
        'latest': latest_dict,
        'time_series': time_series_list,
        'all_records': all_records_list
    }

    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(out_json, f, indent=2, ensure_ascii=False)

    conn.close()
    print(f"✨ Exported {len(all_records_list)} SQL records across {len(latest_dict)} Maharashtra dams to '{json_output_path}'.")

if __name__ == '__main__':
    init_db()
    export_db_to_json()
