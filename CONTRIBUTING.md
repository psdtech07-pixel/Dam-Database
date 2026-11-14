# Contributing to the Maharashtra Dam Water Storage Analytics System

Thank you for your interest in contributing to the **Maharashtra Dam Water Storage Analytics System**! 

This project is an open-source, civic-tech initiative dedicated to making dam water-storage levels across Maharashtra accessible, structured, transparent, and understandable for citizens, researchers, students, and civic communities.

Contributions of all types—whether fixing a bug, enhancing the UI/UX, improving documentation, or curating verified hydrological metadata—are warmly welcomed.

---

## 🎯 Ways You Can Contribute

We welcome contributions in several key areas:

### 1. Data Quality & Hydrological Metadata
- **Dam Coordinates & Dimensions**: Adding or refining exact reservoir coordinates (latitude/longitude), crest elevation, full reservoir levels (FRL), or wall lengths.
- **River Basin & Taluka Mapping**: Verifying administrative talukas and hydrological sub-basins for smaller or newly added dams.
- **Bilingual Translations**: Enhancing Marathi/English naming accuracy and ensuring colloquial dam names are discoverable in search.

### 2. Visual Content & Photography
- **Authentic Reservoir Photography**: Contributing high-resolution, genuine photographs of dams, spillways, reservoirs, and river catchments across Maharashtra.
- **Licensing & Attribution**: Ensuring all images adhere to verified open-license terms (Creative Commons CC BY-SA, CC BY, or Public Domain) with photographer credits and source links.

### 3. Frontend & UI/UX Enhancements
- **Accessibility (a11y)**: Improving screen-reader support, ARIA labels, semantic markup, and keyboard navigation.
- **Responsive Layouts**: Optimising table views, cards, and charts for mobile devices, tablets, and high-DPI displays.
- **Data Visualisation**: Refining Chart.js time-series plots, storage breakdown bars, or delta indicators.

### 4. Data Engineering & Scraping Pipeline
- **Scraper Stability**: Hardening PDF extraction against unexpected layout shifts or network timeouts on the WRD portal.
- **Performance & Decoupling**: Improving static JSON serialization, query indexing, or build execution times.

---

## 🛠️ Contribution Workflow

To contribute code, documentation, or data changes, please follow this standard workflow:

### Step 1: Fork and Clone
1. Fork the repository on GitHub: [psdtech07-pixel/Dam-Database](https://github.com/psdtech07-pixel/Dam-Database).
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Dam-Database.git
   cd Dam-Database
   ```

### Step 2: Set Up Environment
1. Ensure Python 3.10+ and SQLite 3 are installed on your system.
2. (Optional) Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install required Python packages:
   ```bash
   pip install pypdf pdfplumber pandas requests
   ```

### Step 3: Create a Dedicated Branch
Create a descriptive branch for your work:
```bash
git checkout -b feature/dam-coordinates-enrichment
# or
git checkout -b fix/table-mobile-scrolling
```

### Step 4: Make Your Changes
- Follow existing project directory structures and coding patterns.
- Adhere to the Third Normal Form (3NF) relational database conventions in `database/`.
- Ensure frontend changes in `web/` maintain light/dark mode compatibility and work without dynamic server runtimes.

### Step 5: Test Locally
1. Verify database integrity and run test exports:
   ```bash
   python3 -c "import sqlite3; conn = sqlite3.connect('database/pune_dams.db'); print('Dams:', conn.execute('SELECT count(*) FROM dams').fetchone()[0]); conn.close()"
   ```
2. Launch a local web server to inspect UI changes:
   ```bash
   python3 -m http.server 8000 --directory web/
   ```
   Open `http://localhost:8000` in your web browser.
3. If editing JavaScript, verify syntax with:
   ```bash
   node -c web/app.js
   ```

### Step 6: Commit and Submit a Pull Request
1. Commit with a clear, conventional commit message:
   ```bash
   git commit -m "feat: add geographic coordinates and spillway details for Konkan dams"
   ```
2. Push the branch to your fork:
   ```bash
   git push origin feature/dam-coordinates-enrichment
   ```
3. Open a Pull Request against the `main` branch of [psdtech07-pixel/Dam-Database](https://github.com/psdtech07-pixel/Dam-Database).
4. Provide a concise description of your changes, the rationale, and any visual before/after screenshots if modifying the UI.

---

## 📋 Ground Rules & Guidelines

To maintain project stability, performance, and legal compliance, please respect these ground rules:

1. **Database Schema Integrity (3NF)**:
   - Always preserve foreign key constraints, primary keys, and table normalisation.
   - Do not store redundant administrative names or duplicate rows.
   - Use SQLite transactions (`ON CONFLICT ... DO UPDATE`) for idempotent writes.

2. **No Large Binaries in Git History**:
   - Do **not** commit large PDF files, raw scraper cache files, or bulky video assets to git.
   - The repository uses `.gitignore` to keep `dam_pdf/` out of version control.
   - The web deployment operates strictly on lightweight static JSON feeds (`web/data/*.json`).

3. **Copyright, Fair Use & Image Attribution**:
   - Every photograph used must represent the actual dam, reservoir, river, or water body.
   - Only use images that are in the Public Domain or licensed under Creative Commons (e.g., Wikimedia Commons CC BY-SA).
   - Never use copyrighted stock images or irrelevant scenes (e.g. city traffic, night skylines).

4. **Civic Accuracy & Source Attribution**:
   - All hydrological metrics must originate from official bulletins published by the Water Resources Department (WRD), Government of Maharashtra.
   - Never fabricate, extrapolate, or alter official reservoir volume numbers.

5. **Code Quality**:
   - Write clean, readable, self-documenting code.
   - Preserve existing docstrings, SQL schemas, and comments.

---

## 💬 Community & Questions

If you have questions, encounter a data discrepancy, or want to discuss a new feature proposal before implementing it:
- Open an **Issue** on the [GitHub repository](https://github.com/psdtech07-pixel/Dam-Database/issues).
- Reach out to the maintainer: **Parth Sadanand Debadwar** via [LinkedIn](https://www.linkedin.com/in/parth-debadwar-005205377) or [GitHub](https://github.com/psdtech07-pixel).

Thank you for helping make Maharashtra's public water data more accessible and useful for everyone!
