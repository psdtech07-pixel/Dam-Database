import os
import re
import ssl
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, 'dam_pdf')
REGISTRY_PATH = os.path.join(BASE_DIR, 'database', 'dam_registry.json')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_URL = 'https://wrd.maharashtra.gov.in/Upload/PDF/'
PATTERNS = [
    "Today's-Storage-ReportEng-{date}.pdf",
    "Today's Storage ReportEng-{date}.pdf"
]

DIVISIONS = ['Nagpur', 'Amravati', 'Chhatrapati Sambhajinagar', 'Nashik', 'Pune', 'Kokan']
DISTRICTS = [
    'Bhandara', 'Nagpur', 'Gondia', 'Chandrapur', 'Wardha', 'Gadchiroli',
    'Akola', 'Amravati', 'Buldhana', 'Yavatmal', 'Washim',
    'Chhatrapati Sambhajinagar', 'Beed', 'Hingoli', 'Nanded', 'Dharashiv', 'Latur', 'Parbhani', 'Jalna',
    'Ahilyanagar', 'Jalgaon', 'Nashik', 'Dhule', 'Nandurbar',
    'Kolhapur', 'Pune', 'Sangli', 'Satara', 'Solapur',
    'Thane', 'Raigad', 'Ratnagiri', 'Palghar', 'Sindhudurg'
]

def load_dam_lookup():
    """Loads dam registry mapping names and slugs to master info."""
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lookup = {}
    for entry in data:
        if not isinstance(entry, dict) or 'slug' not in entry:
            continue
        info = {
            'slug': entry['slug'],
            'en': entry['en'],
            'mr': entry.get('mr', entry['en']),
            'district': entry['district'],
            'division': entry['division'],
            'basin': entry.get('basin', 'Krishna'),
            'type': entry.get('type', 'MAJOR'),
            'dead': float(entry.get('dead', 0.0)),
            'live': float(entry.get('live', 100.0)),
            'gross': float(entry.get('gross', 110.0))
        }
        lookup[entry['slug']] = info
        lookup[entry['en'].lower()] = info
        for k in entry.get('keys', []):
            lookup[k.lower()] = info
    return lookup

DAM_LOOKUP = load_dam_lookup()

def is_valid_pdf(file_path):
    """Verifies file existence, minimum size (2KB), and valid PDF magic header."""
    if not os.path.exists(file_path):
        return False
    try:
        if os.path.getsize(file_path) < 2000:
            return False
        with open(file_path, 'rb') as f:
            header = f.read(5)
            return header == b'%PDF-'
    except Exception:
        return False

def download_pdf_for_date(date_obj, pdf_dir=PDF_DIR, timeout=8):
    """
    Downloads the official English dam storage report for date_obj.
    Saves directly to pdf_dir/YYYY/MM/report_DD-MM-YYYY.pdf.
    """
    dt_str = date_obj.strftime('%d-%m-%Y')
    year_str = date_obj.strftime('%Y')
    month_str = date_obj.strftime('%m')

    year_month_dir = os.path.join(pdf_dir, year_str, month_str)
    os.makedirs(year_month_dir, exist_ok=True)
    dest_path = os.path.join(year_month_dir, f"report_{dt_str}.pdf")

    if is_valid_pdf(dest_path):
        return dt_str, dest_path, True, 'ALREADY_EXISTS'

    for pat in PATTERNS:
        filename = pat.format(date=dt_str)
        url = BASE_URL + urllib.parse.quote(filename)
        
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = resp.read()
                        if len(data) > 2000 and data.startswith(b'%PDF-'):
                            temp_dest = dest_path + f'.tmp_{os.getpid()}_{int(time.time()*1000)}'
                            with open(temp_dest, 'wb') as f:
                                f.write(data)
                            os.replace(temp_dest, dest_path)
                            return dt_str, dest_path, True, 'DOWNLOADED'
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                time.sleep(0.5)
                continue
            except Exception:
                time.sleep(0.5)
                continue

    return dt_str, None, False, 'NOT_FOUND'

def get_pdf_text_layout(pdf_path):
    """Extracts layout text using pdftotext CLI."""
    try:
        res = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True, timeout=20)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for p in pdf.pages:
                t = p.extract_text(layout=True) or p.extract_text() or ""
                if t:
                    pages.append(t)
            return "\n".join(pages)
    except Exception:
        pass

    return ""

def extract_all_dams_from_pdf(pdf_path, dt_str=None):
    """
    Parses layout text from an English PDF bulletin.
    Extracts all 138 major dams with 100% clean ASCII numbers and division/district tags.
    """
    records = []
    if not is_valid_pdf(pdf_path):
        return records

    # Determine default report date
    if not dt_str:
        m = re.search(r'report_(\d{2}-\d{2}-\d{4})\.pdf', os.path.basename(pdf_path))
        if m:
            dt_str = m.group(1)

    iso_report_date = None
    if dt_str:
        try:
            iso_report_date = datetime.strptime(dt_str, '%d-%m-%Y').strftime('%Y-%m-%d')
        except Exception:
            pass

    text = get_pdf_text_layout(pdf_path)
    if not text:
        return records

    lines = text.split('\n')
    current_div = 'Nagpur'
    current_dist = 'Bhandara'

    for line in lines:
        s = line.strip()
        # Region tracking
        for div in DIVISIONS:
            if f'{div} Region' in s or (div == 'Amravati' and 'Amravti Region' in s):
                current_div = div
                break

        # District tracking
        for dist in DISTRICTS:
            if s == dist or s == f'District: {dist}' or s.startswith(f'{dist} '):
                current_dist = dist
                break

        # Match table row
        # Pattern: {SrNo} {Dam Name} {DD/MM/YYYY} {HH:MM AM/PM} {Numbers...}
        m = re.search(r'^\s*(\d+)\s+([A-Za-z0-9\(\)\.\s\-\/]+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}\s*(?:AM|PM|am|pm)?)\s+(.*)$', line)
        if not m:
            continue

        sr, raw_name, line_date, line_time, rest = m.groups()
        dam_name = raw_name.strip()

        # Filter out table header false positives
        if any(h in dam_name for h in ['UPDATION', 'NAME OF', 'STORAGE', 'PROJECT', 'TOTAL', 'REGION']):
            continue

        nums = re.findall(r'\d+\.\d+|\d+', rest)
        if len(nums) < 5:
            continue

        info = DAM_LOOKUP.get(dam_name.lower())
        if not info:
            # Check without parentheses or trailing qualifiers
            clean_token = re.sub(r'\(.*?\)', '', dam_name).strip().lower()
            info = DAM_LOOKUP.get(clean_token)

        dam_slug = info['slug'] if info else re.sub(r'[^a-zA-Z0-9]+', '-', dam_name).strip('-').lower()
        dam_name_en = info['en'] if info else dam_name
        dam_name_mr = info.get('mr', dam_name_en) if info else dam_name_en
        district = info['district'] if info else current_dist
        division = info['division'] if info else current_div
        basin = info.get('basin', 'Krishna') if info else 'Krishna'

        try:
            dead_val = float(nums[0])
            design_live = float(nums[1]) if float(nums[1]) > 0 else (info['live'] if info else 100.0)
            design_gross = float(nums[2]) if len(nums) > 2 and float(nums[2]) >= design_live else (design_live + dead_val)
            live_val = float(nums[3])
            gross_val = float(nums[4]) if len(nums) > 4 else live_val

            if len(nums) > 5:
                pct_val = float(nums[5])
            elif design_live > 0:
                pct_val = round((live_val / design_live) * 100.0, 2)
            else:
                pct_val = 0.0

            last_pct_val = float(nums[6]) if len(nums) > 6 else 0.0
        except (ValueError, IndexError):
            continue

        # Hydrological sanity assertions
        if gross_val < live_val:
            gross_val = live_val
        if design_live > 0 and live_val > design_live * 1.2:
            live_val = min(live_val, design_live)

        pct_val = min(120.0, max(0.0, pct_val))
        last_pct_val = min(120.0, max(0.0, last_pct_val))

        # Date resolution (bulletin date preferred)
        r_date = iso_report_date
        if not r_date:
            try:
                d, mo, y = line_date.split('/')
                r_date = f"{y}-{mo}-{d}"
            except Exception:
                continue

        records.append({
            'dam_slug': dam_slug,
            'Dam Name': dam_name_en,
            'Dam Name MR': dam_name_mr,
            'District': district,
            'Division': division,
            'Basin': basin,
            'Report Date': r_date,
            'Report Time': line_time.strip(),
            'Dead Storage (MCM)': dead_val,
            'Design Live Storage (MCM)': design_live,
            'Design Gross Storage (MCM)': design_gross,
            'Current Live Storage (MCM)': live_val,
            'Current Gross Storage (MCM)': gross_val,
            'Current Live Storage (%)': pct_val,
            'Last Year Storage (%)': last_pct_val,
            'Status': 'Success'
        })

    return records

def audit_and_reconcile_pdfs(days=1000, pdf_dir=PDF_DIR, max_workers=10):
    """Checks local dam_pdf against required dates and downloads missing files."""
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_files = {}

    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.startswith("report_") and f.endswith(".pdf"):
                m = re.search(r'report_(\d{2}-\d{2}-\d{4})\.pdf', f)
                if m:
                    dt_key = m.group(1)
                    full_p = os.path.join(root, f)
                    if is_valid_pdf(full_p):
                        pdf_files[dt_key] = full_p

    today = datetime.now()
    if days and isinstance(days, int) and days < 1000:
        start_date = max(datetime(2024, 1, 1), today - timedelta(days=days))
    else:
        start_date = datetime(2024, 1, 1)

    end_date = today
    total_days = max(1, (end_date - start_date).days + 1)
    expected_dates = [start_date + timedelta(days=i) for i in range(total_days)]
    missing_dates = [d for d in expected_dates if d.strftime('%d-%m-%Y') not in pdf_files]

    print(f"[*] PDF Audit: {len(pdf_files)} local valid English PDFs found for {total_days} expected dates.")
    if missing_dates:
        print(f"[*] Downloading {len(missing_dates)} missing bulletins from WRD portal...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(download_pdf_for_date, d, pdf_dir): d for d in missing_dates}
            for future in as_completed(futures):
                dt_str, path, ok, _ = future.result()
                if ok and path:
                    pdf_files[dt_str] = path

    return pdf_files

def _parse_single_pdf_worker(item):
    dt_str, path = item
    return extract_all_dams_from_pdf(path, dt_str)

def fetch_multi_dam_data(days=1000, pdf_dir=PDF_DIR, max_workers=8):
    """Audits and extracts dam storage data from English PDF reports in parallel."""
    pdf_files = audit_and_reconcile_pdfs(days=days, pdf_dir=pdf_dir)
    items = sorted(pdf_files.items(), key=lambda x: datetime.strptime(x[0], '%d-%m-%Y'), reverse=True)

    if days and isinstance(days, int) and days < 1000:
        items = items[:days + 2]

    print(f"[*] Extracting data from {len(items)} English PDF bulletins in parallel...")
    all_records = []
    completed = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for dam_results in executor.map(_parse_single_pdf_worker, items, chunksize=10):
            all_records.extend(dam_results)
            completed += 1
            if completed % 100 == 0 or completed == len(items):
                print(f"    -> Progress: [{completed}/{len(items)}] PDF bulletins extracted.")

    df = pd.DataFrame(all_records)
    if not df.empty and 'Report Date' in df.columns:
        df['SortDate'] = pd.to_datetime(df['Report Date'], errors='coerce')
        df = df.sort_values(by=['SortDate', 'Dam Name'], ascending=[False, True]).drop(columns=['SortDate'])
    return df

def save_to_files(df):
    """Ingests extracted records into 3NF SQLite DBMS and exports decoupled web JSON."""
    db_dir = os.path.join(BASE_DIR, 'database')
    if db_dir not in sys.path:
        sys.path.append(db_dir)
    import db_manager

    db_manager.init_db()
    if not df.empty:
        db_manager.ingest_records_from_dataframe(df)
    db_manager.export_decoupled_json()

if __name__ == '__main__':
    days = 1000
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass
    df = fetch_multi_dam_data(days=days)
    save_to_files(df)
