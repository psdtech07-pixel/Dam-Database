# updates.md — Technical Review & Fix Plan (Maharashtra Dam Water Storage / HydroAnalytics)

> **Audience:** an AI coding agent (Antigravity) working inside this repo.
> **Reviewed commit:** `68358f9` ("feat: finalize public platform, documentation and project improvements").
> **Review date:** 13 Nov 2026. Line numbers below refer to that commit and may drift as you edit — search by the quoted code, not only by number.
> **How the numbers were obtained:** the repo was cloned and `database/pune_dams.db`, the scraper, the workflows and `web/app.js` were read and queried directly. Every "baseline" number in this file was measured, not estimated. A runnable audit script that reproduces them is in **Appendix A**.

---

## 0. Rules for the agent (read first)

1. **Do not invent data.** Never fill dam height, length, year, coordinates, capacities or photos from memory or guesswork. If a value cannot be verified from a source listed in this file, store `NULL` and let the UI show "—". Fabricated-but-plausible values are the single worst class of bug in this repo (see B04).
2. **Keep the architecture.** It is: WRD PDF → Python scraper → SQLite → static JSON → static site on GitHub Pages, scheduled by GitHub Actions. Do **not** introduce a backend server, a framework rewrite, or another database. SQLite stays (see §5).
3. **Keep the look and feel.** Do not redesign the UI. Fix behaviour, data and wording only.
4. **Work in phases (§4), one commit per issue ID**, message format `fix(B02): compute real since-yesterday delta`. Create a branch `fix/review-2026-11` first.
5. **Back up before anything destructive.** Before touching the DB: `mkdir -p backup && cp database/pune_dams.db backup/pune_dams.$(date +%F).db` (`backup/` is already gitignored). Before any re-ingest, show me the old-vs-new diff report (see B03) and wait for confirmation.
6. **Run `python scripts/audit_data.py` (Appendix A) before and after every phase** and paste the output into the commit message or the PR description. The goal is that every `[FAIL]` becomes `[PASS]`.
7. **Preserve URLs.** Existing deep links like `#/dam/<slug>` must keep working. When a slug is merged or renamed, add an alias redirect (B07).
8. **If something here contradicts what you see in the code, trust the code, tell me, and adjust.** Items marked *hypothesis* have not been confirmed.

---

## 1. Ratings given in the review

| Area | Rating | Notes |
|---|---|---|
| **Overall project (as it stands)** | **6.5 / 10** | Strong scope and engineering instincts for a second-year project. Data integrity problems are serious and some are visible on the live site. |
| **Repo structure** | **6 / 10** | Sensible top-level split, but binaries/dumps in git, duplicated files, stale leftovers, doc sprawl, no requirements/tests/LICENSE. |
| **Database — on paper** | **7 / 10** | Properly normalized hierarchy, FKs, CHECKs, UNIQUE + UPSERT, right composite index, useful view. |
| **Database — in practice** | **5 / 10** | The constraints do not catch the real bugs; derived columns are stored and drift apart; sentinel values instead of NULL; no provenance; schema drift. |
| **Projected after B01–B03, B05, B06** (fix the bugs, parse PDFs by column, reject instead of clamp) | **≈ 7.5 / 10** | The things a reviewer will find first when spot-checking. |
| **Projected after the full plan in this file** | **8.5+ / 10** | |

**What is already good — do not break it:**
- Static-JSON architecture; zero running cost; no server to maintain.
- Schema hierarchy `divisions → districts → dams ← basins`, enforced FKs, CHECK constraints, `UNIQUE(dam_id, reading_date)` with UPSERT (idempotent ingest), composite index `(dam_id, reading_date DESC)`, the `vw_dam_daily_analytics` view, transactional ingest with rollback.
- UX: plain-language framing, colour bands with explanations, unit conversions (ML / MCM / TMC), ⌘K search, CSV export, per-dam pages.
- Scale: 139 dams, 30 districts, 130,154 rows, 1 Jan 2024 → 12 Nov 2026.

---

## 2. Issue index

Severity: **P0** = wrong or breaking now or soon · **P1** = significant · **P2** = hygiene / polish.

| ID | Sev | Issue | Primary files |
|---|---|---|---|
| B01 | **P0** | **Time bomb:** all data dated after 2026-12-31 is purged → site stops updating on 1 Jan 2027 | `database/db_manager.py` |
| B02 | **P0** | "Since yesterday" delta on the headline card is **hardcoded** | `web/app.js`, `web/index.html` |
| B03 | **P0** | ~3,241 rows with placeholder `live_storage_mcm = 100.0`; ~6,407 rows where % disagrees with live/design (column-shift parsing) | `scraper/fetch_dam_data.py`, `database/db_manager.py` |
| B04 | **P0** | **Fabricated metadata shown as fact** (87/139 dams: 45 m / 1,200 m / 1985; stock photos called "authentic") | `scripts/enrich_dam_metadata.py`, `database/db_manager.py`, `web/index.html`, `web/app.js` |
| B05 | **P0** | Silent clamping/masking instead of validation; unmatched dams silently dropped; missing last-year stored as `0` | `scraper/fetch_dam_data.py`, `database/db_manager.py` |
| B06 | P1 | YoY comparison mixes a simple average with a capacity-weighted figure | `web/app.js` |
| B07 | P1 | Duplicate dam `tillari` / `tillari-kokan-sindhudurg` splits one dam's history; 16 orphan history files; suspicious placeholder capacities | `database/dam_registry.json`, `web/data/history/` |
| B08 | P1 | Coverage claims are false: 264 partial days, 7 Nov 2026 missing, 138/139 on latest day; About-page stats hardcoded | `web/index.html`, scraper |
| B09 | P1 | No provenance / run log / quarantine → problems are invisible | DB schema |
| B10 | P1 | Schema drift, derived columns stored, sentinels instead of NULL, all dams typed `MAJOR`, lat/long NULL, no migrations | `database/schema*.sql`, `db_manager.py` |
| B11 | P1 | TLS verification disabled in the scraper | `scraper/fetch_dam_data.py` |
| B12 | P1 | CI: job reports success when scraping fails; no concurrency control; 5-day lookback only; stale backfill workflow; no failure alert | `.github/workflows/*`, `scraper/daily_dam_worker.py` |
| B13 | P2 | Repo hygiene: binaries/dumps in git, duplicated files, stale leftovers, doc sprawl, no requirements/tests/LICENSE, `sys.path` hacks, oversized `db_manager.py` | repo-wide |
| B14 | P2 | JSON export bloat: `indent=2`, duplicated keys, duplicate `latest*.json`, orphan files, whole-file rewrites each run | `database/db_manager.py` |
| B15 | P2 | Frontend: unpinned CDN script, unescaped `innerHTML`, inline `onclick`, `Date.now()` cache-busting, placeholder text, colour-only status, no `<noscript>` | `web/index.html`, `web/app.js` |
| B16 | P2 | Tests, documentation accuracy, wording | repo-wide |

---

## 3. Issues in detail

Each issue has: **Problem → Evidence → Root cause → Fix → Acceptance**.

---

### B01 — Time bomb: the site stops updating on 1 Jan 2027 &nbsp;`P0`

**Problem.** Any row dated after `2026-12-31` is deleted on every export, and the history export also filters it out. From 1 Jan 2027 every new daily reading is purged and the site freezes at 31 Dec 2026 (while still looking "live").

**Evidence.**
- `database/db_manager.py` ~L259-267 `purge_corrupt_logs()`:
  `DELETE FROM dam_daily_logs WHERE reading_date < '2024-01-01' OR reading_date > '2026-12-31';`
- `database/db_manager.py` ~L385 (per-dam history export): `... AND reading_date <= '2026-12-31'`
- `export_decoupled_json()` calls `purge_corrupt_logs()` first, on every run.

**Fix.**
1. Remove hardcoded upper bounds everywhere. Validate dates **at ingest time** against a moving window, not at export time:
   ```python
   from datetime import date, timedelta
   MIN_VALID_DATE = date(2024, 1, 1)
   def is_valid_report_date(d: date) -> bool:
       return MIN_VALID_DATE <= d <= date.today() + timedelta(days=1)   # +1 for IST/UTC skew
   ```
2. Delete `purge_corrupt_logs()` from the export path. If you keep it, make it an explicit CLI action (`python database/db_manager.py --purge-invalid`) that uses `date('now','+1 day')` as the upper bound.
3. In the history export remove the `reading_date <= '2026-12-31'` condition entirely.
4. `ingest_records_from_dataframe` currently rejects `dt_obj.year < 2024` (~L189). Replace with `is_valid_report_date`.
5. Grep for any other hardcoded year: `grep -rn "2026\|2024" --include=*.py --include=*.js --include=*.yml .` and review each hit (the About page also hardcodes "12 November 2026", see B08).

**Acceptance.**
- Add a unit test: ingest a record dated `date.today()` and one dated `2027-01-05` (mock `date.today()` to 2027-01-06) → both survive an export.
- `grep -rn "2026-12-31" .` returns nothing.

---

### B02 — "Since yesterday" delta is fake &nbsp;`P0`

**Problem.** The headline card always shows a hardcoded delta with a down arrow, whatever the data says.

**Evidence.**
- `web/app.js` L397-401: ``deltaText.innerText = `↘ -0.12% · -1,420 ML · since ${yesterdayDate}`;``
- `web/index.html` L169: static text `↘ -0.15% · -1,520 ML · since yesterday` (shown if JS is slow/off).
- Real value for Pune, 11 Nov → 12 Nov 2026 from the project's own DB: **−0.30 pp, ≈ −37,710 ML** (81.54 % → 81.23 %).

**Fix.**
1. **Export** (in `export_decoupled_json`, latest snapshot query): add each dam's previous reading so the browser can compute a like-for-like delta without loading history.
   ```sql
   SELECT ..., l.reading_date, l.live_storage_mcm,
          p.reading_date      AS prev_date,
          p.live_storage_mcm  AS prev_live_mcm
   FROM dams d
   JOIN ... 
   LEFT JOIN dam_daily_logs l ON l.dam_id = d.dam_id
        AND l.reading_date = (SELECT MAX(reading_date) FROM dam_daily_logs WHERE dam_id = d.dam_id)
   LEFT JOIN dam_daily_logs p ON p.dam_id = d.dam_id
        AND p.reading_date = (SELECT MAX(reading_date) FROM dam_daily_logs
                              WHERE dam_id = d.dam_id AND reading_date < l.reading_date)
   ```
   Add `prev_date` and `prev_live_mcm` to the per-dam JSON object (use `null`, never `0`, when absent).
2. **Frontend** (`updateHeroAnalytics`): compute from the exported fields, only over dams that have both readings, so the two sums are comparable.
   ```js
   function computeRegionDelta(dams) {
     let cur = 0, prev = 0, cap = 0, n = 0; const dates = {};
     for (const d of dams) {
       if (d.prev_live_mcm == null || d.live_mcm == null) continue;
       cur += d.live_mcm; prev += d.prev_live_mcm; cap += d.design_live_mcm; n++;
       dates[d.prev_date] = (dates[d.prev_date] || 0) + 1;
     }
     if (!n || !cap) return null;
     const prevDate = Object.entries(dates).sort((a, b) => b[1] - a[1])[0][0];   // most common
     return { pp: (cur - prev) / cap * 100, ml: (cur - prev) * 1000, prevDate, n, total: dams.length };
   }
   ```
   Render: `↗` if > +0.005, `↘` if < −0.005, `→` otherwise; format with `toLocaleString('en-IN')`; label `since ${formatDateDisplay(prevDate)}` (not "yesterday" — the previous report may be older). If the result is `null` render `—`. If `n < total`, append a muted `(n of total dams)`.
3. **Delete** the hardcoded string in `index.html` L169 (leave the span empty or `—`) and delete `getYesterdayDateString()` if it becomes unused.

**Acceptance.** For Pune on the current data the pill reads approximately `↘ −0.30% · −37,710 ML · since 11 Nov 2026` (exact figures may change slightly after B03's re-ingest). Change one dam's `prev_live_mcm` in a local JSON copy and confirm the pill changes.

---

### B03 — Corrupt storage values from column-shift parsing &nbsp;`P0`

**Problem.** The scraper reads table cells **by position** from whitespace-split numbers. When a cell is blank or a column is absent, every following number shifts left and the wrong value lands in the wrong field.

**Evidence (measured).**
- **3,241 rows** have `live_storage_mcm = 100.0` exactly while the dam's design capacity ≠ 100 (e.g. Koyna, capacity 2,835 MCM: live = 100.0 but pct = 97.85 on 2025-11-12). Because the pct is right and the MCM is wrong, any MCM-based aggregate over history is wrong, and the *Volume Breakdown* chart is unreliable for those dates.
- **6,407 rows (4.9 %)** where stored `storage_pct` differs from `100·live/design` by more than 2 pp (e.g. Mukane: 1.31 MCM stored, 75.29 % stored; Totladoh 2025-07-11: live 100.0, pct 60.44).
- *Hypothesis (verify while re-parsing):* in sampled bad rows `live == 100.0` occurs where the dam is ~98–100 % full, i.e. a **percentage column is being read as MCM** after a shift.
- `scraper/fetch_dam_data.py` L227-240 uses `nums[0] … nums[6]` by index; L240: `last_pct_val = float(nums[6]) if len(nums) > 6 else 0.0`.
- The current day (2026-11-12) is clean (0 mismatches in `latest.json`), so the recent parse works; older layouts and some rows do not.

**Fix — rewrite the row parser to be column-aware, then rebuild history.**
1. **Collect samples.** Run `python scraper/fetch_dam_data.py` to download PDFs into `dam_pdf/` (gitignored). Pick: one recent PDF, one from `2025-11-12`, one from `2025-07-11`, one from early 2024. For each: `pdftotext -layout file.pdf out.txt` and *look at it*. Identify the header, the exact column order, and where cells can be blank.
2. **Parse by column, not by token order.** Either:
   - `pdfplumber`: `page.extract_words()` and bucket each word into a column by its `x0` using column boundaries derived from the header row of that page; or `page.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})` and tune; **or**
   - `pdftotext -layout` and slice each line by character offsets of the header columns.
   Return a typed record with **named** fields (`dead`, `design_live`, `design_gross`, `live`, `gross`, `pct`, `last_year_pct`) and `None` for blank cells. Never substitute `0.0` or a registry default for a missing value.
3. **Validate every row** (the function below) and send failures to quarantine (B05) — never "repair" them silently.
   ```python
   def validate(rec, design_live, tol_pp=2.0):
       errs = []
       if rec.live is None:                         errs.append("live_missing")
       elif rec.live < 0 or rec.live > design_live * 1.10: errs.append("live_out_of_range")
       if rec.live is not None and rec.pct is not None and design_live > 0:
           if abs(100 * rec.live / design_live - rec.pct) > tol_pp: errs.append("pct_mismatch")
       if rec.gross is not None and rec.live is not None and rec.gross < rec.live: errs.append("gross_lt_live")
       if rec.live == 100.0 and design_live != 100.0:  errs.append("suspect_default_100")
       return errs
   ```
   Tune `tol_pp` from data: compute `|100·live/design − pct|` over rows that currently pass and choose a threshold that keeps ≥ 99 % of them (WRD rounds; some dams legitimately exceed 100 %).
4. **Rebuild instead of patching.** Add `database/build_db.py` that creates a *new* DB file, ingests **all** PDFs from `2024-01-01` to today, runs `audit_data.py`, and only then swaps it in. Patching old rows in place leaves stale bad rows behind wherever the new parser now (correctly) rejects a record.
5. **Produce an old-vs-new diff report** (`reports/rebuild_diff.md`): rows changed per dam, rows quarantined per reason, dates whose dam count changed. **Stop and show it before replacing `pune_dams.db`.**
6. Unify the capacity cap: `fetch_dam_data.py` L247 uses 1.2× and `db_manager.py` L212 uses 1.5×. Remove both clamps (see B05) and use the single validation above.
7. Do **not** take `design_live_mcm` from `dam_registry.json` blindly. Compare registry capacities to the PDF's own capacity columns for every parsed row and report differences (see B07 for suspicious ones).

8. **Take the report date from the PDF, not from the filename.** `fetch_dam_data.py` L167-170 and L254-260 prefer the date in the *filename* (`report_DD-MM-YYYY.pdf`) over the `dd/mm/yyyy` printed in each row. If WRD re-uploads yesterday's bulletin under today's file name, the data is silently mislabelled. Parse the row date, compare it with the filename date, and quarantine mismatches (`reason = "date_mismatch"`). Also store a SHA-256 of each PDF in `ingest_runs` and flag two different dates with identical hashes.
9. **Investigate frozen values (do not "fix" blindly).** Measured: **404 runs of ≥ 20 consecutive days with an identical non-zero `live_storage_mcm`**, and 128 of 139 dams have a run ≥ 14 days. Longest: `bham-dam` 69.76 MCM for 152 days (2025-07-06 → 2025-12-05) and again 151 days in 2024; `bhavali` 40.62 MCM for 141 days; `thokerwadi-tata` 352.64 MCM for 109 days. Some of this can be genuine (a dam held at full pool; dry dams at ~0), but it can also be clamping (B05) or stale PDFs. After the rebuild, list runs ≥ 7 days where the WRD **pct changes while live MCM does not** — those are bugs. Report the rest to me with a short classification.

**Acceptance.** After rebuild, `audit_data.py` shows 0 for: `live == 100.0 placeholder`, `pct disagrees with live/design`. Spot-check Koyna 2025-11-12 → live ≈ 2,774 MCM (97.85 % × 2,835.5), not 100.0.

---

### B04 — Fabricated metadata presented as fact &nbsp;`P0`

**Problem.** 87 of 139 dams (63 %) show **identical placeholder facts** — height **45.0 m**, length **1,200 m**, completed **1985** — under *"Dam Specifications & Vital Information"*. Descriptions for these dams are one generated template sentence. The About page claims *"authentic dam photography"*, but there are only **36 distinct Unsplash stock images** for 139 dams (one image is shared by 43 dams).

**Evidence.**
- `scripts/enrich_dam_metadata.py` ~L110-116: `year = meta.get('year', 1985)`, `height_m = meta.get('height_m', 45.0)`, `length_m = meta.get('length_m', 1200.0)`, a template `description`, and a per-division default `image_url` (map at L17-22).
- Only ~52 dams have hand-entered values in `DAM_METADATA`.
- A second layer of fake defaults at export: `database/db_manager.py` L327-334 `'river': ... or 'Major River'`, `'year': ... or 1980`, `'purpose': ... or 'Irrigation & Drinking Water Supply'`, `'height_m': ... or 45.0`, `'length_m': ... or 1200.0`.
- Claim at `web/index.html` L811: "…vital engineering specifications, and authentic dam photography."
- List the affected dams with: `SELECT dam_slug FROM dams WHERE height_m = 45.0 AND length_m = 1200.0;`

**Fix.**
1. **Stop generating placeholders.** In `enrich_dam_metadata.py` use `None` for any missing `year`, `height_m`, `length_m`, `taluka`, `nearest_city`, `river`, `purpose`, `description`, `image_url`. Remove the template `description` and the per-division default image.
2. **Remove fallbacks at export** (`db_manager.py` L327-334): emit `null`.
3. **Make the DB honest.** One-off migration: `UPDATE dams SET height_m=NULL, length_m=NULL, completion_year=NULL WHERE height_m=45.0 AND length_m=1200.0;` and null the template descriptions / default image URLs / the division-default `river` and `purpose` strings.
4. **Frontend:** render `—` for null spec rows; hide the Wikipedia link when `wikipedia_url` is empty (currently renders a `#` link, `index.html` L624); hide the description paragraph when null (remove the `Description loading...` placeholder at L579, or show it only while the fetch is in flight). If a dam has no real photo, show a neutral inline-SVG placeholder with the caption "Photo not available" — **do not** use a stock lake photo as if it were that dam.
5. **Fix the claim** at `index.html` L811 → drop "authentic dam photography" unless every photo is a real, attributed photo.
6. **Fill real data only from verifiable sources, and record provenance** (add `meta_source TEXT` per dam or per field). Candidate sources (check each is accessible and licensing allows use; cite it on the page): CWC *National Register of Large Dams* (height, length, year, coordinates), India-WRIS, Wikipedia/Wikidata, WRD project pages. Photos: Wikimedia Commons with licence + attribution shown in the caption. **If you cannot verify a value, leave it NULL.**
7. Populate `latitude` / `longitude` (currently NULL for all 139) from the same verified sources; this unlocks a map later.

**Acceptance.** `audit_data.py`: `placeholder 45 m / 1200 m` = 0 and `placeholder year 1985` = 0 (they may instead be real values for some dams). No dam page shows an invented number.

---

### B05 — Silent masking instead of validation &nbsp;`P0`

**Problem.** Anomalies are clamped, defaulted or skipped without any trace, which hides parser bugs and corrupts data.

**Evidence.**
- **Clamp to capacity:** `fetch_dam_data.py` L247 `if live_val > design_live*1.2: live_val = min(live_val, design_live)`; `db_manager.py` L212 same at 1.5×. Result: **11,655 rows** have `live == design` exactly. Real overflow above 100 % is hidden.
- **Missing → 0:** `fetch_dam_data.py` L240 `last_pct_val = ... else 0.0`; `db_manager.py` L343 export turns NULL into `0.0`. Result: **5,336 rows** store `last_year_pct = 0`, which the UI cannot tell apart from "no data".
- **Unmatched names dropped:** `db_manager.py` (`if not info: continue` in `ingest_records_from_dataframe`) and `fetch_dam_data.py` L213-219 fall back to an auto-generated slug that is then ignored at ingest. Result: Tillari is **absent from the latest day** and nothing reports it.
- **Hardcoded fallbacks:** `fetch_dam_data.py` L62-63 `live` default `100.0`, `gross` default `110.0`; L228 `... else 100.0`.
- `pct` clamped to `[0, 120]` at L250-251 — 18 rows sit exactly at 120.

**Fix.**
1. **Never clamp or default measurements.** Missing → `None`/`NULL`. Out of range → quarantine with a reason.
2. **Add two tables** (also see B09):
   ```sql
   CREATE TABLE ingest_quarantine (
     id INTEGER PRIMARY KEY, report_date TEXT, source_pdf TEXT,
     raw_line TEXT, parsed_json TEXT, reason TEXT,
     created_at TEXT DEFAULT CURRENT_TIMESTAMP);
   CREATE TABLE ingest_runs (
     run_id INTEGER PRIMARY KEY, report_date TEXT, source_pdf TEXT,
     rows_parsed INTEGER, rows_ingested INTEGER, rows_quarantined INTEGER,
     rows_unmatched INTEGER, expected_dams INTEGER, status TEXT,
     started_at TEXT, finished_at TEXT);
   ```
3. **Unmatched names:** collect them, write to `ingest_quarantine` with reason `unmatched_name`, print a summary, and make the run **fail** (non-zero exit) if any unmatched name appears on the latest report date.
4. **Completeness gate:** after parsing a PDF, if `rows_ingested < 0.95 × expected_dams` (expected = number of dams in registry), mark the run `PARTIAL`, do not publish JSON, exit non-zero (see B12).
5. Allow real overflow: keep values up to `design × 1.10` as-is (they are real when a dam is above FRL); beyond that quarantine.

**Acceptance.** `last_year_pct == 0` count is 0 (NULL instead); `live == design` count drops to a small number of genuinely full dams; every parsed-but-rejected row is visible in `ingest_quarantine`.

---

### B06 — YoY comparison is apples-to-oranges &nbsp;`P1`

**Problem.** The "2025" bar is a **simple average** of per-dam last-year % (zeros excluded), while the "2026" bar is **capacity-weighted** (`Σlive / Σdesign`). Capacity-weighted last-year for Pune on 12 Nov is **≈ 97.3 %**, but the page shows **93.1 %**.

**Evidence.** `web/app.js` L355-367 (`yoySum/yoyCount`), L426-428 (bars), L446 (advisory text uses the same average).

**Fix.**
```js
let lyNum = 0, lyDen = 0;
for (const d of regionDams) {
  if (d.last_year_pct != null && d.design_live_mcm > 0) {   // null, not 0, means "no data"
    lyNum += d.last_year_pct * d.design_live_mcm;
    lyDen += d.design_live_mcm;
  }
}
const lastYearPct = lyDen > 0 ? lyNum / lyDen : null;      // capacity-weighted, like overallPct
```
- If `lastYearPct == null` hide the 2025 bar and the "Last year on this date" sentence rather than show `0.0%`.
- Show coverage: `…based on {count} of {total} dams` when some dams lack a last-year value.
- Replace `Number(dam.last_year_pct) || 0` (L500, L573, L1097, L1150) with null-aware handling.
- Label the bars with the actual years from the data (`batch_date.year`, `year−1`) instead of the hardcoded "2025/2026" in `index.html`.
- **Cross-check (nice to have, after B03):** once the history is clean, compute last-year from the project's own table (`reading_date = date(today,'-1 year')`) and flag dams where it differs from the WRD column by > 5 pp. Today 81 of 87 comparable dams agree within 5 pp, so the check is meaningful.

**Acceptance.** For Pune the 2025 bar ≈ 97 % (not 93 %); hiding works when the data is absent.

---

### B07 — Duplicate dam, orphan files, suspicious capacities &nbsp;`P1`

**Problem.**
- `tillari` and `tillari-kokan-sindhudurg` are the **same dam** (same capacity 447.37 / 462.17, same keys). `tillari` has 985 rows ending **2026-09-27**; `tillari-kokan-sindhudurg` has 782 rows ending **2026-11-12**. The history is split, and the name lookup collides because both entries list `'tillari'` in `keys`.
- **16 orphan history files** (155 files vs 139 dams): `andra, dhalegaon-hlb, dhanegaon-hlb, dongargaon-hlb, ghod-chinchani, jayakwadi-paithan, kalmodi, kasarsai, kawdas-weir, mulshi-tata, nazare, pujaritola, siddheshwar, ujani, visapur, walwhan-tata`.
- `mangrul-h-l-b` and `rajatakli-h-l-b` both have `live=25.0, gross=25.0, dead=0.0` — look like placeholders, not WRD capacities.

**Fix.**
1. **Merge Tillari.** Canonical slug `tillari`. Move all rows of `tillari-kokan-sindhudurg` into `tillari`; where both have the same `reading_date`, keep the row that passes the B03 validation (prefer the newer ingest). Delete the duplicate registry entry; keep its slug in a `slug_aliases` mapping.
2. **Slug alias redirects** (preserve old URLs): add `web/data/slug_aliases.json` (`{"tillari-kokan-sindhudurg": "tillari", "ujani": "bhima-ujjani", ...}`) and in `handleHashRouting` resolve aliases before looking up a dam. Build the alias list from the 16 orphan filenames + merged slugs (map each to its current registry slug; if there is no clear match, ask me).
3. **Delete orphan history files** and make the exporter clean up after itself: after writing, `for f in history_dir.glob("*.json"): if f.stem not in current_slugs: f.unlink()`.
4. **Alias-collision guard:** when building the lookup (both `db_manager.get_dam_lookup_map` and `fetch_dam_data.load_dam_lookup`), if one alias key maps to two different slugs, **raise an error** instead of letting the later entry win. This would have caught Tillari.
5. **Registry capacity audit:** write `scripts/audit_registry.py` that compares each registry entry's `dead/live/gross` with the values in the latest PDF and prints differences. Fix the registry from the PDF; mark any dam where the PDF also lacks capacity as `NULL` and report it.

**Acceptance.** 138 dams (or 139 if the second `Tillari` was in fact distinct — verify against the PDF first), 0 dams missing on the latest day, history files == dams, `audit_registry.py` reports no mismatches.

---

### B08 — Coverage claims are false; About-page stats are hardcoded &nbsp;`P1`

**Problem / Evidence (measured).**
- **264 of 1,046 days (25 %)** report fewer than 130 dams (as low as 6 on 2024-01-11; many days have ~85-90). These are not "complete" daily records.
- **2026-11-07 is missing** (gap between 11-06 and 11-08), yet the About page says *"consecutive daily records spanning continuously"* (`index.html` L815) and *"Continuous Days"* / `1,046` (L837); 1 Jan 2024 → 12 Nov 2026 is 1,047 days.
- **Latest day has 138 of 139 dams** (Tillari, B07).
- `index.html` L822-837 hardcode `139`, `6`, `1,30,154`, `1,046` — they will be wrong tomorrow. L396 shows "0 reservoirs monitored" until JS loads.
- `About` text hardcodes "12 November 2026".

**Fix.**
1. **Find out why days are partial** (do not guess). For every date with < 135 dams run a diagnostic: count lines in the PDF text that contain a `dd/mm/yyyy` date (candidate rows) versus rows the parser accepted. Classify each day as **(a)** WRD's PDF genuinely has fewer rows, **(b)** the parser dropped rows, **(c)** PDF missing/unparseable. Suspects in the current parser: name regex `[A-Za-z0-9\(\)\.\s\-\/]` excludes `'` `,` `&`; rows with `len(nums) < 5` are skipped; header filter substrings (`'PROJECT'`, `'TOTAL'`, `'STORAGE'`) applied to names; older layouts. Fix (b); document (a)/(c).
2. **Add a coverage table** `report_calendar(report_date PRIMARY KEY, status TEXT, dams_reported INT, note TEXT)` with status `OK | PARTIAL | NOT_PUBLISHED | PARSE_FAILED`. Fill it from `ingest_runs` and the download results. For 2026-11-07 determine whether WRD published a PDF; record `NOT_PUBLISHED` if not.
3. **Make the stats dynamic:** export `web/data/meta.json` = `{dams, divisions, rows, days_covered, first_date, last_date, days_partial, days_missing, generated_at}` and fill `.stat-number` elements from it.
4. **Correct the wording:** replace "consecutive/continuous/verified" with accurate text, e.g. "Daily records from 1 Jan 2024; days on which WRD did not publish or published incomplete data are marked on the coverage page." Add a small "Data coverage" section/page that lists partial/missing days.
5. Add `<noscript>` and replace the static "0 reservoirs monitored" with a neutral skeleton/`—`.

**Acceptance.** Stats on the About page match `meta.json`; no false "continuous" claim; each partial day has a classified reason.

---

### B09 — No provenance, run log or quarantine &nbsp;`P1`

**Problem.** Nothing records which PDF a row came from, when it was ingested, or what was rejected. That is why 264 partial days and 9,600+ bad rows went unnoticed. (`system_audit_logs` exists in the shipped DB with 2 rows from September and is unused.)

**Fix.** Add `ingest_runs`, `ingest_quarantine` (B05), `report_calendar` (B08), and `source_pdf` + `ingested_at` columns on the fact table (B10). Add a `python database/db_manager.py --report` command that prints the last 7 runs and the quarantine counts per reason. Drop the unused `system_audit_logs`.

**Acceptance.** Any row can be traced to a PDF; `--report` runs and shows today's run.

---

### B10 — Schema drift, derived columns, sentinels, no migrations &nbsp;`P1`

**Problem / Evidence.**
- Two schema files (`database/schema.sql`, `database/schema_and_masters.sql`) and **legacy tables inside the shipped DB**: `river_basins` (5 rows), `daily_dam_storage_logs` (0 rows), `system_audit_logs`; `basins` and `river_basins` coexist.
- `dam_id` runs up to **1890** for 139 dams → the tables were dropped/recreated repeatedly. `init_db()` silently **drops tables** when it detects an old schema (`db_manager.py` L22-45).
- `dam_daily_logs.storage_pct`, `gross_storage_mcm`, `last_year_pct` are **derivable** (`live/design`, `live+dead`, same table one year earlier). Storing them let them drift apart (B03). *3NF note:* these are redundant derived attributes; compute them in the view.
- Sentinel values instead of NULL (B04, B05). All 139 dams typed `MAJOR` (`project_type NOT NULL CHECK(IN ('MAJOR','MEDIUM','MINOR'))` — the loader defaults to `'MAJOR'`, `fetch_dam_data.py` ~L60). `latitude`/`longitude` NULL for every dam. `river` is free text duplicating `basin`. `reading_time` is the string "08:00 AM".

**Fix — target schema v2** (keep the hierarchy; build it fresh via `build_db.py`, B03):
```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE divisions (division_id INTEGER PRIMARY KEY, division_name TEXT NOT NULL UNIQUE) STRICT;
CREATE TABLE districts (district_id INTEGER PRIMARY KEY, district_name TEXT NOT NULL UNIQUE,
                        division_id INTEGER NOT NULL REFERENCES divisions(division_id)) STRICT;
CREATE TABLE basins    (basin_id INTEGER PRIMARY KEY, basin_name TEXT NOT NULL UNIQUE) STRICT;

CREATE TABLE dams (
  dam_id INTEGER PRIMARY KEY, dam_slug TEXT NOT NULL UNIQUE,
  dam_name_en TEXT NOT NULL, dam_name_mr TEXT,
  district_id INTEGER NOT NULL REFERENCES districts(district_id),
  basin_id    INTEGER NOT NULL REFERENCES basins(basin_id),
  project_type TEXT CHECK (project_type IN ('MAJOR','MEDIUM','MINOR')),   -- NULL unless the bulletin says
  dead_storage_mcm REAL CHECK (dead_storage_mcm >= 0),
  design_live_mcm  REAL NOT NULL CHECK (design_live_mcm > 0),
  design_gross_mcm REAL CHECK (design_gross_mcm >= design_live_mcm),
  latitude REAL, longitude REAL, taluka TEXT, nearest_city TEXT, river TEXT,
  completion_year INTEGER, height_m REAL, length_m REAL,
  purpose TEXT, description TEXT, image_url TEXT, wikipedia_url TEXT,
  meta_source TEXT                                                         -- provenance of the facts above
) STRICT;

CREATE TABLE dam_aliases (alias TEXT PRIMARY KEY, dam_id INTEGER NOT NULL REFERENCES dams(dam_id)) STRICT;

CREATE TABLE dam_daily_logs (
  dam_id INTEGER NOT NULL REFERENCES dams(dam_id) ON DELETE CASCADE,
  reading_date TEXT NOT NULL CHECK (reading_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  live_storage_mcm REAL NOT NULL CHECK (live_storage_mcm >= 0),
  gross_reported_mcm REAL,          -- as published; for audit only
  pct_reported REAL,                -- as published; for audit only
  last_year_pct_reported REAL,      -- as published; NULL if blank (never 0)
  source_pdf TEXT NOT NULL,
  ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (dam_id, reading_date)
) STRICT, WITHOUT ROWID;
CREATE INDEX idx_logs_date ON dam_daily_logs(reading_date);

CREATE VIEW vw_dam_daily AS
SELECT l.dam_id, d.dam_slug, l.reading_date, l.live_storage_mcm,
       d.dead_storage_mcm + l.live_storage_mcm                       AS gross_storage_mcm,
       ROUND(100.0 * l.live_storage_mcm / d.design_live_mcm, 2)      AS storage_pct,
       COALESCE(ROUND(100.0 * y.live_storage_mcm / d.design_live_mcm, 2),
                l.last_year_pct_reported)                            AS last_year_pct,
       ROUND(d.design_live_mcm - l.live_storage_mcm, 2)              AS remaining_capacity_mcm
FROM dam_daily_logs l
JOIN dams d USING (dam_id)
LEFT JOIN dam_daily_logs y ON y.dam_id = l.dam_id AND y.reading_date = date(l.reading_date, '-1 year');
-- plus ingest_runs, ingest_quarantine, report_calendar from B05/B08
```
Notes: `STRICT` needs SQLite ≥ 3.37 — check `sqlite3.sqlite_version` locally and on the runner (Ubuntu 24.04 ships 3.45). The first year (2024) has no own-history last year, hence the `COALESCE` to the reported value.

**Migrations.** Use `PRAGMA user_version` and numbered files `database/migrations/0001_init.sql`, `0002_...sql`; a tiny runner applies those greater than the current version, each in a transaction. **Remove** the drop-tables-if-legacy logic from `init_db()`; refuse to start (with a clear message) if the DB is a newer version than the code.

**Housekeeping.** Delete `schema_and_masters.sql` and `supabase_data_dump.sql`, `supabase_migrator.py` (unused Supabase/MySQL path). Rename `pune_dams.db` → `maharashtra_dams.db` (it covers the whole state) and update every reference (`grep -rn pune_dams .`), workflows included.

**Acceptance.** One schema source; `PRAGMA user_version` = current; no legacy tables; `dam_id` contiguous; the view reproduces `latest.json` values.

---

### B11 — TLS verification disabled &nbsp;`P1`

**Evidence.** `scraper/fetch_dam_data.py` L18-20: `SSL_CONTEXT.check_hostname = False; SSL_CONTEXT.verify_mode = ssl.CERT_NONE`.

**Fix.**
1. First find out *why* it was disabled: `curl -v https://wrd.maharashtra.gov.in/` and check whether the failure is an incomplete certificate chain (common on Indian government sites).
2. Use verification by default: `ssl.create_default_context(cafile=certifi.where())` (add `certifi` to requirements).
3. If the chain is incomplete, bundle the missing intermediate certificate as `scraper/certs/wrd_chain.pem` and pass it as `cafile`/`load_verify_locations` — still verified.
4. Only as a last resort allow `WRD_INSECURE_SSL=1` to disable verification, and print a loud warning when it is used. The default must be secure.
5. Also validate downloads: keep the existing `%PDF-` + size check and additionally require the PDF text to contain the expected header (e.g. "Storage") before saving.

**Acceptance.** Scraper works with verification on in CI.

---

### B12 — CI/CD problems &nbsp;`P1`

**Evidence & fix, item by item.**

1. **Failures are reported as success.** `scraper/daily_dam_worker.py`: `run_daily_job()` catches every exception and returns `False`, but the `--once` branch ignores the return value, so the process exits 0 and the Actions job is green. **Fix:** `ok = run_daily_job(days=args.days); sys.exit(0 if ok else 1)`; also exit non-zero when B05's completeness/unmatched gates fail. Let unexpected exceptions propagate.
2. **No gate before publishing.** Add steps *before* the commit step: `pytest -q` and `python scripts/audit_data.py` (hard failures abort; nothing is committed).
3. **Race condition.** Two cron runs/day (`30 3` and `30 9` UTC) plus manual dispatch can overlap and collide on `git push`. Add:
   ```yaml
   concurrency:
     group: dam-data-update
     cancel-in-progress: false
   ```
   and `git pull --rebase` before `git push`.
4. **5-day lookback only** (`--days 5`): an outage longer than 5 days leaves a permanent gap. **Fix:** make the scraper compute *missing dates from the DB* between `2024-01-01` and today (using `report_calendar`) and retry up to N (e.g. 30) per run, skipping dates already marked `NOT_PUBLISHED`.
5. **Failure alert.** Add a final step `if: failure()` that opens/updates a GitHub issue (`permissions: issues: write`, `gh issue create`) or sends a notification.
6. **Hardening.** `timeout-minutes: 20`; `actions/setup-python` with `cache: pip`; `pip install -r requirements.txt` (pinned); drop `schedule` and `pypdf` if unused; remove `|| true` after `git add` (it hides failures); only `git add` files that exist.
7. **State problem (important):** the committed `database/pune_dams.db` is currently the pipeline's only persistent state (CI only downloads the last 5 days of PDFs). Do **not** simply `git rm` it. Use a text source of truth instead — see B13.1.
8. **Stale backfill workflow** `backfill_10year_pdfs.yml`: `git add dam_pdfs/ database/pune_dams.db web/dam_data.json || true` references gitignored/removed paths; installs `mysql-connector-python` (unused); advertises "10-year" but ingest rejects anything before 2024. **Fix:** rewrite it to call the same entrypoint as the daily job with `--days N` and a `--since` date; remove stale paths and MySQL; rename to "Historical backfill".
9. `systemd/` unit files and `daily_dam_worker.py` daemon mode are redundant with Actions; keep only if you actually use them, otherwise delete and update the docs.

**Acceptance.** Break the scraper on purpose (wrong URL) → the job turns red and nothing is committed. Two simultaneous runs don't fail.

---

### B13 — Repo structure & hygiene &nbsp;`P2`  (rated **6/10**)

**Evidence (measured).** `database/pune_dams.db` 28 MB and `database/supabase_data_dump.sql` 32 MB are committed (the DB is rewritten and re-committed on every data change); `HydroAnalytics.pptx` is committed although `.gitignore` lists `HydroAnalytics.pptx/` (trailing slash = directory pattern, matches nothing). `web/data/latest.json` and `latest_snapshot.json` are identical (168 KB each). `export_db_for_web.py` duplicates `db_manager.export_decoupled_json()`; `download_english_pdfs.py` overlaps `fetch_dam_data.download_pdf_for_date()`. Four docs at the root (`README.md` 368 lines, `ppt_info.md` 537, `SCRAPER_AND_AUTOMATION_GUIDE.md`, `CONTRIBUTIONS.md`). No `requirements.txt`, no tests, no `LICENSE`. Scripts use `sys.path.append(...)` hacks. `db_manager.py` (468 lines) mixes schema init, seeding, ingestion, export and inspection. Naming still says "Pune" in places (`pune_dams.db`, root `index.html` `<title>`, `run.sh` banner) although the project is statewide.

**Fix.**
1. **Text source of truth, binary DB as build artifact.** CI currently depends on the committed `.db` as its state (B12.7), so replace the state with a deterministic text file:
   - `database/seed/dam_daily_logs.csv` — one row per dam per day, sorted by `reading_date, dam_slug`, fixed column order, LF line endings. ≈ 130k rows ≈ a few MB; appends delta-compress well in git.
   - `build_db.py --from-csv` rebuilds the SQLite file; CI = build DB from CSV → ingest new PDFs → append new rows to the CSV → export JSON → commit **CSV + JSON only**.
   - Add `*.db` to `.gitignore`. Optionally attach the built DB to a GitHub Release.
   - **Do not rewrite git history** (`git filter-repo`/BFG) to purge the old blobs unless I explicitly ask — it breaks every existing clone/fork. Just stop adding new ones. Ask me first.
2. **Delete** `supabase_data_dump.sql`, `supabase_migrator.py`, `schema_and_masters.sql` (superseded, B10), `export_db_for_web.py`, `latest_snapshot.json` (and the fallback fetch at `app.js` L181-183), and `download_english_pdfs.py` after folding anything unique into the main downloader. Move `HydroAnalytics.pptx` to a GitHub Release or `docs/` and fix the `.gitignore` pattern if you keep it out of git.
3. **Target layout** (do this *after* correctness fixes; it is a refactor):
   ```
   .
   ├── README.md   LICENSE   CONTRIBUTING.md   requirements.txt
   ├── docs/        architecture.md  scraper-guide.md  project-report/ (ppt_info.md, pptx)
   ├── dam_tracker/ __init__.py  download.py  parser.py  validate.py  db.py  ingest.py  export.py  registry.py  cli.py
   ├── database/    migrations/  dam_registry.json  seed/dam_daily_logs.csv
   ├── scripts/     audit_data.py  audit_registry.py  enrich_dam_metadata.py
   ├── tests/       fixtures/ (pdftotext outputs)  test_*.py
   ├── web/         index.html  app.js  index.css  data/ (+ vendor/ if Chart.js is vendored)
   └── .github/workflows/  daily.yml  backfill.yml  ci.yml
   ```
   Run as `python -m dam_tracker daily` / `... backfill --since 2024-01-01` / `... build-db` / `... report`; no `sys.path` hacks. Split `db_manager.py` into `db.py` (connection/migrations), `ingest.py`, `export.py`. Keep `run.sh` working (local preview) and rename its banner.
4. **Add** `requirements.txt` (pin to the versions you actually run: `pip freeze | grep -iE "pandas|pdfplumber|pypdf|certifi|pytest"`), `LICENSE` (**ask me which licence** — code and data are different; WRD data needs attribution and the existing "unofficial" disclaimer), `CONTRIBUTING.md` (rename `CONTRIBUTIONS.md`).
5. **Rename** `pune_dams.db` → `maharashtra_dams.db` and fix every reference (`grep -rn "pune_dams\|Pune Dam" .`), including workflows, `run.sh`, root `index.html`, README.
6. **README accuracy pass:** remove claims that are not true after the fixes (10-year backfill, "continuous", "authentic photography") and document the real pipeline, data caveats, and how to run `audit_data.py` and the tests.

**Acceptance.** A fresh clone is < ~15 MB of tracked files without binaries; `pip install -r requirements.txt && pytest && python -m dam_tracker build-db` works on a clean machine.

---

### B14 — JSON export bloat & churn &nbsp;`P2`

**Evidence.** Per-dam history is written with `indent=2` **and duplicated keys** (`d/m/p` *and* `date/mcm/pct`) — `khadakwasla.json` is 125 KB raw (13 KB gzip); the same data as compact arrays is 27 KB raw (5 KB gzip). All 155 history files are rewritten on every export, so every run produces a large git diff. `latest.json` is indented and duplicated as `latest_snapshot.json`.

**Fix.**
1. History as compact arrays: `[["2024-01-01", 34.76, 62.17], ...]` written with `json.dump(..., separators=(",", ":"))`. Update the frontend where it reads history (`app.js` L738, L743, L858, L872-873, L1196-1201 — those already accept two key styles; replace with one adapter `const toPoint = ([d, m, p]) => ({ d, m, p })` applied once in `loadDamHistory`, and delete the dual-key branches).
2. Deterministic output (`sort_keys=True`, fixed rounding, LF) and **write a file only if its bytes changed** (compare before writing; write to a temp file then `os.replace`). Only dams with a new reading change daily, so the daily diff shrinks from ~155 files to the handful that actually changed.
3. Delete `latest_snapshot.json`; delete orphan history files (B07); emit `meta.json` (B08) with `generated_at`, `batch_date`, `schema_version`.
4. Export `null` (not `0`) for unknown numbers (B05/B06).

**Acceptance.** A typical daily commit touches `latest.json`, `meta.json`, `dates.json` and ≤ ~140 small history files only if their last row changed; total `web/data/` well under 17 MB.

---

### B15 — Frontend issues &nbsp;`P2`

1. **Unpinned CDN script.** `index.html` L20 `https://cdn.jsdelivr.net/npm/chart.js` resolves to whatever is latest — a future major release can break the charts, and an unverified third-party script runs on your page. Pin an exact version (check the current stable and pick one that is at least two weeks old), use the UMD build, add `integrity="sha384-…"` + `crossorigin="anonymous"`, or vendor it into `web/vendor/`. Test every chart afterwards (trend, volume breakdown, comparison).
2. **Unescaped `innerHTML`.** Data-derived strings are interpolated raw at `app.js` L446 (`regionNamePretty`), L523-533 (`name_en`, `name_mr`, `district`), L701, L1105, L1325-1334 and others; only the search box uses `escapeHtml` (L1399). The data is first-party today, but it originates from third-party PDF text. Escape every interpolation (or build nodes with `createElement` + `textContent`, or use a tiny tagged template that escapes by default). Add a test with a dam name containing `<img onerror=…>`.
3. **Inline `onclick="openDamPage('${slug}')"` on `div`s/`span`s** (L526, L701, L1105, L1119, L1328). Make cards real links `<a href="#/dam/${slug}">` — this gives keyboard access, middle-click/open-in-new-tab, and crawlable links — and use one delegated listener for the rest.
4. **Cache-busting defeats caching.** `?v=` + `Date.now()` on every fetch (L180, L182, L200, L820) means no HTTP caching. Fetch `meta.json` with `cache: 'no-cache'` (revalidate), then use `?v=${meta.generated_at}` for the other files.
5. **Silent failures.** `loadDamHistory` swallows errors (`catch (err) {}`, L826); init failure only sets the badge to "Offline Mode". Show a visible, dismissible error with Retry, and a **stale-data banner** when `batch_date` is more than 2 days old ("Latest WRD bulletin is from …; the source may not have published").
6. **Stale static placeholders.** `index.html` ships literal values (`81.2% Healthy`, `Report as of 12 November 2026`, `-0.15% …`, `0 reservoirs monitored`, `Description loading...`, `1,30,154`). Replace with neutral skeletons/`—` so a slow load never shows fake or outdated numbers (B02, B04, B08).
7. **Prescriptive advice from an unofficial site.** The advisory text at `app.js` ~L460-470 says things like "Strictly enforce water rationing…" when storage < 25 %. The footer correctly says the site is unofficial; reword to neutral information ("Storage is low compared with capacity. Follow guidance from your local water authority.") and keep the disclaimer next to it.
8. **Accessibility.** Status is conveyed mostly by colour: add the text label/icon wherever only colour is used (cards, table rows, chart legend). Give the ring gauge and bars `role="img"` / `role="progressbar"` with `aria-valuenow` and a text alternative; add `aria-label` to charts plus a data-table fallback; check colour contrast of the "Low" orange on white; respect `prefers-reduced-motion`; visible focus styles; mark Marathi text with `lang="mr"`.
9. **`<noscript>`** message explaining that the dashboard needs JavaScript and linking to the WRD bulletin.
10. **SEO / sharing (optional but valuable).** Hash routes (`#/dam/…`) cannot be indexed. At export time also generate `web/dam/<slug>/index.html` stubs with proper `<title>`, meta description, Open Graph tags and a canonical URL that boot into the SPA, plus `sitemap.xml`. Update the page `<title>` on route change. Root `index.html` title still says "Pune Dam Water Storage Analytics" → rename.
11. **Wording.** "Healthy ≥ 50 %" next to "Moderate 25–50 %" will read oddly when a reservoir is at 55 % in May. Consider adding seasonal context (vs last year, later vs a multi-year median for the same date) before using the word "Healthy" in the headline.

**Acceptance.** Lighthouse (accessibility, best-practices) ≥ 90 on the overview page; no console errors with JS disabled/enabled; XSS test passes.

---

### B16 — Tests & documentation &nbsp;`P2`

Add `pytest` and wire it into CI (B12.2). Minimum set:
- `tests/test_parser.py` — saved `pdftotext -layout` outputs (small text fixtures, not PDFs) for: a recent day, `2025-11-12`, `2025-07-11`, an early-2024 day, a day with blank cells. Assert exact parsed values for Koyna, Khadakwasla, Mukane, Totladoh, Tillari and the row counts.
- `tests/test_validate.py` — each rejection reason (`live_missing`, `live_out_of_range`, `pct_mismatch`, `gross_lt_live`, `suspect_default_100`, `date_mismatch`, `unmatched_name`).
- `tests/test_dates.py` — B01 (ingest/export survive dates after 2026-12-31).
- `tests/test_registry.py` — unique slugs, no alias collisions (B07), capacities > 0.
- `tests/test_export.py` — `prev_*` fields present, `null` not `0`, orphan cleanup, deterministic bytes.
- `tests/test_schema.py` — migrations apply twice cleanly (idempotent), `PRAGMA user_version`, no placeholder metadata.
- JS: move pure functions (`computeRegionDelta`, weighted YoY, `getStatusDetails`) to `web/lib.js` and test with Node's built-in runner (`node --test`).

---

## 4. Execution order

| Phase | Goal | Issues | Needs data rebuild? |
|---|---|---|---|
| **0 — Setup** | Branch, backup, deps, baseline | Create branch `fix/review-2026-11`; backup DB; add `scripts/audit_data.py` (Appendix A); run it and save the baseline output | no |
| **1 — Stop the bleeding** (small, safe) | Remove false/misleading output and the 1 Jan 2027 bomb | **B01**, **B02**, **B06**, B04 steps 1-5 (null the placeholders, hide them in UI, fix the "authentic" claim), B12.1 (exit codes), B11 (TLS), B15.1/15.2/15.6/15.7 | no |
| **2 — Data correctness** | Correct parsing + validation + rebuild | **B03**, **B05**, B07, B08.1-2, B09 | **yes** — show the diff report and wait for my OK |
| **3 — Schema & facts** | Clean schema v2; real metadata | B10, B04 steps 6-7, B08.3-5 | yes (rebuild into v2) |
| **4 — Pipeline & repo** | Reliable CI, lean repo | B12 (rest), B13, B14 | no |
| **5 — Polish & tests** | Frontend quality, tests, docs | B15 (rest), B16, README | no |

After each phase: run `audit_data.py` and `pytest`, then give me a short report — what changed, before/after audit output, anything that needs my decision.

**Decisions the agent must ask me about (do not guess):**
1. Replacing `pune_dams.db` after seeing the rebuild diff report (Phase 2).
2. Which `LICENSE` to use.
3. Whether to rewrite git history to purge old binaries (default: **no**).
4. Slug mapping for orphan history files when the correct current dam is not obvious (B07).
5. Photo policy: which verified, licensed photos may be used (B04).
6. Whether to keep `systemd/` and daemon mode (B12.9).

---

## 5. Which database? — stay on SQLite

SQLite is the right choice for this workload: ~130k rows today (roughly 500k after ten years), a **single writer**, **one batch write per day**, and a browser that never queries the DB (it reads exported static JSON). Nothing here needs a server database.

Use these SQLite features: `STRICT` tables, `PRAGMA foreign_keys=ON`, WAL mode, `PRAGMA user_version` + numbered migrations (B10), and **do not commit the `.db`** (B13.1).

Reconsider only if requirements change: a **live query API** with concurrent users/writers → PostgreSQL (optionally TimescaleDB); **spatial queries / map analytics** → PostgreSQL + PostGIS (plain lat/long display does not need it); **sub-hourly sensor streams** (inflow/outflow every few minutes) → a time-series store. Keep the schema portable (no SQLite-only tricks beyond `STRICT`) so that move stays easy. Viva line: *"Single-writer, read-mostly workload served as static JSON — SQLite fits; Postgres is the upgrade path for a live query API."*

---

## 6. Definition of done

- [ ] `python scripts/audit_data.py` → **0 hard failures**; every baseline in Appendix A is resolved or explained.
- [ ] `pytest` and `node --test` pass locally and in CI.
- [ ] Headline card delta matches the DB (Pune, 11→12 Nov 2026 ≈ −0.30 pp / −37,710 ML before any rebuild corrections).
- [ ] Koyna (2,835.5 MCM capacity) on 2025-11-12 shows ≈ 2,774 MCM, not 100.0.
- [ ] No dam page shows invented height/length/year/photo; null → "—".
- [ ] Tillari is one dam with continuous history to the latest day; 0 dams missing on the latest day (or the missing dam is explained).
- [ ] About page statistics come from `meta.json`; no "continuous/consecutive/authentic" claims that the data does not support; coverage gaps listed.
- [ ] Ingest/export survive dates after 2026-12-31 (test).
- [ ] A deliberately broken scrape turns the Actions job red and commits nothing.
- [ ] Fresh clone: `pip install -r requirements.txt && python -m dam_tracker build-db` works; tracked repo has no binaries/dumps.
- [ ] README describes the real pipeline, caveats, and how to run the audit and tests.

---

## Appendix A — `scripts/audit_data.py` (tested against `68358f9`; reproduces every baseline above)

Create this file as `scripts/audit_data.py`. Exit code `1` on any hard failure, so CI can use it as a gate. Expected output on the **current** DB: 6 hard failures (the `[FAIL]` lines) — that is the baseline to drive to zero.

```python
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
```

Baseline output on commit `68358f9`:

```text
139 dams, 130,154 rows, 2024-01-01 -> 2026-11-12
[FAIL] rows with live_storage_mcm == 100.0 placeholder   (baseline 3241): 3241
[FAIL] rows where pct disagrees with live/design >2pp    (baseline 6407): 6407
[FAIL] rows with last_year_pct == 0 (should be NULL)     (baseline 5336): 5336
[WARN] rows with live == design exactly (clamp suspects) (baseline 11655): 11655
[FAIL] dams with placeholder 45 m / 1200 m               (baseline 87): 87
[FAIL] dams with placeholder year 1985                   (baseline ~87): 87
[WARN] calendar gaps between first and last day          (baseline 1: 2026-11-07): 1
[WARN] days reporting <135 dams                          (baseline 264): 264
[FAIL] dams missing on the latest day                    (baseline 1: tillari): 1
[WARN] capacity-identical dam pairs (possible duplicates)(baseline 2): 2
[WARN] legacy tables present                             (baseline 3): 3
HARD FAILURES: 6
```

After Phase 3 (schema v2) the table/column names in the script change (`storage_pct` and `last_year_pct` move to the view `vw_dam_daily`); update the queries to read from the view and keep the same checks.

---

## Appendix B — Hardened daily workflow (starting point)

```yaml
name: Daily Maharashtra Dam Storage Tracker

on:
  schedule:
    - cron: '30 3 * * *'     # 09:00 IST
    - cron: '30 9 * * *'     # 15:00 IST (re-check for late bulletins)
  workflow_dispatch:

permissions:
  contents: write
  issues: write

concurrency:
  group: dam-data-update
  cancel-in-progress: false

jobs:
  update:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - run: sudo apt-get update && sudo apt-get install -y poppler-utils
      - run: pip install -r requirements.txt

      - name: Build DB from seed CSV, fetch new bulletins, ingest, export
        run: python -m dam_tracker daily --fill-missing --max-days 30   # non-zero exit on any gate failure

      - name: Gate (must pass before anything is committed)
        run: |
          pytest -q
          python scripts/audit_data.py

      - name: Commit data
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add database/seed/dam_daily_logs.csv web/data
          if git diff --staged --quiet; then
            echo "No data changes."
          else
            git commit -m "data: update dam storage [$(date -u +%F)]"
            git pull --rebase
            git push
          fi

      - name: Open issue on failure
        if: failure()
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh issue create --title "Daily dam update failed ($(date -u +%F))" \
            --body "Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" || true
```

Adapt the `python -m dam_tracker …` command to whatever entrypoint exists at that point (before the B13 refactor use `python scraper/daily_dam_worker.py --once …`, which must exit non-zero on failure — B12.1).

---

## Appendix C — Quick reference of files/lines touched

| File | Lines (commit `68358f9`) | Issue |
|---|---|---|
| `database/db_manager.py` | ~L22-45 drop-on-legacy; L189 year<2024; L200-212 defaults/cap; L259-267 purge; L327-343 fake fallbacks; L385 date cap | B01, B03, B04, B05, B10 |
| `scraper/fetch_dam_data.py` | L18-20 TLS off; L60-63 registry defaults; L167-170, L254-260 date from filename; L213-219 name→slug fallback; L227-251 positional parse + clamps | B03, B05, B08, B11 |
| `scraper/daily_dam_worker.py` | `run_daily_job` swallows exceptions; `--once` ignores return value | B12 |
| `scripts/enrich_dam_metadata.py` | L17-22 default images; L110-116 placeholder defaults | B04 |
| `database/dam_registry.json` | duplicate `tillari` entries; `mangrul-h-l-b`, `rajatakli-h-l-b` capacities | B07 |
| `web/app.js` | L180-209 fetch/cache-bust; L355-367 YoY avg; L397-401 hardcoded delta; L426-446 bars/advisory; L500/573/1097/1150 `Number(x) \|\| 0` fallbacks; L523-533, 701, 1105, 1325-1334 unescaped HTML; L820-826 history fetch | B02, B06, B14, B15 |
| `web/index.html` | L20 CDN; L169 static delta; L396 "0 reservoirs"; L579 loading text; L624 wiki link; L811, L815 claims; L822-837 hardcoded stats | B02, B04, B08, B15 |
| `.github/workflows/*.yml` | daily: no concurrency/gates; backfill: stale paths, MySQL | B12 |
| `.gitignore` | `HydroAnalytics.pptx/` pattern; missing `*.db` | B13 |
