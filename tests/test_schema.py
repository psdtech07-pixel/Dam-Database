import sqlite3
import pytest
from datetime import date

def test_schema_constraints():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    # Setup core tables with STRICT mode
    conn.executescript("""
        CREATE TABLE divisions (division_id INTEGER PRIMARY KEY, division_name TEXT NOT NULL UNIQUE) STRICT;
        CREATE TABLE districts (district_id INTEGER PRIMARY KEY, district_name TEXT NOT NULL UNIQUE,
                                division_id INTEGER NOT NULL REFERENCES divisions(division_id)) STRICT;
        CREATE TABLE basins (basin_id INTEGER PRIMARY KEY, basin_name TEXT NOT NULL UNIQUE) STRICT;
        CREATE TABLE dams (
            dam_id INTEGER PRIMARY KEY,
            dam_slug TEXT NOT NULL UNIQUE,
            dam_name_en TEXT NOT NULL,
            district_id INTEGER NOT NULL REFERENCES districts(district_id),
            basin_id INTEGER NOT NULL REFERENCES basins(basin_id),
            design_live_mcm REAL NOT NULL CHECK (design_live_mcm > 0),
            dead_storage_mcm REAL DEFAULT 0.0 CHECK (dead_storage_mcm >= 0)
        ) STRICT;

        CREATE TABLE dam_daily_logs (
            dam_id INTEGER NOT NULL REFERENCES dams(dam_id) ON DELETE CASCADE,
            reading_date TEXT NOT NULL CHECK (reading_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
            live_storage_mcm REAL NOT NULL CHECK (live_storage_mcm >= 0),
            PRIMARY KEY (dam_id, reading_date)
        ) STRICT, WITHOUT ROWID;

        CREATE VIEW vw_dam_daily AS
        SELECT l.dam_id, d.dam_slug, l.reading_date, l.live_storage_mcm,
               d.dead_storage_mcm + l.live_storage_mcm AS gross_storage_mcm,
               ROUND(100.0 * l.live_storage_mcm / d.design_live_mcm, 2) AS storage_pct
        FROM dam_daily_logs l
        JOIN dams d USING (dam_id);
    """)

    # Seed master data
    conn.execute("INSERT INTO divisions VALUES (1, 'Pune');")
    conn.execute("INSERT INTO districts VALUES (1, 'Pune', 1);")
    conn.execute("INSERT INTO basins VALUES (1, 'Krishna');")
    conn.execute("INSERT INTO dams (dam_id, dam_slug, dam_name_en, district_id, basin_id, design_live_mcm, dead_storage_mcm) VALUES (1, 'khadakwasla', 'Khadakwasla', 1, 1, 55.91, 1.0);")

    # Verify Foreign Key enforcement
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO dams (dam_id, dam_slug, dam_name_en, district_id, basin_id, design_live_mcm) VALUES (2, 'bad', 'Bad Dam', 999, 1, 10.0);")

    # Verify B01: Year 2027 log record succeeds (no 2026-12-31 upper bound constraint)
    conn.execute("INSERT INTO dam_daily_logs (dam_id, reading_date, live_storage_mcm) VALUES (1, '2027-01-05', 45.0);")
    row = conn.execute("SELECT gross_storage_mcm, storage_pct FROM vw_dam_daily WHERE reading_date = '2027-01-05';").fetchone()
    assert row is not None
    assert row[0] == 46.0  # 45.0 live + 1.0 dead
    assert row[1] == round(100.0 * 45.0 / 55.91, 2)
