# Maharashtra Dam Water Storage Scraper & Automation Guide

## 1. Summary of Fixes

### Why the Previous Scraper Was Failing:
1. **Devanagari Font Ligature Corruption**: The old Marathi PDFs had custom embedded font ligatures (`\uE000`–`\uF8FF`), numeral concatenation (e.g., `1802.811517.20`), and inconsistent naming, leading to extraction crashes.
2. **GitHub Actions Repository Bloat / Timeouts**: The old workflow attempted to `git add dam_pdfs/` (over 900 MB of binary PDFs) and `web/dam_data.json` (36.5 MB), causing GitHub push limits and network timeouts.
3. **Missing English PDF URLs**: The script prioritized `Today's-Storage-ReportMarathi-*.pdf` which failed on 404s.

### What Was Done:
- **Clean English-Only Scraper Pipeline**: We switched 100% to the official English bulletin (`Today's-Storage-ReportEng-{DD-MM-YYYY}.pdf`). All Marathi translation hacks, font ligature cleanups, and Devanagari digit translations have been removed from the extraction logic.
- **English Storage with Bilingual Display**: Data is parsed and stored cleanly in English in SQLite (`pune_dams.db`), while the frontend displays both English and authentic Devanagari Marathi names (e.g. `Khadakwasla (खडकवासला)`).
- **All 782 English Bulletins Downloaded & Ingested**: All dates from `01-01-2024` to `12-11-2026` are downloaded and verified in `dam_pdf/`. 130,154 clean records across all 139 dams are ingested into SQLite.
- **Removed 36.5MB Obsolete Dump**: Deleted `web/dam_data.json` and added `dam_pdf/` to `.gitignore`. Decoupled JSON files (`latest.json`, `dates.json`, `history/*.json`) are now under ~75 KB total.

---

## 2. Running the Scraper Manually

### Fetch recent days & update database:
```bash
# Update last 3 days (fast, takes ~5 seconds)
python3 scraper/daily_dam_worker.py --once --days 3

# Full backfill of all available PDFs
python3 scraper/fetch_dam_data.py 1000
```

### Inspect database health & stats:
```bash
python3 database/db_manager.py --inspect
```

---

## 3. Automation Methods

### Method 1: GitHub Actions (Recommended if using GitHub)
The workflow file [`.github/workflows/daily_dam_scraper.yml`](file:///.github/workflows/daily_dam_scraper.yml) is already configured:
- **Schedule**: Runs automatically twice daily at **09:00 AM IST** (03:30 UTC) and **03:00 PM IST** (09:30 UTC).
- **Lightweight Git Push**: It only commits the web JSON files (`web/data/latest.json`, `dates.json`, `history/*.json`) and the SQLite database. It ignores the large PDF binaries.
- **Manual Trigger**: Can also be triggered anytime via GitHub UI: **Actions** → **Daily Maharashtra Dam Storage Tracker** → **Run workflow**.

---

### Method 2: Linux Crontab (Simplest Local / VPS Automation)
If GitHub Actions is not desired or your repository is private with limited Action minutes, set up a local cron job:

1. Open crontab editor:
```bash
crontab -e
```
2. Add this line to run daily at 09:00 AM IST:
```cron
0 9 * * * cd /home/parth/SY/DBMS/CP && /usr/bin/python3 scraper/daily_dam_worker.py --once --days 3 >> /tmp/dam_scraper.log 2>&1
```

---

### Method 3: Systemd Timer (Robust Linux Service)
For dedicated Linux servers or VPS, use the bundled systemd unit and timer:

1. Copy service and timer files to systemd directory:
```bash
sudo cp systemd/dam_scraper.service /etc/systemd/system/
sudo cp systemd/dam_scraper.timer /etc/systemd/system/
```
2. Enable and start the timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dam_scraper.timer
```
3. Check timer status:
```bash
systemctl list-timers | grep dam_scraper
```

---

### Method 4: Free Cloud Serverless Worker (Render / Fly.io / Modal)
If you prefer not keeping your laptop running:
- **Render Cron Job (Free Tier)**: Connect your GitHub repo, create a Cron Job pointing to `python3 scraper/daily_dam_worker.py --once`, with schedule `0 3,9 * * *`.
- **Modal / AWS Lambda**: Run `daily_dam_worker.py` as an ephemeral scheduled function pushing updated JSON to GitHub or an S3/Cloudflare R2 bucket.
