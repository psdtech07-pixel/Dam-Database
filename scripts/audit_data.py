#!/usr/bin/env python3
"""Data-quality audit for the dam DB. Exit code 1 if any HARD check fails.
Usage: python scripts/audit_data.py [path/to/db]   (default: database/pune_dams.db)
Run it BEFORE and AFTER every phase and paste the output into the PR/commit message."""
import sqlite3, sys, datetime as dt
from pathlib import Path

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "database" / "pune_dams.db"
c = sqlite3.connect(DB)
one = lambda sql, *a: c.execute(sql, a).fetchone()[0]

checks = []   # (name, value, ok, hard)
def check(name, value, ok, hard=True):
    checks.append((name, value, ok, hard))

n_dams  = one("SELECT COUNT(*) FROM dams")
n_logs  = one("SELECT COUNT(*) FROM dam_daily_logs")
first, last = c.execute("SELECT MIN(reading_date), MAX(reading_date) FROM dam_daily_logs").fetchone()
check("dams", n_dams, n_dams >= 135, False)
check("log rows", n_logs, n_logs > 0, False)

# 1. placeholder live storage (registry default leaking into facts)
v = one("""SELECT COUNT(*) FROM dam_daily_logs l JOIN dams d USING(dam_id)
           WHERE l.live_storage_mcm = 100.0 AND d.design_live_mcm <> 100.0""")
check("rows with live_storage_mcm == 100.0 placeholder   (baseline 3241)", v, v == 0)

# 2. stored % must agree with live/design
v = one("""SELECT COUNT(*) FROM dam_daily_logs l JOIN dams d USING(dam_id)
           WHERE ABS(l.storage_pct - 100.0*l.live_storage_mcm/d.design_live_mcm) > 2""")
check("rows where pct disagrees with live/design >2pp    (baseline 6407)", v, v == 0)

# 3. NULL stored as 0 for last-year
v = one("SELECT COUNT(*) FROM dam_daily_logs WHERE last_year_pct = 0")
check("rows with last_year_pct == 0 (should be NULL)     (baseline 5336)", v, v == 0)

# 4. clamped-to-capacity rows
v = one("""SELECT COUNT(*) FROM dam_daily_logs l JOIN dams d USING(dam_id)
           WHERE l.live_storage_mcm = d.design_live_mcm""")
check("rows with live == design exactly (clamp suspects) (baseline 11655)", v, v < 2000, False)

# 5. fabricated metadata
v = one("SELECT COUNT(*) FROM dams WHERE height_m = 45.0 AND length_m = 1200.0")
check("dams with placeholder 45 m / 1200 m               (baseline 87)", v, v == 0)
v = one("SELECT COUNT(*) FROM dams WHERE completion_year = 1985 AND height_m = 45.0")
check("dams with placeholder year 1985                   (baseline ~87)", v, v == 0)

# 6. coverage
days = [dt.date.fromisoformat(r[0]) for r in c.execute("SELECT DISTINCT reading_date FROM dam_daily_logs ORDER BY 1")]
gaps = [(a, b) for a, b in zip(days, days[1:]) if (b - a).days > 1]
check("calendar gaps between first and last day          (baseline 1: 2026-11-07)", len(gaps), len(gaps) == 0, False)
v = one("SELECT COUNT(*) FROM (SELECT reading_date FROM dam_daily_logs GROUP BY 1 HAVING COUNT(*) < 135)")
check("days reporting <135 dams                          (baseline 264)", v, v == 0, False)
v = one("""SELECT COUNT(*) FROM dams WHERE dam_id NOT IN
           (SELECT dam_id FROM dam_daily_logs WHERE reading_date = (SELECT MAX(reading_date) FROM dam_daily_logs))""")
check("dams missing on the latest day                    (baseline 1: tillari)", v, v == 0)

# 7. duplicates / schema drift
v = one("""SELECT COUNT(*) FROM (SELECT design_live_mcm, design_gross_mcm FROM dams
           GROUP BY 1,2 HAVING COUNT(*) > 1)""")
check("capacity-identical dam pairs (possible duplicates)(baseline 2)", v, v == 0, False)
legacy = [r[0] for r in c.execute("""SELECT name FROM sqlite_master WHERE type='table'
          AND name IN ('river_basins','daily_dam_storage_logs','system_audit_logs')""")]
check("legacy tables present                             (baseline 3)", len(legacy), len(legacy) == 0, False)

# 8. freshness / future dates
today = dt.date.today().isoformat()
v = one("SELECT COUNT(*) FROM dam_daily_logs WHERE reading_date > ?", today)
check("rows dated in the future", v, v == 0)
age = (dt.date.today() - dt.date.fromisoformat(last)).days if last else 999
check(f"latest reading is {last} (age in days)", age, age <= 2)

print(f"DB: {DB}\n{n_dams} dams, {n_logs:,} rows, {first} -> {last}\n")
bad = 0
for name, value, ok, hard in checks:
    tag = "PASS" if ok else ("FAIL" if hard else "WARN")
    bad += (not ok and hard)
    print(f"[{tag}] {name}: {value}")
print(f"\n{'HARD FAILURES: ' + str(bad) if bad else 'No hard failures.'}")
sys.exit(1 if bad else 0)
