# Pune 5 Dams Water Storage DBMS & Analytics System 💧

An enterprise-grade **Database Management System (DBMS)** and real-time Web Analytics Dashboard for 5 major dam reservoirs in Pune, Maharashtra:
1. **Khadakwasla** (`KHD`)
2. **Panshet** (`PNS`)
3. **Mulshi** (`MUL`)
4. **Gunjawani** (`GNJ`)
5. **Temghar** (`TMG`)

---

## 🏛️ Project Architecture & Directory Structure

The repository is organized following clean DBMS modular software engineering principles:

```
├── database/                   # Relational DBMS Core (3NF Schema)
│   ├── pune_dams.db            # SQLite 3NF Database (4,915 storage logs across 983 days)
│   ├── schema.sql              # SQL DDL & DML Schema (3NF Tables, Indexes, Views)
│   └── db_manager.py           # Relational Database Engine, Upsert & Faculty Inspector
│
├── scraper/                    # Ingestion Engine & Automated Workers
│   ├── fetch_dam_data.py       # Multi-threaded PDF parser with 7-day median filter
│   └── daily_dam_worker.py    # Daily cron worker for continuous background scraping
│
├── web/                        # Web Dashboard UI Assets
│   ├── index.html              # Modern glassmorphism dashboard UI
│   ├── index.css               # Modern CSS styling system & dark mode tokens
│   ├── app.js                  # Dynamic Chart.js rendering, KPIs, & filter engine
│   └── dam_data.json           # High-speed JSON export generated from SQL Views
│
├── dam_pdfs/                   # Cached daily official WRD PDF reports (891 PDFs)
├── run.sh                      # One-click launcher for web server & faculty inspect tool
├── index.html                  # Root redirect to web/index.html for GitHub Pages
└── README.md                   # Documentation
```

---

## 📌 Key DBMS Features

- **3rd Normal Form (3NF) Relational Schema**: Clean separation of master metadata (`dams`), daily time-series logs (`daily_dam_storage_logs`), and audit logs (`system_audit_logs`).
- **Relational View (`vw_dam_daily_analytics`)**: Pre-joined view computing remaining storage volume (MCM) and year-over-year percentage change.
- **0 Data Loss Ingestion**: Direct UPSERT via `ON CONFLICT(dam_id, report_date)` in SQLite.
- **Zero Flat File Dependency**: All historical CSV/XLSX flat files deleted; SQLite `.db` acts as sole single source of truth.
- **Faculty Inspection Tool**: Run `./run.sh --inspect` or `python3 database/db_manager.py --inspect` for real-time schema audit reports.

---

## 🚀 Quick Start

### 1. View Faculty DBMS Inspection Report
```bash
./run.sh --inspect
```

### 2. Launch Local Web Dashboard
```bash
./run.sh 8000
```
Open `http://localhost:8000` in your browser.

### 3. Run Ingestion Scraper & Update Database
```bash
python3 scraper/fetch_dam_data.py
```

---

## ☁️ GitHub Actions Daily Sync

The GitHub Actions workflow (`.github/workflows/daily_dam_scraper.yml`) automatically executes daily at 09:00 AM IST to fetch new PDF reports, update `database/pune_dams.db`, and regenerate `web/dam_data.json` for live GitHub Pages deployment.
