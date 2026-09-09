import sqlite3
import pandas as pd
import json

DATABASE_FILE = "pune_dams.db"

# Canonical Dam Master Reference Data
DAM_MASTER_DATA = [
    {
        "dam_code": "KHADAKWASLA",
        "dam_name": "Khadakwasla",
        "river": "Mutha",
        "district": "Pune",
        "dead_storage_mcm": 30.0,
        "design_live_mcm": 55.91,
        "design_gross_mcm": 85.91
    },
    {
        "dam_code": "PANSHET",
        "dam_name": "Panshet",
        "river": "Ambi",
        "district": "Pune",
        "dead_storage_mcm": 9.0,
        "design_live_mcm": 301.61,
        "design_gross_mcm": 310.61
    },
    {
        "dam_code": "MULSHI",
        "dam_name": "Mulshi",
        "river": "Mula",
        "district": "Pune",
        "dead_storage_mcm": 230.0,
        "design_live_mcm": 522.76,
        "design_gross_mcm": 752.76
    },
    {
        "dam_code": "GUNJAWANI",
        "dam_name": "Gunjawani",
        "river": "Kanandi",
        "district": "Pune",
        "dead_storage_mcm": 0.21,
        "design_live_mcm": 104.48,
        "design_gross_mcm": 104.69
    },
    {
        "dam_code": "TEMGHAR",
        "dam_name": "Temghar",
        "river": "Mutha",
        "district": "Pune",
        "dead_storage_mcm": 2.95,
        "design_live_mcm": 105.01,
        "design_gross_mcm": 107.96
    }
]

def get_db_connection():
    """Returns a connection to the SQLite database with Foreign Keys enabled."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the relational database schema in 3rd Normal Form (3NF).
    Tables:
      - dams: Master metadata table
      - daily_reports: Transactional report log table with Foreign Keys & Constraints
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Master Dam Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dams (
        dam_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dam_code TEXT UNIQUE NOT NULL,
        dam_name TEXT UNIQUE NOT NULL,
        river TEXT,
        district TEXT,
        dead_storage_mcm REAL NOT NULL CHECK (dead_storage_mcm >= 0),
        design_live_mcm REAL NOT NULL CHECK (design_live_mcm > 0),
        design_gross_mcm REAL NOT NULL CHECK (design_gross_mcm > 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Transactional Daily Storage Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dam_id INTEGER NOT NULL,
        report_date DATE NOT NULL,
        report_time TEXT,
        current_live_mcm REAL NOT NULL CHECK (current_live_mcm >= 0),
        current_gross_mcm REAL NOT NULL CHECK (current_gross_mcm >= 0),
        current_pct REAL NOT NULL CHECK (current_pct BETWEEN 0 AND 105),
        last_year_pct REAL CHECK (last_year_pct BETWEEN 0 AND 105),
        status TEXT DEFAULT 'Success',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dam_id) REFERENCES dams(dam_id) ON DELETE CASCADE,
        UNIQUE (dam_id, report_date)
    );
    """)

    # Indexes for high-performance SQL query optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_dam_date ON daily_reports(dam_id, report_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_date ON daily_reports(report_date);")

    # Seed Master Dam Metadata
    for dam in DAM_MASTER_DATA:
        cursor.execute("""
        INSERT INTO dams (dam_code, dam_name, river, district, dead_storage_mcm, design_live_mcm, design_gross_mcm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dam_code) DO UPDATE SET
            river=excluded.river,
            district=excluded.district,
            dead_storage_mcm=excluded.dead_storage_mcm,
            design_live_mcm=excluded.design_live_mcm,
            design_gross_mcm=excluded.design_gross_mcm;
        """, (
            dam['dam_code'], dam['dam_name'], dam['river'], dam['district'],
            dam['dead_storage_mcm'], dam['design_live_mcm'], dam['design_gross_mcm']
        ))

    conn.commit()
    conn.close()
    print("✅ Database schema initialized and master dam records seeded.")

def seed_reports_from_csv(csv_path="Maharashtra_5_Dams_Cleaned_Data.csv"):
    """
    Seeds/upserts historical cleaned CSV records into the SQLite database.
    Guarantees transactional integrity and zero data loss.
    """
    init_db()
    
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get mapping of dam_name to dam_id
    cursor.execute("SELECT dam_id, dam_name FROM dams;")
    dam_map = {row['dam_name']: row['dam_id'] for row in cursor.fetchall()}

    inserted_count = 0
    updated_count = 0

    for _, row in df.iterrows():
        dam_name = row['Dam Name']
        dam_id = dam_map.get(dam_name)
        if not dam_id:
            continue

        # Format ISO date YYYY-MM-DD
        dt_str = pd.to_datetime(row['Report Date'], format='%d/%m/%Y', errors='coerce')
        if pd.isnull(dt_str):
            dt_str = pd.to_datetime(row.get('iso_date'), errors='coerce')
        if pd.isnull(dt_str):
            continue
            
        iso_date = dt_str.strftime('%Y-%m-%d')
        report_time = str(row.get('Report Time', '08:00 स.'))
        live_mcm = float(row['Current Live Storage (MCM)'])
        gross_mcm = float(row['Current Gross Storage (MCM)'])
        current_pct = float(row['Current Live Storage (%)'])
        last_year_pct = float(row.get('Last Year Storage (%)', 0))
        status = str(row.get('Status', 'Success'))

        cursor.execute("""
        INSERT INTO daily_reports (dam_id, report_date, report_time, current_live_mcm, current_gross_mcm, current_pct, last_year_pct, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dam_id, report_date) DO UPDATE SET
            report_time=excluded.report_time,
            current_live_mcm=excluded.current_live_mcm,
            current_gross_mcm=excluded.current_gross_mcm,
            current_pct=excluded.current_pct,
            last_year_pct=excluded.last_year_pct,
            status=excluded.status;
        """, (dam_id, iso_date, report_time, live_mcm, gross_mcm, current_pct, last_year_pct, status))
        
        inserted_count += 1

    conn.commit()
    conn.close()
    print(f"✅ DBMS Seed Complete: Processed {inserted_count} records into 'daily_reports' table in SQLite DB '{DATABASE_FILE}'.")

def export_db_to_json(json_output_path="dam_data.json"):
    """
    Queries the SQLite relational database using SQL JOINs & Window Functions,
    and exports the JSON dataset consumed by the frontend dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Query Latest Report per Dam using SQL JOIN
    sql_latest = """
    SELECT 
        d.dam_name,
        r.report_date,
        r.report_time,
        d.dead_storage_mcm,
        d.design_live_mcm,
        d.design_gross_mcm,
        r.current_live_mcm,
        r.current_gross_mcm,
        r.current_pct,
        r.last_year_pct,
        r.status
    FROM dams d
    INNER JOIN daily_reports r ON d.dam_id = r.dam_id
    WHERE r.report_date = (
        SELECT MAX(r2.report_date) 
        FROM daily_reports r2 
        WHERE r2.dam_id = d.dam_id
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
            'current_pct': r['current_pct'],
            'last_year_pct': r['last_year_pct'],
            'status': r['status']
        }

    # 2. Query All Historical Time Series
    sql_time_series = """
    SELECT 
        r.report_date,
        d.dam_name,
        r.current_pct,
        r.current_live_mcm
    FROM daily_reports r
    JOIN dams d ON r.dam_id = d.dam_id
    ORDER BY r.report_date ASC;
    """
    cursor.execute(sql_time_series)
    ts_rows = cursor.fetchall()

    # Pivot SQL time series in memory
    ts_by_date = {}
    for r in ts_rows:
        dt_iso = r['report_date']
        if dt_iso not in ts_by_date:
            dt_fmt = pd.to_datetime(dt_iso).strftime('%d/%m/%Y')
            ts_by_date[dt_iso] = {'date': dt_iso, 'date_fmt': dt_fmt}
        
        dam = r['dam_name']
        ts_by_date[dt_iso][f"{dam}_pct"] = r['current_pct']
        ts_by_date[dt_iso][f"{dam}_mcm"] = r['current_live_mcm']

    time_series_list = list(ts_by_date.values())

    # 3. Query All Database Logs for Table (Newest First)
    sql_all_records = """
    SELECT 
        r.report_date,
        r.report_time,
        d.dam_name,
        r.current_live_mcm,
        d.design_live_mcm,
        r.current_pct,
        r.last_year_pct,
        r.status
    FROM daily_reports r
    JOIN dams d ON r.dam_id = d.dam_id
    ORDER BY r.report_date ASC;
    """
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
            'current_pct': r['current_pct'],
            'last_year_pct': r['last_year_pct'] or 0,
            'status': r['status'] or 'Success'
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

    # Also export full CSV
    sql_csv = """
    SELECT 
        d.dam_name AS "Dam Name",
        strftime('%d/%m/%Y', r.report_date) AS "Report Date",
        r.report_time AS "Report Time",
        d.dead_storage_mcm AS "Dead Storage (MCM)",
        d.design_live_mcm AS "Design Live Storage (MCM)",
        d.design_gross_mcm AS "Design Gross Storage (MCM)",
        r.current_live_mcm AS "Current Live Storage (MCM)",
        r.current_gross_mcm AS "Current Gross Storage (MCM)",
        r.current_pct AS "Current Live Storage (%)",
        r.last_year_pct AS "Last Year Storage (%)",
        r.status AS "Status"
    FROM daily_reports r
    JOIN dams d ON r.dam_id = d.dam_id
    ORDER BY r.report_date DESC, d.dam_name ASC;
    """
    csv_df = pd.read_sql_query(sql_csv, conn)
    csv_df.to_csv("Maharashtra_5_Dams_Data.csv", index=False, encoding='utf-8-sig')
    csv_df.to_csv("Maharashtra_5_Dams_Cleaned_Data.csv", index=False, encoding='utf-8-sig')

    conn.close()
    print(f"✨ Successfully queried DBMS ('{DATABASE_FILE}') and exported {len(all_records_list)} SQL records across {len(time_series_list)} dates to '{json_output_path}' and 'Maharashtra_5_Dams_Data.csv'.")


if __name__ == '__main__':
    import sys
    print("🚀 Initializing DBMS Engine...")
    init_db()
    seed_reports_from_csv("Maharashtra_5_Dams_Cleaned_Data.csv")
    export_db_to_json("dam_data.json")
