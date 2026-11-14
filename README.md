# Maharashtra Dam Water Storage Analytics System 💧

[![Live Dashboard](https://img.shields.io/badge/Live_Dashboard-GitHub_Pages-0284c7?style=for-the-badge&logo=github&logoColor=white)](https://psdtech07-pixel.github.io/Dam-Database/web/index.html)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/psdtech07-pixel/Dam-Database)
[![Developer LinkedIn](https://img.shields.io/badge/LinkedIn-Parth_Debadwar-0077b5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/parth-debadwar-005205377)
[![Database](https://img.shields.io/badge/Database-SQLite_3NF-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](database/schema.sql)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](scraper/)

An open, database-driven **civic-tech and hydrological analytics platform** monitoring **138 major dams and reservoirs** across all 6 administrative divisions of Maharashtra.

The platform transforms daily unstructured PDF bulletins published by the **Water Resources Department (WRD), Government of Maharashtra** into a normalized relational database, maintaining a comprehensive historical archive and presenting interactive, accessible water analytics to the public.

---

## 🌐 Live Web Dashboard

Explore the live, interactive web dashboard hosted on GitHub Pages:  
👉 **[https://psdtech07-pixel.github.io/Dam-Database/web/index.html](https://psdtech07-pixel.github.io/Dam-Database/web/index.html)**

---

## 🏛️ Project Evolution & Academic Background

The **Maharashtra Dam Water Storage Analytics System** originated as an academic course project for the **Database Management System (DBMS)** curriculum during undergraduate studies in **Instrumentation and Control Engineering** at **Vishwakarma Institute of Technology (VIT), Pune** (Academic Period: 2025–2029).

### The Problem
Maharashtra possesses an extensive network of reservoirs critical for municipal drinking supplies, agricultural irrigation, and hydroelectric generation. The Water Resources Department (WRD) publishes official storage figures daily at 08:00 AM IST. However, these figures are distributed across isolated daily PDF bulletins. For everyday citizens, researchers, and students, comparing reservoirs across river basins, tracking multi-month depletion curves, or conducting historical analyses required tedious manual downloading and parsing of hundreds of individual documents.

### The Journey
- **Academic Idea**: Apply relational database concepts (normalization, integrity constraints, views, transactions) to real-world government water data rather than simulated classroom datasets.
- **Database Project**: Designed a normalized **Third Normal Form (3NF)** relational schema to store reservoir metadata and daily telemetry logs without data redundancy.
- **Automated Data Platform**: Developed automated Python ingestion scrapers and background schedulers to process daily morning bulletins, cleanse anomalies, and maintain an uninterrupted historical archive.
- **Public Dashboard**: Built a fast, responsive, zero-runtime-cost web dashboard on GitHub Pages, decoupling dynamic database queries into lightweight static JSON endpoints to ensure sub-50ms load times worldwide.

Developed by **Parth Sadanand Debadwar**, the platform has expanded far beyond its original classroom submission into an enduring, publicly accessible civic resource.

---

## 📊 Current Dataset & Scope

As verified in the current production database:

| Metric | Verified Value | Description |
|---|---|---|
| **Major Dams & Reservoirs** | **138** | State-monitored water storage assets across Maharashtra |
| **Administrative Divisions** | **6** | Pune, Konkan, Nashik, Chhatrapati Sambhajinagar, Amravati, Nagpur |
| **Administrative Districts** | **30+** | Multi-tier district hierarchy linking reservoirs to revenue authorities |
| **River Basins** | **5** | Krishna, Godavari, Tapi, Narmada, and West Flowing Rivers |
| **Historical Records** | **105,420** | Verified daily time-series observation rows in `dam_daily_logs` |
| **Archive Coverage** | **784 dates** | Official daily bulletin archives (**1 January 2024 – 14 November 2026**) |

---

## ⚙️ Data Pipeline & Architecture

The system operates an automated, five-stage continuous ingestion and publishing pipeline:

```
[WRD Portal 08:00 AM Bulletin]
            │
            ▼
┌─────────────────────────────────┐
│ 1. Automated Retrieval & Ingest │  fetch_dam_data.py / daily_dam_worker.py
│    - English PDF Downloads      │  (Direct English bulletins: Today's-Storage-ReportEng-DD-MM-YYYY.pdf)
└─────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ 2. Column-Aware PDF Parser v2   │  scraper/pdf_parser_v2.py
│    - Right-edge column slotting │  Hydrological validation layer, eliminates column shifts,
│    - Zero translation overhead  │  resolves dam aliases & sends anomalies to quarantine
└─────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ 3. Relational DBMS Engine (v2)  │  database/pune_dams.db (SQLite with STRICT mode)
│    - Referential Integrity (FK) │  ACID-compliant transactions, WITHOUT ROWID fact logs
│    - Ingest Runs & Quarantine   │  ingest_runs, ingest_quarantine, report_calendar tables
│    - vw_dam_daily View          │  Analytical View for dynamically calculated metrics
└─────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ 4. Decoupled Static JSON Feeds  │  database/db_manager.py
│    - web/data/latest.json       │  Snapshot of all 138 dams (~132 KB)
│    - web/data/dates.json        │  Chronological index of unique reporting dates
│    - web/data/meta.json         │  Dynamic platform metadata and coverage statistics
│    - web/data/history/*.json    │  Compact per-dam time-series shards (~5-10 KB each)
└─────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ 5. Public Web Dashboard (SPA)   │  GitHub Pages Edge CDN
│    - Sub-50ms instant loading   │  Zero server database costs, no connection pool limits
│    - Light/Dark mode, Chart.js  │  Command Palette (Ctrl+K), Dam Detail Views
└─────────────────────────────────┘
```

### Why Decoupled Static JSON?
Traditional web architectures query an active database server on every visitor page request. In an emergency (e.g. intense monsoon downpours or flood discharge alerts), thousands of concurrent citizens querying the database would exhaust server memory and connection pools, crashing the service.

By pre-rendering the database into compact, decoupled static JSON feeds (`latest.json` for immediate dashboard display, and lazy-loaded `history/{dam_slug}.json` only when opening a dam trend chart), the frontend runs entirely from static CDN edge nodes with **zero hosting bills, zero server maintenance, and sub-50ms latency**.

---

## 🗄️ Relational Database Schema (3NF)

The database schema (`database/schema.sql`) strictly adheres to **Third Normal Form (3NF)** principles to guarantee data integrity, eliminate update anomalies, and optimize storage efficiency.

```sql
PRAGMA foreign_keys = ON;

-- 1. Administrative Divisions (6 Revenue Divisions of Maharashtra)
CREATE TABLE divisions (
    division_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    division_name       TEXT NOT NULL UNIQUE
);

-- 2. Administrative Districts
CREATE TABLE districts (
    district_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name       TEXT NOT NULL UNIQUE,
    division_id         INTEGER NOT NULL,
    FOREIGN KEY (division_id) REFERENCES divisions(division_id) ON DELETE RESTRICT
);

-- 3. Hydrological River Basins
CREATE TABLE basins (
    basin_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    basin_name          TEXT NOT NULL UNIQUE
);

-- 4. Dam Master Metadata Entities
CREATE TABLE dams (
    dam_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_slug            TEXT NOT NULL UNIQUE,
    dam_name_en         TEXT NOT NULL,
    dam_name_mr         TEXT,
    district_id         INTEGER NOT NULL,
    basin_id            INTEGER NOT NULL,
    project_type        TEXT NOT NULL CHECK(project_type IN ('MAJOR', 'MEDIUM', 'MINOR')),
    dead_storage_mcm    REAL NOT NULL DEFAULT 0.0 CHECK(dead_storage_mcm >= 0),
    design_live_mcm     REAL NOT NULL CHECK(design_live_mcm > 0),
    design_gross_mcm    REAL NOT NULL CHECK(design_gross_mcm >= design_live_mcm),
    taluka              TEXT,
    nearest_city        TEXT,
    river               TEXT,
    completion_year     INTEGER,
    purpose             TEXT,
    description         TEXT,
    image_url           TEXT,
    wikipedia_url       TEXT,
    height_m            REAL,
    length_m            REAL,
    FOREIGN KEY (district_id) REFERENCES districts(district_id),
    FOREIGN KEY (basin_id) REFERENCES basins(basin_id)
);

-- 5. Dynamic Time-Series Telemetry Fact Table
CREATE TABLE dam_daily_logs (
    log_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dam_id              INTEGER NOT NULL,
    reading_date        DATE NOT NULL,          -- ISO 8601 'YYYY-MM-DD'
    reading_time        TEXT,
    live_storage_mcm    REAL NOT NULL CHECK(live_storage_mcm >= 0),
    gross_storage_mcm   REAL NOT NULL CHECK(gross_storage_mcm >= live_storage_mcm),
    storage_pct         REAL NOT NULL CHECK(storage_pct >= 0 AND storage_pct <= 120.0),
    last_year_pct       REAL CHECK(last_year_pct IS NULL OR (last_year_pct >= 0 AND last_year_pct <= 120.0)),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dam_id) REFERENCES dams(dam_id) ON DELETE CASCADE,
    CONSTRAINT unique_dam_daily_log UNIQUE (dam_id, reading_date)
);

-- High-Performance Query Indexing
CREATE INDEX idx_logs_dam_date ON dam_daily_logs(dam_id, reading_date DESC);
CREATE INDEX idx_logs_date     ON dam_daily_logs(reading_date);
CREATE INDEX idx_dams_district ON dams(district_id);
CREATE INDEX idx_dams_basin    ON dams(basin_id);

-- Pre-Computed Analytical View
CREATE VIEW vw_dam_daily_analytics AS
SELECT 
    d.dam_id, d.dam_slug, d.dam_name_en, d.dam_name_mr,
    dt.district_name, dv.division_name, b.basin_name,
    d.project_type, d.dead_storage_mcm, d.design_live_mcm, d.design_gross_mcm,
    l.reading_date, l.live_storage_mcm, l.gross_storage_mcm,
    l.storage_pct, l.last_year_pct,
    ROUND(d.design_live_mcm - l.live_storage_mcm, 2) AS remaining_capacity_mcm,
    ROUND(l.storage_pct - l.last_year_pct, 2) AS yoy_pct_diff
FROM dams d
JOIN districts dt ON d.district_id = dt.district_id
JOIN divisions dv ON dt.division_id = dv.division_id
JOIN basins b ON d.basin_id = b.basin_id
JOIN dam_daily_logs l ON d.dam_id = l.dam_id;
```

---

## ✨ Platform Features

1. **Circular Storage Progress Gauge**:
   - Displays real-time aggregate storage percentage for any selected division or all Maharashtra.
   - Status categorization: **Critical** (<10%), **Low** (10–25%), **Moderate** (25–50%), **Healthy** (≥50%).
   - Daily delta indicators showing changes compared with yesterday.
   - Volumes displayed simultaneously in **Million Litres (ML)**, **Million Cubic Metres (MCM)**, and **TMC**.

2. **Year-on-Year Comparative Graph**:
   - Compares current storage with the exact same calendar date from the prior year.

3. **Regional Division Filters**:
   - Instant filtering across **Pune**, **Konkan**, **Nashik**, **Chhatrapati Sambhajinagar**, **Amravati**, **Nagpur**, or **All Maharashtra**.

4. **Command Palette (`Ctrl + K` / `⌘K`) & Table Search**:
   - Keyboard-accessible instant search dialog matching reservoirs by English name, Marathi name, district, or river.
   - Multi-criteria tabular filters by river basin, district, and storage health tier.

5. **Dedicated Reservoir Pages (`#/dam/{slug}`)**:
   - Single-page application routing displaying comprehensive reservoir data:
     - Live stored water vs. designed live capacity in ML, MCM, and TMC.
     - Year-on-year percentage comparison.
     - Technical specifications (dam height, wall length, completion year, dead storage, river, basin).
     - Verified authentic reservoir photography.
     - Direct **"Learn more on Wikipedia ↗"** supplementary links.
     - Interactive time-series trends chart with **30D**, **90D**, **1Y**, and **All-Time** historical ranges.
     - Quick navigation pills to other major reservoirs in the same district.

6. **Light & Dark Theme**:
   - High-contrast accessible design tokens with persistent theme storage in `localStorage` and automatic OS preference detection.

7. **Streamlined About Page (`#/about`)**:
   - 7 curated sections detailing platform purpose, VIT Pune academic origin, audience breakdown, current dataset metrics, developer profile, more projects by the developer, and technical documentation links.

---

## 📁 Repository Structure

```
Dam-Database/
├── database/                    # Relational DBMS Core (3NF SQLite Schema)
│   ├── pune_dams.db             # Primary SQLite database (130,154 records, 1,046 days)
│   ├── schema.sql               # SQL DDL & DML specifications (tables, views, indexes)
│   ├── db_manager.py            # DBMS engine, transactional upserts & web JSON export
│   └── dam_registry.json        # Master reservoir registry with metadata & Wikipedia URLs
│
├── scraper/                     # Automated Extraction & Ingestion Engine
│   ├── fetch_dam_data.py        # English PDF parser with regex tabular matrix extraction
│   ├── daily_dam_worker.py     # Incremental daily scraper (~7s execution time)
│   └── download_english_pdfs.py # Parallel batch downloader for historical bulletins
│
├── web/                         # Modern Static Web Frontend (GitHub Pages)
│   ├── index.html               # Main SPA dashboard (#overview, #damDetail, #about)
│   ├── index.css                # Responsive stylesheet with Light & Dark mode tokens
│   ├── app.js                   # Client SPA router, Chart.js graphs, Command Palette
│   ├── logo.png / logo.svg      # Circular hydro-analytics emblem branding
│   ├── favicon.ico / favicon.svg# Multi-size vector and raster favicons
│   └── data/                    # Decoupled static JSON feeds
│       ├── latest.json          # Real-time metrics & metadata for 139 dams (~160 KB)
│       ├── dates.json           # Index of 1,046 available historical dates
│       └── history/*.json       # 139 decoupled per-dam historical time-series shards
│
├── scripts/                     # Maintenance & Metadata Scripts
│   ├── enrich_dam_metadata.py   # Curates authentic imagery, Wikipedia links, and specs
│   └── generate_logo.py         # Vector and raster logo generator
│
├── .github/workflows/           # CI/CD Automation
│   └── daily_dam_scraper.yml   # Scheduled workflow for daily bulletin processing
│
├── systemd/                     # Headless Linux Daemon Configuration
│   ├── dam_scraper.service      # Systemd service unit definition
│   └── dam_scraper.timer        # Systemd timer unit for automated scheduling
│
├── CONTRIBUTIONS.md             # Open-source contribution guidelines & workflow
├── run.sh                       # One-click execution and database inspection utility
└── README.md                    # Project documentation
```

---

## 🚀 Installation & Local Development

### 1. Prerequisites
- **Python**: Version 3.10 or higher
- **SQLite**: Version 3.35+
- **Git**: Installed and configured
- **Modern Web Browser**: Chrome, Firefox, Safari, or Edge

### 2. Clone Repository & Setup
```bash
git clone https://github.com/psdtech07-pixel/Dam-Database.git
cd Dam-Database

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
pip install pypdf pdfplumber pandas requests
```

### 3. Inspect Database Health
Verify the 3NF schema, record counts, and latest readings:
```bash
./run.sh --inspect
# or directly with Python:
python3 database/db_manager.py --inspect
```

### 4. Run the Local Web Server
Start the local static server:
```bash
./run.sh 8000
# or:
python3 -m http.server 8000 --directory web/
```
Open **`http://localhost:8000`** in your browser.

Direct view URLs:
- **Overview Dashboard**: `http://localhost:8000`
- **About Page**: `http://localhost:8000/#/about`
- **About Developer**: `http://localhost:8000/#/about-us`
- **Khadakwasla Dam**: `http://localhost:8000/#/dam/khadakwasla`
- **Koyna Dam**: `http://localhost:8000/#/dam/koyna`
- **Ujjani Dam**: `http://localhost:8000/#/dam/bhima-ujjani`

### 5. Execute Incremental Ingestion Worker
To fetch recent bulletins and perform transactional upserts:
```bash
python3 scraper/daily_dam_worker.py --once --days 3
```

---

## 👨‍💻 About the Developer

Developed and maintained by:

**Parth Sadanand Debadwar**  
*Second-Year (SY) B.Tech Student — Instrumentation and Control Engineering*  
**Vishwakarma Institute of Technology (VIT), Pune**  
*Academic Period: 2025–2029*

- **GitHub**: [@psdtech07-pixel](https://github.com/psdtech07-pixel)
- **LinkedIn**: [linkedin.com/in/parth-debadwar-005205377](https://www.linkedin.com/in/parth-debadwar-005205377)

### Other Projects by the Developer
- **[Moodify Aura](https://modify-s9hc.onrender.com/)**: A mood-based music recommendation platform that connects user emotions with suitable songs using audio analysis and intelligent playlists.
- **[Arduino Masterclass](https://basics-of-arduino-eftdsakn0-psd-tech.vercel.app/)**: A comprehensive beginner-friendly learning resource covering Arduino fundamentals, electronics basics, sensor integration, and microcontroller programming.

---

## 🤝 Contributing

Contributions to data accuracy, scraper resilience, UI accessibility, or photographic attribution are welcome! Please read **[CONTRIBUTIONS.md](CONTRIBUTIONS.md)** for detailed workflows, coding standards, and ground rules.

---

## 📜 Data Source & Transparency Disclaimer

All hydrological records, dam water levels, storage capacities, and rainfall data presented on this platform are compiled directly from publicly available daily storage bulletins published by:

**Water Resources Department (WRD), Government of Maharashtra**  
*Official Bulletin: Daily Dam Water Storage Report (08:00 AM IST)*

> [!NOTE]  
> The **Maharashtra Dam Water Storage Analytics System** is an independent civic-tech and educational platform developed for public information, data transparency, and academic learning. It is **not** an official Government of Maharashtra website and does not claim any official government representation. For official regulatory, emergency flood release, or legal purposes, always consult the official communications of the Maharashtra Water Resources Department.

---

*© 2026 Maharashtra Dam Water Storage Analytics System • Designed & Developed by Parth Sadanand Debadwar*
