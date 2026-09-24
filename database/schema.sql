-- ============================================================================
-- MAHARASHTRA STATE WATER RESOURCES MONITORING SYSTEM (3NF RELATIONAL SCHEMA)
-- Compatible with SQLite3, MySQL, and PostgreSQL RDBMS Engines
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. MASTER TABLE: divisions (6 Revenue Divisions of Maharashtra)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS divisions (
    division_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    division_code           VARCHAR(10) UNIQUE NOT NULL,
    division_name           VARCHAR(100) UNIQUE NOT NULL,
    division_name_mr        VARCHAR(100),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. MASTER TABLE: districts (Districts of Maharashtra)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS districts (
    district_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    division_id             INTEGER NOT NULL,
    district_name           VARCHAR(100) UNIQUE NOT NULL,
    district_name_mr        VARCHAR(100),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (division_id) REFERENCES divisions(division_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. MASTER TABLE: river_basins (Major River Basins)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS river_basins (
    basin_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    basin_name              VARCHAR(100) UNIQUE NOT NULL,
    basin_name_mr           VARCHAR(100),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. MASTER TABLE: dams (Master Table for All State Dams)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dams (
    dam_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_code                VARCHAR(50) UNIQUE NOT NULL,
    dam_name                VARCHAR(100) NOT NULL,
    dam_name_mr             VARCHAR(100),
    district_id             INTEGER NOT NULL,
    basin_id                INTEGER NOT NULL,
    river_name              VARCHAR(100) DEFAULT 'Main River',
    project_type            VARCHAR(20) DEFAULT 'MAJOR' CHECK (project_type IN ('MAJOR', 'MEDIUM', 'MINOR')),
    dead_storage_mcm        DECIMAL(10,2) NOT NULL CHECK (dead_storage_mcm >= 0),
    design_live_mcm         DECIMAL(10,2) NOT NULL CHECK (design_live_mcm > 0),
    design_gross_mcm        DECIMAL(10,2) NOT NULL CHECK (design_gross_mcm > 0),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (district_id) REFERENCES districts(district_id) ON DELETE CASCADE,
    FOREIGN KEY (basin_id) REFERENCES river_basins(basin_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5. TRANSACTION TABLE: daily_dam_storage_logs (Time-Series Storage Records)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_dam_storage_logs (
    log_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_id                  INTEGER NOT NULL,
    report_date             DATE NOT NULL,
    report_time             VARCHAR(20) DEFAULT '08:00 AM',
    current_live_mcm        DECIMAL(10,2) NOT NULL CHECK (current_live_mcm >= 0),
    current_gross_mcm       DECIMAL(10,2) NOT NULL CHECK (current_gross_mcm >= 0),
    current_live_pct        DECIMAL(5,2) NOT NULL CHECK (current_live_pct BETWEEN 0 AND 150),
    same_date_last_year_pct DECIMAL(5,2) CHECK (same_date_last_year_pct BETWEEN 0 AND 150),
    inflow_cusecs           DECIMAL(10,2) DEFAULT 0.00,
    outflow_cusecs          DECIMAL(10,2) DEFAULT 0.00,
    data_source             VARCHAR(50) DEFAULT 'WRD_STATE_PDF_SCRAPER',
    status_code             VARCHAR(50) DEFAULT 'SUCCESS',
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (dam_id) REFERENCES dams(dam_id) ON DELETE CASCADE,
    CONSTRAINT uq_dam_date UNIQUE (dam_id, report_date)
);

-- ----------------------------------------------------------------------------
-- 6. AUDIT TRAIL TABLE: system_audit_logs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_audit_logs (
    audit_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    action_name             VARCHAR(100) NOT NULL,
    records_affected        INTEGER DEFAULT 0,
    execution_status        VARCHAR(50) DEFAULT 'SUCCESS',
    log_message             TEXT,
    timestamp               DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- INDEXES FOR HIGH-PERFORMANCE QUERY OPTIMIZATION
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dams_district ON dams(district_id);
CREATE INDEX IF NOT EXISTS idx_dams_basin ON dams(basin_id);
CREATE INDEX IF NOT EXISTS idx_logs_dam_date ON daily_dam_storage_logs(dam_id, report_date);
CREATE INDEX IF NOT EXISTS idx_logs_date ON daily_dam_storage_logs(report_date);
CREATE INDEX IF NOT EXISTS idx_logs_status ON daily_dam_storage_logs(status_code);

-- ----------------------------------------------------------------------------
-- 7. RELATIONAL ANALYTICAL VIEW: vw_dam_daily_analytics
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_dam_daily_analytics AS
SELECT 
    d.dam_id,
    d.dam_code,
    d.dam_name,
    d.dam_name_mr,
    dt.district_name,
    dv.division_name,
    b.basin_name,
    d.project_type,
    l.report_date,
    l.report_time,
    d.dead_storage_mcm,
    d.design_live_mcm,
    d.design_gross_mcm,
    l.current_live_mcm,
    l.current_gross_mcm,
    l.current_live_pct,
    l.same_date_last_year_pct,
    ROUND(d.design_live_mcm - l.current_live_mcm, 2) AS remaining_capacity_mcm,
    ROUND(l.current_live_pct - COALESCE(l.same_date_last_year_pct, 0), 2) AS yoy_change_pct,
    l.status_code,
    l.data_source
FROM dams d
JOIN districts dt ON d.district_id = dt.district_id
JOIN divisions dv ON dt.division_id = dv.division_id
JOIN river_basins b ON d.basin_id = b.basin_id
JOIN daily_dam_storage_logs l ON d.dam_id = l.dam_id;

-- ----------------------------------------------------------------------------
-- MASTER SEED DATA: Divisions, Basins, Districts
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO divisions (division_code, division_name, division_name_mr) VALUES
('PUN', 'Pune', 'पुणे'),
('KOK', 'Kokan', 'कोकण'),
('NSK', 'Nashik', 'नाशिक'),
('AUR', 'Chhatrapati Sambhajinagar', 'छत्रपती संभाजीनगर'),
('AMR', 'Amravati', 'अमरावती'),
('NAG', 'Nagpur', 'नागपूर');

INSERT OR IGNORE INTO river_basins (basin_name, basin_name_mr) VALUES
('Krishna River Basin', 'कृष्णा खोरे'),
('Godavari River Basin', 'गोदावरी खोरे'),
('Tapi River Basin', 'तापी खोरे'),
('Narmada River Basin', 'नर्मदा खोरे'),
('West Flowing Rivers (Konkan)', 'पश्चिम वाहिनी नद्या');

INSERT OR IGNORE INTO districts (division_id, district_name, district_name_mr) VALUES
(1, 'Pune', 'पुणे'),
(1, 'Satara', 'सातारा'),
(1, 'Solapur', 'सोलापूर'),
(1, 'Sangli', 'सांगली'),
(1, 'Kolhapur', 'कोल्हापूर'),
(2, 'Thane', 'ठाणे'),
(2, 'Palghar', 'पालघर'),
(2, 'Raigad', 'रायगड'),
(2, 'Ratnagiri', 'रत्नागिरी'),
(2, 'Sindhudurg', 'सिंधुदुर्ग'),
(3, 'Nashik', 'नाशिक'),
(3, 'Ahmednagar', 'अहमदनगर'),
(3, 'Jalgaon', 'जळगाव'),
(3, 'Dhule', 'धुळे'),
(3, 'Nandurbar', 'नंदुरबार'),
(4, 'Chhatrapati Sambhajinagar', 'छत्रपती संभाजीनगर'),
(4, 'Jalna', 'जालना'),
(4, 'Beed', 'बीड'),
(4, 'Latur', 'लातूर'),
(4, 'Dharashiv', 'धाराशिव'),
(4, 'Nanded', 'नांदेड'),
(4, 'Parbhani', 'परभणी'),
(4, 'Hingoli', 'हिंगोली'),
(5, 'Amravati', 'अमरावती'),
(5, 'Akola', 'अकोला'),
(5, 'Buldhana', 'बुलढाणा'),
(5, 'Yavatmal', 'यवतमाळ'),
(5, 'Washim', 'वाशीम'),
(6, 'Nagpur', 'नागपूर'),
(6, 'Bhandara', 'भंडारा'),
(6, 'Gondia', 'गोंदिया'),
(6, 'Chandrapur', 'चंद्रपूर'),
(6, 'Gadchiroli', 'गडचिरोली'),
(6, 'Wardha', 'वर्धा');

-- Seed Pune Default Dams
INSERT OR IGNORE INTO dams (dam_code, dam_name, dam_name_mr, district_id, basin_id, river_name, dead_storage_mcm, design_live_mcm, design_gross_mcm) VALUES
('KHD', 'Khadakwasla', 'खडकवासला', 1, 1, 'Mutha River',  30.00,  55.91,  85.91),
('PNS', 'Panshet',     'पानशेत',     1, 1, 'Ambi River',   9.00, 301.61, 310.61),
('MUL', 'Mulshi',      'मुळशी',      1, 1, 'Mula River', 230.00, 522.76, 752.76),
('GNJ', 'Gunjawani',   'गुंजवणी',    1, 1, 'Kanandi River', 0.21, 104.48, 104.69),
('TMG', 'Temghar',     'टेमघर',      1, 1, 'Mutha River',   2.95, 105.01, 107.96);
