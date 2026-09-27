-- ============================================================================
-- MAHARASHTRA STATE WATER RESOURCES MONITORING SYSTEM (3NF RELATIONAL SCHEMA)
-- SQLite Engine Schema
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Administrative Divisions (6 Revenue Divisions of Maharashtra)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS divisions (
    division_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    division_name       TEXT NOT NULL UNIQUE
);

-- ----------------------------------------------------------------------------
-- 2. Administrative Districts
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS districts (
    district_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name       TEXT NOT NULL UNIQUE,
    division_id         INTEGER NOT NULL,
    FOREIGN KEY (division_id) REFERENCES divisions(division_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 3. Hydrological River Basins
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS basins (
    basin_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    basin_name          TEXT NOT NULL UNIQUE
);

-- ----------------------------------------------------------------------------
-- 4. Static Dam Metadata Entities
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dams (
    dam_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_slug                TEXT NOT NULL UNIQUE,
    dam_name_en             TEXT NOT NULL,
    dam_name_mr             TEXT,
    district_id             INTEGER NOT NULL,
    basin_id                INTEGER NOT NULL,
    project_type            TEXT NOT NULL CHECK(project_type IN ('MAJOR', 'MEDIUM', 'MINOR')),
    dead_storage_mcm        REAL NOT NULL DEFAULT 0.0 CHECK(dead_storage_mcm >= 0),
    design_live_mcm         REAL NOT NULL CHECK(design_live_mcm > 0),
    design_gross_mcm        REAL NOT NULL CHECK(design_gross_mcm >= design_live_mcm),
    full_reservoir_level_m  REAL,
    latitude                REAL,
    longitude               REAL,
    FOREIGN KEY (district_id) REFERENCES districts(district_id),
    FOREIGN KEY (basin_id) REFERENCES basins(basin_id)
);

-- ----------------------------------------------------------------------------
-- 5. Dynamic Time-Series Telemetry Fact Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dam_daily_logs (
    log_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_id                  INTEGER NOT NULL,
    reading_date            DATE NOT NULL,          -- ISO 8601 Format 'YYYY-MM-DD'
    reading_time            TEXT,
    live_storage_mcm        REAL NOT NULL CHECK(live_storage_mcm >= 0),
    gross_storage_mcm       REAL NOT NULL CHECK(gross_storage_mcm >= live_storage_mcm),
    storage_pct             REAL NOT NULL CHECK(storage_pct >= 0 AND storage_pct <= 120.0),
    last_year_pct           REAL CHECK(last_year_pct IS NULL OR (last_year_pct >= 0 AND last_year_pct <= 120.0)),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dam_id) REFERENCES dams(dam_id) ON DELETE CASCADE,
    CONSTRAINT unique_dam_daily_log UNIQUE (dam_id, reading_date)
);

-- ----------------------------------------------------------------------------
-- High-Performance Query Indexing
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_logs_dam_date ON dam_daily_logs(dam_id, reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_logs_date ON dam_daily_logs(reading_date);
CREATE INDEX IF NOT EXISTS idx_dams_district ON dams(district_id);
CREATE INDEX IF NOT EXISTS idx_dams_basin ON dams(basin_id);

-- ----------------------------------------------------------------------------
-- Analytical View: Daily Storage Analytics View
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_dam_daily_analytics AS
SELECT 
    d.dam_id,
    d.dam_slug,
    d.dam_name_en,
    d.dam_name_mr,
    dt.district_name,
    dv.division_name,
    b.basin_name,
    d.project_type,
    l.reading_date,
    l.reading_time,
    d.dead_storage_mcm,
    d.design_live_mcm,
    d.design_gross_mcm,
    l.live_storage_mcm,
    l.gross_storage_mcm,
    l.storage_pct,
    l.last_year_pct,
    ROUND(d.design_live_mcm - l.live_storage_mcm, 2) AS remaining_capacity_mcm,
    ROUND(l.storage_pct - COALESCE(l.last_year_pct, 0), 2) AS yoy_change_pct
FROM dams d
JOIN districts dt ON d.district_id = dt.district_id
JOIN divisions dv ON dt.division_id = dv.division_id
JOIN basins b ON d.basin_id = b.basin_id
JOIN dam_daily_logs l ON d.dam_id = l.dam_id;
