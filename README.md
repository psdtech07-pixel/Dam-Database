# Maharashtra 5 Dams Storage Scraper & Database Sync

Automated daily data collection & analytics pipeline for 5 major dams in Maharashtra:
1. **Khadakwasla** (`dam_khadakwasla`)
2. **Panshet** (`dam_panshet`)
3. **Mulshi** (`dam_mulshi`)
4. **Gunjawani** (`dam_gunjawani`)
5. **Temghar** (`dam_temghar`)

---

## 📌 Features

- **Multi-Dam PDF Scraper**: Downloads daily PDF storage reports from Water Resources Department (WRD), Maharashtra.
- **Parallel Text Processing**: Fast extraction using multi-threaded `pdftotext` & layout parsers.
- **Automated MySQL Database Sync**: Creates separate tables for each dam (`dam_<name>`) and upserts new daily records using `ON DUPLICATE KEY UPDATE`.
- **Excel & CSV Exports**: Formatted Excel (`Maharashtra_5_Dams_Data.xlsx`) with master sheet + individual tabs per dam.
- **GitHub Actions Integration**: Daily automated Cloud execution at 09:00 AM IST.

---

## 🛠️ Setup & Installation

### 1. Install Dependencies

```bash
sudo apt-get install poppler-utils
pip install pandas openpyxl mysql-connector-python pypdf pdfplumber schedule
```

### 2. Run 10-Year Historical Data Scraper

```bash
python3 fetch_maharashtra_dams_data.py 3650
```

### 3. Run Daily Background Worker

```bash
python3 daily_dam_worker.py
```

---

## 📊 Database Schema (Example: `dam_khadakwasla`)

```sql
CREATE TABLE IF NOT EXISTS dam_khadakwasla (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    report_time VARCHAR(20),
    dead_storage_mcm FLOAT,
    design_live_storage_mcm FLOAT,
    design_gross_storage_mcm FLOAT,
    current_live_storage_mcm FLOAT,
    current_gross_storage_mcm FLOAT,
    current_live_storage_pct FLOAT,
    last_year_storage_pct FLOAT,
    status VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## ☁️ GitHub Actions Daily Cloud Sync

The workflow file `.github/workflows/daily_dam_scraper.yml` automatically executes every day at **09:00 AM IST** to scrape new reports, update GitHub files, and sync to Cloud MySQL.
