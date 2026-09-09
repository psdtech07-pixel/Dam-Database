-- ============================================================================
-- PUNE WATER RESOURCES RESERVOIR MONITORING SYSTEM (3NF RELATIONAL SCHEMA)
-- Compatible with SQLite3, MySQL, and PostgreSQL RDBMS Engines
-- ============================================================================

-- Enable Foreign Key Support (SQLite requirement)
PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. MASTER TABLE: dams
-- Stores static metadata for each monitored dam reservoir.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dams (
    dam_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_code                VARCHAR(20) UNIQUE NOT NULL,
    dam_name                VARCHAR(100) UNIQUE NOT NULL,
    river_name              VARCHAR(100) NOT NULL,
    basin_name              VARCHAR(100) DEFAULT 'Krishna River Basin',
    district                VARCHAR(100) DEFAULT 'Pune',
    state                   VARCHAR(100) DEFAULT 'Maharashtra',
    dead_storage_mcm        DECIMAL(10,2) NOT NULL CHECK (dead_storage_mcm >= 0),
    design_live_mcm         DECIMAL(10,2) NOT NULL CHECK (design_live_mcm > 0),
    design_gross_mcm        DECIMAL(10,2) NOT NULL CHECK (design_gross_mcm > 0),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. TRANSACTION LOG TABLE: daily_dam_storage_logs
-- Stores daily time-series water storage metrics for each dam.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_dam_storage_logs (
    log_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_id                  INTEGER NOT NULL,
    report_date             DATE NOT NULL,
    report_time             VARCHAR(20) DEFAULT '08:00 AM',
    current_live_mcm        DECIMAL(10,2) NOT NULL CHECK (current_live_mcm >= 0),
    current_gross_mcm       DECIMAL(10,2) NOT NULL CHECK (current_gross_mcm >= 0),
    current_live_pct        DECIMAL(5,2) NOT NULL CHECK (current_live_pct BETWEEN 0 AND 105),
    same_date_last_year_pct DECIMAL(5,2) CHECK (same_date_last_year_pct BETWEEN 0 AND 105),
    data_source             VARCHAR(50) DEFAULT 'WRD_PDF_SCRAPER',
    status_code             VARCHAR(50) DEFAULT 'SUCCESS',
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (dam_id) REFERENCES dams(dam_id) ON DELETE CASCADE,
    CONSTRAINT uq_dam_date UNIQUE (dam_id, report_date)
);

-- ----------------------------------------------------------------------------
-- 3. AUDIT TRAIL TABLE: system_audit_logs
-- Tracks data ingestion, scraping jobs, and maintenance tasks.
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
CREATE INDEX IF NOT EXISTS idx_logs_dam_date ON daily_dam_storage_logs(dam_id, report_date);
CREATE INDEX IF NOT EXISTS idx_logs_date ON daily_dam_storage_logs(report_date);
CREATE INDEX IF NOT EXISTS idx_logs_status ON daily_dam_storage_logs(status_code);

-- ----------------------------------------------------------------------------
-- 4. RELATIONAL VIEW: vw_dam_daily_analytics
-- Joins dams and daily_dam_storage_logs with calculated metrics.
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_dam_daily_analytics AS
SELECT 
    d.dam_id,
    d.dam_code,
    d.dam_name,
    d.river_name,
    d.district,
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
JOIN daily_dam_storage_logs l ON d.dam_id = l.dam_id;

-- ----------------------------------------------------------------------------
-- MASTER SEED DATA: dams
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO dams (dam_code, dam_name, river_name, dead_storage_mcm, design_live_mcm, design_gross_mcm) VALUES
('KHD', 'Khadakwasla', 'Mutha River',  30.00,  55.91,  85.91),
('PNS', 'Panshet',     'Ambi River',   9.00, 301.61, 310.61),
('MUL', 'Mulshi',      'Mula River', 230.00, 522.76, 752.76),
('GNJ', 'Gunjawani',   'Kanandi River', 0.21, 104.48, 104.69),
('TMG', 'Temghar',     'Mutha River',   2.95, 105.01, 107.96);

