import sqlite3
import pandas as pd
import json
import os
import re
from pathlib import Path

# Paths relative to repository root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "pune_dams.db"
SCHEMA_FILE = BASE_DIR / "database" / "schema.sql"
REGISTRY_FILE = BASE_DIR / "database" / "dam_registry.json"
WEB_DATA_DIR = BASE_DIR / "web" / "data"

def get_db_connection():
    """Returns a connection to the SQLite database with Foreign Keys enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the 3NF relational database schema and seeds administrative/hydrological master tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Legacy schema migration check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dams';")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(dams);")
        columns = [row[1] for row in cursor.fetchall()]
        if 'dam_slug' not in columns:
            print("[!] Legacy table schema detected. Dropping legacy tables for 3NF upgrade...")
            cursor.executescript("""
                DROP VIEW IF EXISTS vw_dam_daily_analytics;
                DROP TABLE IF EXISTS dam_daily_logs;
                DROP TABLE IF EXISTS daily_water_levels;
                DROP TABLE IF EXISTS dams;
                DROP TABLE IF EXISTS districts;
                DROP TABLE IF EXISTS divisions;
                DROP TABLE IF EXISTS basins;
            """)

    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())

    # Load dam registry
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        registry = [item for item in raw_data if isinstance(item, dict) and 'slug' in item and 'division' in item]

        # 1. Seed Divisions
        divisions = sorted(list({item['division'] for item in registry}))
        for div in divisions:
            cursor.execute("INSERT OR IGNORE INTO divisions (division_name) VALUES (?);", (div,))

        cursor.execute("SELECT division_id, division_name FROM divisions;")
        div_map = {row['division_name']: row['division_id'] for row in cursor.fetchall()}

        # 2. Seed Districts
        districts = {(item['district'], item['division']) for item in registry}
        for dist_name, div_name in districts:
            div_id = div_map.get(div_name, 1)
            cursor.execute("INSERT OR IGNORE INTO districts (district_name, division_id) VALUES (?, ?);", (dist_name, div_id))

        cursor.execute("SELECT district_id, district_name FROM districts;")
        dist_map = {row['district_name']: row['district_id'] for row in cursor.fetchall()}

        # 3. Seed River Basins
        basins = sorted(list({item['basin'] for item in registry}))
        for bname in basins:
            cursor.execute("INSERT OR IGNORE INTO basins (basin_name) VALUES (?);", (bname,))

        cursor.execute("SELECT basin_id, basin_name FROM basins;")
        basin_map = {row['basin_name']: row['basin_id'] for row in cursor.fetchall()}

        # 4. Seed Dams Metadata
        for item in registry:
            slug = item['slug']
            name_en = item['en']
            name_mr = item['mr']
            dist_id = dist_map.get(item['district'], 1)
            basin_id = basin_map.get(item['basin'], 1)
            ptype = item.get('type', 'MAJOR')
            dead = float(item.get('dead', 0.0))
            live = float(item.get('live', 100.0))
            gross = float(item.get('gross', dead + live))
            if gross < live:
                gross = live + dead

            cursor.execute("""
            INSERT INTO dams (
                dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, 
                project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dam_slug) DO UPDATE SET
                dam_name_en = excluded.dam_name_en,
                dam_name_mr = excluded.dam_name_mr,
                district_id = excluded.district_id,
                basin_id = excluded.basin_id,
                dead_storage_mcm = excluded.dead_storage_mcm,
                design_live_mcm = excluded.design_live_mcm,
                design_gross_mcm = excluded.design_gross_mcm;
            """, (slug, name_en, name_mr, dist_id, basin_id, ptype, dead, live, gross))

    conn.commit()
    conn.close()
    print(f"✅ DBMS Engine ('{DB_FILE}') initialized with 3NF Schema & Master Registries.")

def get_dam_lookup_map():
    """Returns a lookup dictionary mapping raw/damaged dam names to dam_id and metadata."""
    if not REGISTRY_FILE.exists():
        return {}
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    registry = [item for item in raw_data if isinstance(item, dict) and 'slug' in item]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dam_id, dam_slug FROM dams;")
    slug_to_id = {row['dam_slug']: row['dam_id'] for row in cursor.fetchall()}
    conn.close()

    lookup = {}
    for item in registry:
        did = slug_to_id.get(item['slug'])
        if not did:
            continue
        info = {
            'dam_id': did,
            'slug': item['slug'],
            'en': item['en'],
            'mr': item['mr'],
            'design_live_mcm': float(item.get('live', 100.0)),
            'design_gross_mcm': float(item.get('gross', 110.0))
        }
        lookup[item['slug']] = info
        lookup[item['en'].lower()] = info
        lookup[item['mr'].lower()] = info
        for k in item.get('keys', []):
            lookup[k.lower()] = info

    return lookup

def ingest_records_from_dataframe(df):
    """
    Ingests DataFrame records into dam_daily_logs via ACID-compliant SQLite UPSERT transactions.
    Validates domain assertions and rejects epoch/invalid dates.
    """
    init_db()
    if df.empty:
        print("[!] DataFrame is empty.")
        return 0

    lookup = get_dam_lookup_map()
    conn = get_db_connection()
    cursor = conn.cursor()

    inserted_count = 0

    conn.execute("BEGIN TRANSACTION;")
    try:
        for _, row in df.iterrows():
            raw_name = str(row.get('Dam Name', '')).strip()
            if not raw_name:
                continue

            info = lookup.get(raw_name.lower())
            if not info and 'Dam Name MR' in row:
                info = lookup.get(str(row['Dam Name MR']).strip().lower())
            if not info:
                continue

            dam_id = info['dam_id']
            design_live_mcm = info['design_live_mcm']

            # Date Validation & Epoch Date Elimination
            raw_date = row.get('Report Date') or row.get('reading_date') or row.get('iso_date')
            dt_obj = pd.to_datetime(raw_date, format='%d/%m/%Y', errors='coerce')
            if pd.isnull(dt_obj):
                dt_obj = pd.to_datetime(raw_date, errors='coerce')

            if pd.isnull(dt_obj) or dt_obj.year < 2024:
                # Reject epoch dates (e.g., 1970-01-16 / 1970-01-17)
                continue

            reading_date = dt_obj.strftime('%Y-%m-%d')
            reading_time = str(row.get('Report Time', '08:00 AM'))

            # Capacity Domain Validations & Assertions
            try:
                live_mcm = float(row.get('Current Live Storage (MCM)', 0.0))
            except (ValueError, TypeError):
                live_mcm = 0.0

            try:
                gross_mcm = float(row.get('Current Gross Storage (MCM)', live_mcm))
            except (ValueError, TypeError):
                gross_mcm = live_mcm

            # Domain Assertion 1: Avoid inverted capacities
            if gross_mcm < live_mcm:
                gross_mcm = live_mcm

            # Domain Assertion 2: Column realignment check for over-capacity bounds
            if design_live_mcm > 0 and live_mcm > design_live_mcm * 1.5:
                # Potential column index shift anomaly detected - cap or adjust
                live_mcm = min(live_mcm, design_live_mcm)

            # Percentage calculation
            raw_pct = row.get('Current Live Storage (%)')
            if raw_pct is not None and str(raw_pct).strip() != '' and float(raw_pct) > 0:
                storage_pct = float(raw_pct)
            elif design_live_mcm > 0:
                storage_pct = round((live_mcm / design_live_mcm) * 100.0, 2)
            else:
                storage_pct = 0.0

            storage_pct = min(120.0, max(0.0, storage_pct))

            try:
                last_year_pct = float(row.get('Last Year Storage (%)', 0.0))
                last_year_pct = min(120.0, max(0.0, last_year_pct))
            except (ValueError, TypeError):
                last_year_pct = None

            cursor.execute("""
            INSERT INTO dam_daily_logs (
                dam_id, reading_date, reading_time, live_storage_mcm, 
                gross_storage_mcm, storage_pct, last_year_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dam_id, reading_date) DO UPDATE SET
                reading_time = excluded.reading_time,
                live_storage_mcm = excluded.live_storage_mcm,
                gross_storage_mcm = excluded.gross_storage_mcm,
                storage_pct = excluded.storage_pct,
                last_year_pct = excluded.last_year_pct;
            """, (dam_id, reading_date, reading_time, live_mcm, gross_mcm, storage_pct, last_year_pct))

            inserted_count += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[!] DBMS Transaction Rollback due to error: {e}")
        raise e
    finally:
        conn.close()

    print(f"✅ Atomic DBMS Ingestion Complete: {inserted_count} records upserted into 'dam_daily_logs'.")
    return inserted_count

def purge_corrupt_logs():
    """Purges corrupt records with invalid dates outside [2024-01-01, 2026-12-31]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dam_daily_logs WHERE reading_date < '2024-01-01' OR reading_date > '2026-12-31';")
    purged = cursor.rowcount
    conn.commit()
    conn.close()
    if purged > 0:
        print(f"🧹 Purged {purged} corrupt log records outside 2024–2026 range.")
    return purged

def export_decoupled_json():
    """
    Exports 3NF database content into decoupled static JSON files for web serving:
    1. web/data/latest.json (~20 KB): Latest Available Snapshot for all dams.
    2. web/data/history/{dam_slug}.json (~10-15 KB each): Compact chronological time-series array [{"d": "YYYY-MM-DD", "m": live_mcm, "p": pct}].
    """
    init_db()
    purge_corrupt_logs()

    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    history_dir = WEB_DATA_DIR / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query latest date across all logs
    cursor.execute("SELECT MAX(reading_date) AS max_date FROM dam_daily_logs;")
    max_date_row = cursor.fetchone()
    latest_batch_date = max_date_row['max_date'] if max_date_row and max_date_row['max_date'] else None

    # 1. Generate Latest Snapshot JSON
    sql_latest = """
    SELECT 
        d.dam_id, d.dam_slug, d.dam_name_en, d.dam_name_mr,
        dt.district_name, dv.division_name, b.basin_name,
        d.project_type, d.dead_storage_mcm, d.design_live_mcm, d.design_gross_mcm,
        l.reading_date, l.reading_time, l.live_storage_mcm, l.gross_storage_mcm,
        l.storage_pct, l.last_year_pct,
        ROUND(d.design_live_mcm - l.live_storage_mcm, 2) AS remaining_capacity_mcm
    FROM dams d
    JOIN districts dt ON d.district_id = dt.district_id
    JOIN divisions dv ON dt.division_id = dv.division_id
    JOIN basins b ON d.basin_id = b.basin_id
    LEFT JOIN dam_daily_logs l ON d.dam_id = l.dam_id AND l.reading_date = (
        SELECT MAX(reading_date) FROM dam_daily_logs WHERE dam_id = d.dam_id
    )
    ORDER BY d.dam_name_en ASC;
    """
    cursor.execute(sql_latest)
    latest_rows = cursor.fetchall()

    latest_dams = {}
    for r in latest_rows:
        latest_dams[r['dam_slug']] = {
            'dam_id': r['dam_id'],
            'slug': r['dam_slug'],
            'name_en': r['dam_name_en'],
            'name_mr': r['dam_name_mr'] or r['dam_name_en'],
            'district': r['district_name'],
            'division': r['division_name'],
            'basin': r['basin_name'],
            'type': r['project_type'],
            'dead_mcm': r['dead_storage_mcm'],
            'design_live_mcm': r['design_live_mcm'],
            'design_gross_mcm': r['design_gross_mcm'],
            'date': r['reading_date'],
            'time': r['reading_time'] or '08:00 AM',
            'live_mcm': r['live_storage_mcm'] if r['live_storage_mcm'] is not None else 0.0,
            'gross_mcm': r['gross_storage_mcm'] if r['gross_storage_mcm'] is not None else 0.0,
            'pct': r['storage_pct'] if r['storage_pct'] is not None else 0.0,
            'last_year_pct': r['last_year_pct'] if r['last_year_pct'] is not None else 0.0,
            'remaining_mcm': r['remaining_capacity_mcm'] if r['remaining_capacity_mcm'] is not None else r['design_live_mcm']
        }

    snapshot_data = {
        'batch_date': latest_batch_date,
        'total_dams': len(latest_dams),
        'dams': latest_dams
    }

    latest_path = WEB_DATA_DIR / "latest.json"
    latest_snapshot_path = WEB_DATA_DIR / "latest_snapshot.json"
    
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
    with open(latest_snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

    size_kb = latest_path.stat().st_size / 1024
    print(f"✨ Exported 'web/data/latest.json' & 'latest_snapshot.json' ({size_kb:.1f} KB, {len(latest_dams)} dams).")

    # 2. Generate per-dam compact history JSON files
    cursor.execute("SELECT dam_id, dam_slug FROM dams;")
    all_dams = cursor.fetchall()

    exported_histories = 0
    for drow in all_dams:
        did = drow['dam_id']
        slug = drow['dam_slug']

        cursor.execute("""
        SELECT reading_date, live_storage_mcm, gross_storage_mcm, storage_pct, last_year_pct
        FROM dam_daily_logs
        WHERE dam_id = ? AND reading_date >= '2024-01-01' AND reading_date <= '2026-12-31'
        ORDER BY reading_date ASC;
        """, (did,))
        hrows = cursor.fetchall()

        history_points = []
        for hr in hrows:
            history_points.append({
                'd': hr['reading_date'],
                'm': hr['live_storage_mcm'],
                'p': hr['storage_pct'],
                'date': hr['reading_date'],
                'mcm': hr['live_storage_mcm'],
                'pct': hr['storage_pct']
            })

        h_path = history_dir / f"{slug}.json"
        with open(h_path, 'w', encoding='utf-8') as f:
            json.dump(history_points, f, indent=2, ensure_ascii=False)
        exported_histories += 1

    conn.close()
    print(f"✨ Exported {exported_histories} decoupled dam time-series files to 'web/data/history/*.json'.")

if __name__ == '__main__':
    init_db()
    export_decoupled_json()
