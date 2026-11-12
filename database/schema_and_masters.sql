-- ============================================================================
-- MAHARASHTRA DAM DATABASE - SUPABASE POSTGRESQL MASTER SCHEMA & DATA SEED
-- ============================================================================

-- 1. Divisions
CREATE TABLE IF NOT EXISTS divisions (
    division_id SERIAL PRIMARY KEY,
    division_name TEXT NOT NULL UNIQUE
);

-- 2. Districts
CREATE TABLE IF NOT EXISTS districts (
    district_id SERIAL PRIMARY KEY,
    district_name TEXT NOT NULL UNIQUE,
    division_id INT NOT NULL REFERENCES divisions(division_id) ON DELETE RESTRICT
);

-- 3. River Basins
CREATE TABLE IF NOT EXISTS basins (
    basin_id SERIAL PRIMARY KEY,
    basin_name TEXT NOT NULL UNIQUE
);

-- 4. Dams Metadata
CREATE TABLE IF NOT EXISTS dams (
    dam_id SERIAL PRIMARY KEY,
    dam_slug TEXT NOT NULL UNIQUE,
    dam_name_en TEXT NOT NULL,
    dam_name_mr TEXT,
    district_id INT NOT NULL REFERENCES districts(district_id),
    basin_id INT NOT NULL REFERENCES basins(basin_id),
    project_type TEXT NOT NULL CHECK(project_type IN ('MAJOR', 'MEDIUM', 'MINOR')),
    dead_storage_mcm NUMERIC NOT NULL DEFAULT 0.0 CHECK(dead_storage_mcm >= 0),
    design_live_mcm NUMERIC NOT NULL CHECK(design_live_mcm > 0),
    design_gross_mcm NUMERIC NOT NULL CHECK(design_gross_mcm >= design_live_mcm),
    full_reservoir_level_m NUMERIC,
    latitude NUMERIC,
    longitude NUMERIC
);

-- 5. Daily Telemetry Logs
CREATE TABLE IF NOT EXISTS dam_daily_logs (
    log_id BIGSERIAL PRIMARY KEY,
    dam_id INT NOT NULL REFERENCES dams(dam_id) ON DELETE CASCADE,
    reading_date DATE NOT NULL,
    reading_time TEXT,
    live_storage_mcm NUMERIC NOT NULL CHECK(live_storage_mcm >= 0),
    gross_storage_mcm NUMERIC NOT NULL CHECK(gross_storage_mcm >= live_storage_mcm),
    storage_pct NUMERIC NOT NULL CHECK(storage_pct >= 0 AND storage_pct <= 120.0),
    last_year_pct NUMERIC CHECK(last_year_pct IS NULL OR (last_year_pct >= 0 AND last_year_pct <= 120.0)),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_dam_daily_log UNIQUE (dam_id, reading_date)
);

CREATE INDEX IF NOT EXISTS idx_logs_dam_date ON dam_daily_logs(dam_id, reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_logs_date ON dam_daily_logs(reading_date);

-- Enable RLS and Permissive API Access
ALTER TABLE divisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE districts ENABLE ROW LEVEL SECURITY;
ALTER TABLE basins ENABLE ROW LEVEL SECURITY;
ALTER TABLE dams ENABLE ROW LEVEL SECURITY;
ALTER TABLE dam_daily_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public select divisions" ON divisions FOR SELECT USING (true);
CREATE POLICY "Public select districts" ON districts FOR SELECT USING (true);
CREATE POLICY "Public select basins" ON basins FOR SELECT USING (true);
CREATE POLICY "Public select dams" ON dams FOR SELECT USING (true);
CREATE POLICY "Public select dam_daily_logs" ON dam_daily_logs FOR SELECT USING (true);

GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role, postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role, postgres;

BEGIN;

INSERT INTO divisions (division_name) VALUES ('Amravati') ON CONFLICT (division_name) DO NOTHING;
INSERT INTO divisions (division_name) VALUES ('Chhatrapati Sambhajinagar') ON CONFLICT (division_name) DO NOTHING;
INSERT INTO divisions (division_name) VALUES ('Kokan') ON CONFLICT (division_name) DO NOTHING;
INSERT INTO divisions (division_name) VALUES ('Nagpur') ON CONFLICT (division_name) DO NOTHING;
INSERT INTO divisions (division_name) VALUES ('Nashik') ON CONFLICT (division_name) DO NOTHING;
INSERT INTO divisions (division_name) VALUES ('Pune') ON CONFLICT (division_name) DO NOTHING;

INSERT INTO districts (district_name, division_id) VALUES ('Buldhana', (SELECT division_id FROM divisions WHERE division_name='Amravati')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Parbhani', (SELECT division_id FROM divisions WHERE division_name='Chhatrapati Sambhajinagar')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Nagpur', (SELECT division_id FROM divisions WHERE division_name='Nagpur')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Gondia', (SELECT division_id FROM divisions WHERE division_name='Nagpur')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Nashik', (SELECT division_id FROM divisions WHERE division_name='Nashik')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Palghar', (SELECT division_id FROM divisions WHERE division_name='Kokan')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Jalgaon', (SELECT division_id FROM divisions WHERE division_name='Nashik')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Ahmednagar', (SELECT division_id FROM divisions WHERE division_name='Nashik')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Raigad', (SELECT division_id FROM divisions WHERE division_name='Kokan')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Hingoli', (SELECT division_id FROM divisions WHERE division_name='Chhatrapati Sambhajinagar')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Gadchiroli', (SELECT division_id FROM divisions WHERE division_name='Nagpur')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Sangli', (SELECT division_id FROM divisions WHERE division_name='Pune')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Chhatrapati Sambhajinagar', (SELECT division_id FROM divisions WHERE division_name='Chhatrapati Sambhajinagar')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Solapur', (SELECT division_id FROM divisions WHERE division_name='Pune')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Dharashiv', (SELECT division_id FROM divisions WHERE division_name='Chhatrapati Sambhajinagar')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Yavatmal', (SELECT division_id FROM divisions WHERE division_name='Amravati')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Thane', (SELECT division_id FROM divisions WHERE division_name='Kokan')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Beed', (SELECT division_id FROM divisions WHERE division_name='Chhatrapati Sambhajinagar')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Kolhapur', (SELECT division_id FROM divisions WHERE division_name='Pune')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Nanded', (SELECT division_id FROM divisions WHERE division_name='Chhatrapati Sambhajinagar')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Akola', (SELECT division_id FROM divisions WHERE division_name='Amravati')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Sindhudurg', (SELECT division_id FROM divisions WHERE division_name='Kokan')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Satara', (SELECT division_id FROM divisions WHERE division_name='Pune')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Pune', (SELECT division_id FROM divisions WHERE division_name='Pune')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Wardha', (SELECT division_id FROM divisions WHERE division_name='Nagpur')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Chandrapur', (SELECT division_id FROM divisions WHERE division_name='Nagpur')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Bhandara', (SELECT division_id FROM divisions WHERE division_name='Nagpur')) ON CONFLICT (district_name) DO NOTHING;
INSERT INTO districts (district_name, division_id) VALUES ('Amravati', (SELECT division_id FROM divisions WHERE division_name='Amravati')) ON CONFLICT (district_name) DO NOTHING;

INSERT INTO basins (basin_name) VALUES ('Godavari River Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Tapi River Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Wainganga / Godavari Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('West Flowing Rivers (Konkan)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Aundha Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Bagh Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Bham Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Darna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Dudhana Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Godavari Main)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Kadva Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Kadwa Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Kolvan Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Manar Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Manjara Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Mula Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Pench Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Penganga Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Pranhita Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Pravara Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Purna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Sindphana Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Sur Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Terna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Unanda Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Wainganga Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Godavari River Basin (Wardha Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Ambi Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Arpa Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Bhama Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Bhima Main)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Bhima Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Bhogawati Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Dudhganga Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Ghod Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Kanandi Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Koyna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Krishna Main)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Kukadi Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Meena Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Mose Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Mula Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Mutha Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Nira Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Pavana Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Sina Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Tarali Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Tulshi Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Urmodi Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Velvandi Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Venna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Krishna River Basin (Warna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Tapi River Basin (Girna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Tapi River Basin (Purna Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Tapi River Basin (Waghur Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('Tapi River Basin (Wan Sub-basin)') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('West Flowing / Surya Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('West Flowing / Tillari Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('West Flowing / Ulhas Basin') ON CONFLICT (basin_name) DO NOTHING;
INSERT INTO basins (basin_name) VALUES ('West Flowing / Vaitarna Basin') ON CONFLICT (basin_name) DO NOTHING;

INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('khadakwasla', 'Khadakwasla', 'खडकवासला', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Mutha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('panshet', 'Panshet', 'पानशेत', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Ambi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('varasgaon', 'Varasgaon', 'वरसगाव', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Mose Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('temghar', 'Temghar', 'टेमघर', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Mutha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('mulshi-tata', 'Mulshi', 'मुळशी', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 230.0, 522.76, 752.76)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('gunjawani', 'Gunjawani', 'गुंजवणी', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Kanandi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('pavana', 'Pavana', 'पवना', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Pavana Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('chaskaman', 'Chaskaman', 'चासकमान', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Bhima Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dimbhe', 'Dimbhe', 'डिंभे', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Ghod Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bhama-askhed', 'Bhama Askhed', 'भामा आसखेड', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Bhama Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('andra', 'Andra', 'आंद्रा', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MEDIUM', 2.0, 80.0, 82.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('pimpalgaon-joge', 'Pimpalgaon Joge', 'पिंपळगाव जोगे', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Arpa Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('manikdoh', 'Manikdoh', 'माणिकडोह', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Kukadi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('yedgaon', 'Yedgaon', 'येडगाव', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Kukadi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('wadaj', 'Wadaj', 'वडज', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Meena Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('ghod-chinchani', 'Ghod', 'घोड (चिंचणी)', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 61.5, 154.8, 216.3)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('visapur', 'Visapur', 'विसापूर', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MEDIUM', 1.0, 25.0, 26.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kalmodi', 'Kalmodi', 'कलमोडी', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MEDIUM', 0.1, 42.6, 42.7)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kasarsai', 'Kasarsai', 'कासारसाई', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MEDIUM', 0.5, 16.0, 16.5)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('nira-deoghar', 'Nira Deoghar', 'नीरा देवघर', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Nira Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bhatghar', 'Bhatghar', 'भाटघर', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Velvandi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('nazare', 'Nazare', 'नाझरे', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MEDIUM', 1.0, 22.3, 23.3)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('lonavala-tata', 'Lonavala Tata', 'लोणावळा टाटा', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 0.06, 11.72, 11.78)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('walwhan-tata', 'Walwhan Tata', 'वळवण टाटा', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 0.28, 71.84, 72.12)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('shirawta-tata', 'Shirawta Tata', 'शिरवटा टाटा', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 0.87, 197.28, 198.15)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kundali-tata', 'Kundali Tata', 'कडली टाटा', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 0.8, 6.34, 7.14)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('thokerwadi-tata', 'Thokerwadi Tata', 'ठोकरवाडी टाटा', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 11.06, 352.64, 363.7)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('ujani', 'Ujani', 'भीमा (उजनी)', (SELECT district_id FROM districts WHERE district_name='Solapur'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Bhima Main)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('koyna', 'Koyna', 'कोयना', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Koyna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dhom', 'Dhom', 'धोम', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Krishna Main)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dhom-balkawadi', 'Dhom Balkawadi', 'धोम बलकवडी', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kanher', 'Kanher', 'कण्हेर', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Venna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('urmodi', 'Urmodi', 'उरमोडी', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Urmodi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('tarali', 'Tarali', 'तारळी', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Tarali Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('veer', 'Veer', 'वीर', (SELECT district_id FROM districts WHERE district_name='Satara'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Nira Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('radhanagari', 'Radhanagari', 'राधानगरी', (SELECT district_id FROM districts WHERE district_name='Kolhapur'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Bhogawati Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dudhganga', 'Dudhganga', 'दूधगंगा', (SELECT district_id FROM districts WHERE district_name='Kolhapur'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Dudhganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('tulshi', 'Tulshi', 'तुळशी', (SELECT district_id FROM districts WHERE district_name='Kolhapur'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Tulshi Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('warna', 'Warna', 'वारणा', (SELECT district_id FROM districts WHERE district_name='Sangli'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Warna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bhatsa', 'Bhatsa', 'भातसा', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Ulhas Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('tansa', 'Tansa', 'तानसा', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Vaitarna Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('modak-sagar', 'Modak Sagar', 'मोडकसागर', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Vaitarna Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('middle-vaitarna', 'Middle Vaitarna', 'मध्य वैतरणा', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Vaitarna Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('barvi', 'Barvi', 'बारवी', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Ulhas Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('lower-chondhe', 'Lower Chondhe', 'निम्न चोंढे', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing Rivers (Konkan)'), 'MAJOR', 0.48, 2.73, 3.21)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('upper-ghatghar', 'Upper Ghatghar', 'ऊर्ध्व घाटघर', (SELECT district_id FROM districts WHERE district_name='Thane'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing Rivers (Konkan)'), 'MAJOR', 0.68, 5.14, 5.82)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dhamni', 'Dhamni', 'धामणी', (SELECT district_id FROM districts WHERE district_name='Palghar'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Surya Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kawdas-weir', 'Kawdas P. U. Weir', 'कवडास पिकअप बंधारा', (SELECT district_id FROM districts WHERE district_name='Palghar'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing Rivers (Konkan)'), 'MAJOR', 3.74, 9.96, 13.7)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dolwahal-weir', 'Dolwahal weir', 'डोलवाहाल पिकअप बंधारा', (SELECT district_id FROM districts WHERE district_name='Raigad'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing Rivers (Konkan)'), 'MAJOR', 8.23, 6.5, 14.74)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('tillari', 'Tillari', 'तिल्लारी', (SELECT district_id FROM districts WHERE district_name='Sindhudurg'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing Rivers (Konkan)'), 'MAJOR', 14.8, 447.37, 462.17)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bhandardara', 'Bhandardara', 'भंडारदरा', (SELECT district_id FROM districts WHERE district_name='Ahmednagar'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Pravara Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('mula', 'Mula', 'मुळा', (SELECT district_id FROM districts WHERE district_name='Ahmednagar'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Mula Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('nilwande-2', 'Nilwande-2', 'निळवंडे-2', (SELECT district_id FROM districts WHERE district_name='Ahmednagar'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Pravara Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('upper-tapi-hatnur', 'Upper Tapi Hatnur', 'ऊर्ध्व तापी हतनूर', (SELECT district_id FROM districts WHERE district_name='Jalgaon'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('waghur', 'Waghur', 'वाघूर', (SELECT district_id FROM districts WHERE district_name='Jalgaon'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin (Waghur Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('arjunsagar', 'Arjunsagar', 'अर्जुनसागर', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 2.76, 36.99, 39.75)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bham-dam', 'Bham Dam', 'भाम धरण', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bhavali', 'Bhavali', 'भावली', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Bham Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('chankapur', 'Chankapur', 'चणकापूर', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin (Girna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('darna', 'Darna', 'दारणा', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Darna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('gangapur', 'Gangapur', 'गंगापूर', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Godavari Main)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('girna', 'Girna', 'गिरणा', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin (Girna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kadwa', 'Kadwa', 'कडवा', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Kadwa Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('karanjwan', 'Karanjwan', 'करंजवण', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Kadva Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('mukane', 'Mukane', 'मुकणे', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Aundha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('ozarkhed', 'Ozarkhed', 'ओझरखेड', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Unanda Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('palkhed', 'Palkhed', 'पालखेड', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Kadwa Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('punegaon', 'Punegaon', 'पुणेगाव', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Unanda Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('tisgaon', 'Tisgaon', 'तिसगाव', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('upper-vaitarna', 'Upper Vaitarna', 'वैतरणा ज. वि. प्रकल्प', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Vaitarna Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('waghad', 'Waghad', 'वाघाड', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Kolvan Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('waki-dam', 'Waki Dam', 'वाकी धरण', (SELECT district_id FROM districts WHERE district_name='Nashik'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('jayakwadi-paithan', 'Paithan (Jayakwadi)', 'जयकवाडी (पैठण)', (SELECT district_id FROM districts WHERE district_name='Chhatrapati Sambhajinagar'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 738.11, 2170.93, 2909.04)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('apegaon-hlb', 'Apegaon H L B', 'आपेगाव उ स्त.बं.', (SELECT district_id FROM districts WHERE district_name='Chhatrapati Sambhajinagar'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('majalgaon', 'Majalgaon', 'माजलगाव', (SELECT district_id FROM districts WHERE district_name='Beed'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Sindphana Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('manjara', 'Manjara', 'मांजरा', (SELECT district_id FROM districts WHERE district_name='Beed'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Manjara Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dhanegaon-hlb', 'Dhanegaon High Level Barrage', 'धनेगाव उच्च पातळी बंधारा', (SELECT district_id FROM districts WHERE district_name='Beed'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.34, 10.98, 11.32)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dongargaon-hlb', 'Dongargaon H L B', 'डोंगरगाव उच्च पातळी बंधारा', (SELECT district_id FROM districts WHERE district_name='Beed'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.01, 7.89, 7.9)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('siddheshwar', 'Siddheshwar', 'सिध्देश्वर', (SELECT district_id FROM districts WHERE district_name='Hingoli'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Purna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('yeldari', 'Yeldari', 'येलदरी', (SELECT district_id FROM districts WHERE district_name='Hingoli'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Purna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('amdura', 'Amdura', 'अमदुरा', (SELECT district_id FROM districts WHERE district_name='Nanded'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dhalegaon-hlb', 'Dhalegaon H L B', 'ढालेगाव उच्च पातळी बंधारा', (SELECT district_id FROM districts WHERE district_name='Nanded'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 1.37, 13.5, 14.87)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('lower-manar', 'Lower Manar', 'निम्न मनार', (SELECT district_id FROM districts WHERE district_name='Nanded'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Manar Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('vishnupuri', 'Vishnupuri', 'विष्णुपुरी', (SELECT district_id FROM districts WHERE district_name='Nanded'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('lower-terna', 'Lower Terna', 'निम्न तेरणा', (SELECT district_id FROM districts WHERE district_name='Dharashiv'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Terna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('sina-kolegaon', 'Sina kolegaon', 'सिना कोळेगाव', (SELECT district_id FROM districts WHERE district_name='Dharashiv'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Sina Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('lower-dudhana', 'Lower Dudhana', 'निम्न दुधना', (SELECT district_id FROM districts WHERE district_name='Parbhani'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Dudhana Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('upper-wardha', 'Upper Wardha', 'ऊर्ध्व वर्धा', (SELECT district_id FROM districts WHERE district_name='Amravati'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wardha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('arunavati', 'Arunavati', 'अरुणावती', (SELECT district_id FROM districts WHERE district_name='Yavatmal'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Penganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bembla', 'Bembla', 'बेंबळा', (SELECT district_id FROM districts WHERE district_name='Yavatmal'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wardha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('isapur', 'Isapur', 'इसापूर', (SELECT district_id FROM districts WHERE district_name='Yavatmal'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Penganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('pus', 'Pus', 'पूस', (SELECT district_id FROM districts WHERE district_name='Yavatmal'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Penganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('wan', 'Wan', 'वान', (SELECT district_id FROM districts WHERE district_name='Akola'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin (Wan Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('katepurna', 'Katepurna', 'काटेपूर्णा', (SELECT district_id FROM districts WHERE district_name='Akola'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin (Purna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('khadakpurna', 'Khadakpurna', 'खडकपूर्णा', (SELECT district_id FROM districts WHERE district_name='Buldhana'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Purna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('nalganga', 'Nalganga', 'नळगंगा', (SELECT district_id FROM districts WHERE district_name='Buldhana'), (SELECT basin_id FROM basins WHERE basin_name='Tapi River Basin (Purna Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('pentakli', 'Pentakli', 'पेनटाकळी', (SELECT district_id FROM districts WHERE district_name='Buldhana'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Penganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('totladoh', 'Totladoh', 'तोतलाडोह', (SELECT district_id FROM districts WHERE district_name='Nagpur'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Pench Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('gosikhurd', 'Gosikhurd', 'गोसीखुर्द', (SELECT district_id FROM districts WHERE district_name='Bhandara'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wainganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bawanthadi', 'Bawanthadi', 'बावनथडी', (SELECT district_id FROM districts WHERE district_name='Bhandara'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wainganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('asolamendha', 'Asolamendha', 'असोलामेंढा', (SELECT district_id FROM districts WHERE district_name='Chandrapur'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wainganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dina', 'Dina', 'दिना', (SELECT district_id FROM districts WHERE district_name='Gadchiroli'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Pranhita Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('dhapewada', 'Dhapewada', 'धापवाडा', (SELECT district_id FROM districts WHERE district_name='Gondia'), (SELECT basin_id FROM basins WHERE basin_name='Wainganga / Godavari Basin'), 'MAJOR', 0.0, 44.05, 44.05)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('itiadoh', 'Itiadoh', 'इटियाडोह', (SELECT district_id FROM districts WHERE district_name='Gondia'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wainganga Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kalisarar', 'Kalisarar', 'कालीसरार', (SELECT district_id FROM districts WHERE district_name='Gondia'), (SELECT basin_id FROM basins WHERE basin_name='Wainganga / Godavari Basin'), 'MAJOR', 2.47, 26.04, 28.52)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('pujaritola', 'Pujaritola P.U.Weir', 'पुजारीटोला', (SELECT district_id FROM districts WHERE district_name='Gondia'), (SELECT basin_id FROM basins WHERE basin_name='Wainganga / Godavari Basin'), 'MAJOR', 14.93, 43.53, 58.46)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('sirpur', 'Sirpur', 'सिरपूर', (SELECT district_id FROM districts WHERE district_name='Gondia'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Bagh Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('kamthi-khairy', 'Kamthi Khairy', 'कामठी खैरी', (SELECT district_id FROM districts WHERE district_name='Nagpur'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Pench Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('khindsi', 'Khindsi', 'खिंडसी', (SELECT district_id FROM districts WHERE district_name='Nagpur'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Sur Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('nand', 'Nand', 'नांद', (SELECT district_id FROM districts WHERE district_name='Nagpur'), (SELECT basin_id FROM basins WHERE basin_name='Wainganga / Godavari Basin'), 'MAJOR', 9.0, 53.18, 62.18)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('wadgaon', 'Wadgaon', 'वडगाव', (SELECT district_id FROM districts WHERE district_name='Nagpur'), (SELECT basin_id FROM basins WHERE basin_name='Wainganga / Godavari Basin'), 'MAJOR', 16.6, 134.9, 151.5)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('bor', 'Bor', 'बोर', (SELECT district_id FROM districts WHERE district_name='Wardha'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wardha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('lower-wardha', 'Lower Wardha', 'निम्न वर्धा', (SELECT district_id FROM districts WHERE district_name='Wardha'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Wardha Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('mulshi', 'Mulshi', 'मुळशी', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Mula Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('ghod', 'Ghod', 'घोड (चिंचणी)', (SELECT district_id FROM districts WHERE district_name='Pune'), (SELECT basin_id FROM basins WHERE basin_name='Krishna River Basin (Ghod Sub-basin)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('jayakwadi', 'Jayakwadi (Paithan)', 'पैठण (जायकवाडी)', (SELECT district_id FROM districts WHERE district_name='Chhatrapati Sambhajinagar'), (SELECT basin_id FROM basins WHERE basin_name='Godavari River Basin (Godavari Main)'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;
INSERT INTO dams (dam_slug, dam_name_en, dam_name_mr, district_id, basin_id, project_type, dead_storage_mcm, design_live_mcm, design_gross_mcm)
VALUES ('tillari-kokan', 'Tillari', 'तिल्लारी', (SELECT district_id FROM districts WHERE district_name='Sindhudurg'), (SELECT basin_id FROM basins WHERE basin_name='West Flowing / Tillari Basin'), 'MAJOR', 0.0, 100.0, 100.0)
ON CONFLICT (dam_slug) DO UPDATE SET dam_name_en=EXCLUDED.dam_name_en, dam_name_mr=EXCLUDED.dam_name_mr;

COMMIT;
