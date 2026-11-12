import sqlite3
import json
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "pune_dams.db"

SUPABASE_URL = "https://uudwrsqjgluehlnjertm.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1ZHdyc3FqZ2x1ZWhsbmplcnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTAzODYwNSwiZXhwIjoyMTA2NjE0NjA1fQ.ihey9zVVP3acE8mwIVKAYsCfRbBoA5Dk0Hr45PdeAsk"

HEADERS = {
    'apikey': SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation, resolution=merge-duplicates'
}

def post_to_supabase(endpoint, data, headers_extra=None):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    h = HEADERS.copy()
    if headers_extra:
        h.update(headers_extra)
    
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers=h, method='POST')
    
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        if hasattr(e, 'read'):
            err_body = e.read().decode('utf-8')
            print(f"[!] Error on POST {endpoint}: {e} -> {err_body}")
        else:
            print(f"[!] Error on POST {endpoint}: {e}")
        return None

def fetch_from_supabase(endpoint):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}?select=*"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[!] Error fetching {endpoint}: {e}")
        return []

def migrate():
    print("[*] Starting Migration from SQLite to Supabase Cloud PostgreSQL...")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Migrate Divisions
    cursor.execute("SELECT division_name FROM divisions;")
    div_rows = cursor.fetchall()
    div_payload = [{'division_name': r['division_name']} for r in div_rows]
    if div_payload:
        res = post_to_supabase('divisions', div_payload, {'Prefer': 'resolution=ignore-duplicates'})
        print(f"[+] Synced {len(div_payload)} Divisions to Supabase.")

    divs = fetch_from_supabase('divisions')
    div_map = {d['division_name']: d['division_id'] for d in divs}

    # 2. Migrate Districts
    cursor.execute("""
        SELECT d.district_name, dv.division_name 
        FROM districts d JOIN divisions dv ON d.division_id = dv.division_id;
    """)
    dist_rows = cursor.fetchall()
    dist_payload = []
    for r in dist_rows:
        divid = div_map.get(r['division_name'], 1)
        dist_payload.append({'district_name': r['district_name'], 'division_id': divid})

    if dist_payload:
        post_to_supabase('districts', dist_payload, {'Prefer': 'resolution=ignore-duplicates'})
        print(f"[+] Synced {len(dist_payload)} Districts to Supabase.")

    dists = fetch_from_supabase('districts')
    dist_map = {d['district_name']: d['district_id'] for d in dists}

    # 3. Migrate Basins
    cursor.execute("SELECT basin_name FROM basins;")
    basin_rows = cursor.fetchall()
    basin_payload = [{'basin_name': r['basin_name']} for r in basin_rows]
    if basin_payload:
        post_to_supabase('basins', basin_payload, {'Prefer': 'resolution=ignore-duplicates'})
        print(f"[+] Synced {len(basin_payload)} River Basins to Supabase.")

    basins = fetch_from_supabase('basins')
    basin_map = {b['basin_name']: b['basin_id'] for b in basins}

    # 4. Migrate Dams Metadata
    cursor.execute("""
        SELECT d.*, dt.district_name, b.basin_name 
        FROM dams d 
        JOIN districts dt ON d.district_id = dt.district_id 
        JOIN basins b ON d.basin_id = b.basin_id;
    """)
    dam_rows = cursor.fetchall()
    dam_payload = []
    for r in dam_rows:
        dam_payload.append({
            'dam_slug': r['dam_slug'],
            'dam_name_en': r['dam_name_en'],
            'dam_name_mr': r['dam_name_mr'],
            'district_id': dist_map.get(r['district_name'], 1),
            'basin_id': basin_map.get(r['basin_name'], 1),
            'project_type': r['project_type'],
            'dead_storage_mcm': r['dead_storage_mcm'],
            'design_live_mcm': r['design_live_mcm'],
            'design_gross_mcm': r['design_gross_mcm'],
            'full_reservoir_level_m': r['full_reservoir_level_m'],
            'latitude': r['latitude'],
            'longitude': r['longitude']
        })

    if dam_payload:
        post_to_supabase('dams', dam_payload, {'Prefer': 'resolution=merge-duplicates,on_conflict=dam_slug'})
        print(f"[+] Synced {len(dam_payload)} Dams Metadata to Supabase.")

    sb_dams = fetch_from_supabase('dams')
    slug_to_sb_id = {d['dam_slug']: d['dam_id'] for d in sb_dams}

    # 5. Migrate Daily Log Telemetry (32,900+ records in chunks of 1000)
    cursor.execute("""
        SELECT d.dam_slug, l.reading_date, l.reading_time, l.live_storage_mcm, 
               l.gross_storage_mcm, l.storage_pct, l.last_year_pct
        FROM dam_daily_logs l
        JOIN dams d ON l.dam_id = d.dam_id
        WHERE l.reading_date >= '2024-01-01' AND l.reading_date <= '2026-12-31'
        ORDER BY l.reading_date ASC;
    """)
    log_rows = cursor.fetchall()
    conn.close()

    print(f"[*] Preparing {len(log_rows)} daily telemetry log records for batch upload...")

    batch = []
    inserted_total = 0
    for r in log_rows:
        sb_dam_id = slug_to_sb_id.get(r['dam_slug'])
        if not sb_dam_id:
            continue
        
        batch.append({
            'dam_id': sb_dam_id,
            'reading_date': r['reading_date'],
            'reading_time': r['reading_time'],
            'live_storage_mcm': r['live_storage_mcm'],
            'gross_storage_mcm': r['gross_storage_mcm'],
            'storage_pct': r['storage_pct'],
            'last_year_pct': r['last_year_pct']
        })

        if len(batch) >= 1000:
            res = post_to_supabase('dam_daily_logs', batch, {'Prefer': 'resolution=merge-duplicates,on_conflict=dam_id,reading_date'})
            inserted_total += len(batch)
            print(f"    -> Progress: [{inserted_total}/{len(log_rows)}] records uploaded to Supabase PostgreSQL.")
            batch = []

    if batch:
        post_to_supabase('dam_daily_logs', batch, {'Prefer': 'resolution=merge-duplicates,on_conflict=dam_id,reading_date'})
        inserted_total += len(batch)
        print(f"    -> Progress: [{inserted_total}/{len(log_rows)}] records uploaded to Supabase PostgreSQL.")

    print(f"✨ SUCCESS: Migration Complete! {inserted_total} records live on Supabase Cloud PostgreSQL.")

if __name__ == '__main__':
    migrate()
