# Maharashtra Dam Water Storage Analytics System 💧

An enterprise-grade **Database Management System (DBMS)** and real-time civic-tech web analytics platform monitoring **139 major dams and reservoirs** across all 6 administrative divisions of Maharashtra.

Live daily reports are sourced automatically from official **Maharashtra Water Resources Department (WRD)** bulletins and archived into a normalized relational database.

---

## 🏛️ System Architecture

```
├── database/                   # Relational DBMS Core (3NF Normalized Schema)
│   ├── pune_dams.db            # SQLite 3NF Database (130,154 records across 1,046 days)
│   ├── schema.sql              # SQL DDL & DML Schema (Tables, Views, Indexes, Foreign Keys)
│   ├── db_manager.py           # DBMS Engine, Transactional Upsert & Integrity Inspector
│   └── dam_registry.json       # Master metadata registry for 139 dams
│
├── scraper/                    # Ingestion Engine & Automated Workers
│   ├── fetch_dam_data.py       # English PDF parser with regex layout extraction
│   ├── daily_dam_worker.py    # Daily incremental worker (runs in ~7 seconds)
│   └── download_english_pdfs.py # Parallel batch downloader for historical bulletins
│
├── web/                        # Modern Civic-Tech Web Frontend
│   ├── index.html              # Main dashboard with SPA routing (#/dam/{slug})
│   ├── dam.html                # Standalone URL redirector (?slug=...)
│   ├── index.css               # Editorial CSS system with Light & Dark mode tokens
│   ├── app.js                  # Client-side routing, Chart.js graphs, Command Palette
│   ├── logo.svg                # Vector branding logo
│   ├── favicon.svg             # Standalone vector favicon
│   ├── favicon.ico             # Multi-resolution ICO (16x16, 32x32, 48x48, 64x64)
│   └── data/                   # Decoupled static data feeds for zero-latency loading
│       ├── latest.json         # Real-time metrics + full metadata for 139 dams
│       ├── dates.json          # Calendar index of 1,046 historical dates
│       └── history/*.json      # 139 decoupled time-series files (one per dam)
│
├── .github/workflows/          # CI/CD Automation
│   └── daily_dam_scraper.yml  # Scheduled GitHub Action running at 09:00 AM & 03:00 PM IST
│
├── systemd/                    # Linux Self-Hosted Service Alternative
│   ├── dam_scraper.service     # Systemd service unit definition
│   └── dam_scraper.timer       # Systemd timer unit for automated execution
│
├── scripts/                    # Maintenance & Enrichment Scripts
│   ├── enrich_dam_metadata.py  # Populates encyclopedic specs and photo URLs
│   └── generate_logo.py        # Vector & raster icon generator
│
├── run.sh                      # One-click launcher for web server & database inspect
└── README.md                   # Project documentation
```

---

## 📌 Key Features

### 1. 3NF Relational DBMS
- **Full 3rd Normal Form**: Master entities (`dams`, `divisions`, `districts`, `river_basins`), daily time-series logs (`dam_daily_logs`), and audit tracking.
- **Relational Analytics View (`vw_dam_daily_analytics`)**: Pre-computes remaining storage volume, percentage full, and year-over-year percentage point differences.
- **Comprehensive Historical Backfill**: **130,154 records** spanning **1,046 consecutive calendar days** (`2024-01-01` to `2026-11-12`).
- **Encyclopedic Metadata**: Schema includes river, basin, nearest city, taluka, completion year, height, length, dead storage, gross capacity, primary purpose, and high-resolution photo URLs.

### 2. High-Performance English PDF Scraper
- **Zero Translation Overhead**: Directly ingests official English bulletins (`Today's-Storage-ReportEng-DD-MM-YYYY.pdf`), eliminating Devanagari font ligature translation and regex corruption.
- **Sub-10-Second Incremental Execution**: `scraper/daily_dam_worker.py --once --days 3` audits missing dates, downloads PDFs, extracts 138+ tables, upserts to SQLite, and regenerates web JSON in **~7 seconds**.
- **Dual Automation Pipeline**:
  - **GitHub Actions**: Configured in `.github/workflows/daily_dam_scraper.yml` to run twice daily. Commits only static data assets without bloating Git with heavy PDF files.
  - **Linux Systemd Service / Crontab**: Standalone headless background automation with zero third-party dependencies (see [`SCRAPER_AND_AUTOMATION_GUIDE.md`](SCRAPER_AND_AUTOMATION_GUIDE.md)).

### 3. Clean Civic-Tech UI/UX (Inspired by Bombay7)
- **Minimalist Typography & Editorial Layout**: Clean typography (`Inter` and `Newsreader`), neutral border contrast, and color-coded status badges.
- **Dark Mode Support**: Persistent Light/Dark theme toggle with automatic system preference detection (`prefers-color-scheme`).
- **Circular Ring Progress Gauge**: Real-time storage percentage, status pill (`Healthy`, `Moderate`, `Low`, `Critical`), daily change delta (`↘ -0.15% since yesterday`), and volumes in **Million Litres (ML)**, **MCM**, and **TMC**.
- **2025 vs 2026 YoY Comparison**: Vertical two-bar comparative graph with dashed reference gridlines.
- **"What it means today" Advisory Callout**: Plain-language water assessment and 4-tier color bands legend:
  - 🔴 **Critical**: `< 10%`
  - 🟠 **Low**: `10–25%`
  - 🟡 **Moderate**: `25–50%`
  - 🟢 **Healthy**: `≥ 50%`

### 4. Dedicated Dam Detail Pages
- **Instant Client-Side Routing**: Clicking any reservoir card seamlessly navigates to `#/dam/{slug}` (e.g. `#/dam/khadakwasla` or `#/dam/panshet`).
- **Breadcrumb Navigation**: `Maharashtra dams by district / {District} / {Dam Name}`.
- **Primary Metric Card**: Stored vs. Capacity in ML/MCM/TMC, Today's % vs. Same-Date Last Year %, and YoY difference (`+20.78 pp Higher YoY`).
- **Encyclopedia & Specifications Grid**: Architectural dimensions, river basin, year completed, dead storage, gross storage, and purpose.
- **Interactive Historical Chart**: Dedicated Chart.js line graph with **30D**, **90D**, **1Y**, and **All** time range filters.
- **"Other Major Dams in {District}"**: Interactive pill block grid for exploring related reservoirs in the same administrative area.

### 5. Search & Command Palette Suite
- **Quick Search Command Palette (`Ctrl+K` / `⌘K`)**: Instant search modal accessible via the top navigation bar or keyboard shortcuts to find any reservoir by English name, Marathi name, district, or river.
- **Dynamic Table Search**: Table search input with an explicit **Search** button and live dropdown filters for River Basin, District, and Storage Status.

---

## 🚀 Quick Start

### 1. Inspect Database Health
Run the built-in DBMS inspection utility to verify schema normalization and recent data:
```bash
./run.sh --inspect
# or
python3 database/db_manager.py --inspect
```

### 2. Launch Local Web Dashboard
```bash
./run.sh 8000
# or
python3 -m http.server 8000 --directory web
```
Open **`http://localhost:8000`** in your browser.

Direct dam view links:
- `http://localhost:8000/#/dam/khadakwasla`
- `http://localhost:8000/#/dam/koyna`
- `http://localhost:8000/#/dam/bhima-ujjani`

### 3. Run Incremental Daily Update
```bash
python3 scraper/daily_dam_worker.py --once --days 3
```

---

## 📊 Hydrological Units Reference

| Unit | Expansion | Equivalent |
|---|---|---|
| **ML** | Million Litres | 10 Lakh Litres |
| **MCM** | Million Cubic Metres | 1,000 ML (100 Crore Litres) |
| **TMC** | Thousand Million Cubic Feet | 28.317 MCM (2,831.7 Crore Litres) |
| **1 MCM** | — | **0.035315 TMC** |

---

## 📜 Data Source & Attribution
Data is compiled from official daily dam water storage bulletins published by the **Water Resources Department (WRD), Government of Maharashtra**.
