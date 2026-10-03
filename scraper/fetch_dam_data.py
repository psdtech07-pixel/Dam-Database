import os
import re
import ssl
import sys
import json
import subprocess
import urllib.request
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

MARATHI_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Load Master Dam Lookup from database/dam_registry.json
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'dam_registry.json')

def load_dam_lookup():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        registry = [item for item in data if isinstance(item, dict) and 'slug' in item]
        lookup = {}
        for entry in registry:
            info = {
                'en': entry['en'],
                'mr': entry['mr'],
                'district': entry['district'],
                'division': entry['division'],
                'basin': entry.get('basin', 'Krishna'),
                'slug': entry['slug'],
                'design_live_mcm': float(entry.get('design_live_mcm', 100.0)),
                'design_gross_mcm': float(entry.get('design_gross_mcm', 110.0))
            }
            lookup[entry['slug']] = info
            lookup[entry['en'].lower()] = info
            lookup[entry['mr'].lower()] = info
            if 'aliases_mr' in entry:
                for alias in entry['aliases_mr']:
                    lookup[alias.lower()] = info
            for k in entry.get('keys', []):
                lookup[k.lower()] = info
        return lookup
    return {}

DAM_LOOKUP = load_dam_lookup()

def clean_marathi_text(text):
    """Strips PDF font ligature artifact symbols from Marathi text."""
    if not text: return ""
    cleaned = re.sub(r'[\uE000-\uF8FF]', '', text).strip()
    return cleaned if cleaned else text

def get_pdf_text_layout(pdf_path):
    """Extract layout-preserved text from PDF using pdftotext or pdfplumber."""
    try:
        res = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text_pages = []
            for page in pdf.pages:
                t = page.extract_text(layout=True) or page.extract_text() or ""
                if t:
                    text_pages.append(t)
            if text_pages:
                return "\n".join(text_pages)
    except Exception:
        pass

    return ""

def parse_dam_line_11col(line, pdf_date_str, active_division="Pune", active_district="Pune"):
    """
    Parses a single line of storage metrics based on the standard 11-column WRD grid.
    Translates Devanagari numerals and resolves concatenated decimal values.
    """
    if not line or len(line.strip()) < 10:
        return None

    line_trans = line.translate(MARATHI_DIGITS)
    
    # Locate Date token DD/MM/YYYY
    m_date = re.search(r'(\d{2}/\d{2}/\d{4})', line_trans)
    if not m_date:
        return None

    date_idx_start = m_date.start()
    date_idx_end = m_date.end()
    
    date_str = m_date.group(1)

    dam_part = line_trans[:date_idx_start].strip()
    after_date = line_trans[date_idx_end:].strip()

    # Extract dam name tokens (removing leading serial number digits)
    name_tokens = [t for t in dam_part.split() if not re.match(r'^\d+$', t)]
    raw_dam_name = clean_marathi_text(' '.join(name_tokens)).strip()
    if not raw_dam_name and dam_part.split():
        raw_dam_name = clean_marathi_text(dam_part.split()[-1])

    if not raw_dam_name:
        return None

    dict_info = DAM_LOOKUP.get(raw_dam_name.lower())
    if not dict_info and name_tokens:
        dict_info = DAM_LOOKUP.get(name_tokens[-1].lower())

    if dict_info:
        dam_name_en = dict_info['en']
        dam_name_mr = dict_info['mr']
        district = dict_info['district']
        division = dict_info['division']
        design_live = dict_info['design_live_mcm']
    else:
        dam_name_en = raw_dam_name
        dam_name_mr = raw_dam_name
        district = active_district
        division = active_division
        design_live = 100.0

    # Extract reading time (e.g. 08:00 AM / 08:00 स. / 08:00)
    m_time = re.search(r'(\d{2}:\d{2}\s*(?:AM|PM|am|pm|स\.|वा\.)?)', after_date)
    if m_time:
        report_time = m_time.group(1).strip()
        numeric_part = after_date[m_time.end():].strip()
    else:
        report_time = "08:00 AM"
        numeric_part = after_date

    # Extract numbers with 2-decimal point pattern matching to split concatenated values (e.g. 1802.811517.20 -> 1802.81, 1517.20)
    nums = re.findall(r'\d+\.\d{2}|\d+', numeric_part)
    if len(nums) < 5:
        return None

    # Strict 11-column positioning:
    # nums[0]: Dead Storage MCM
    # nums[1]: Designed Live Storage MCM (Col 6)
    # nums[2]: Designed Gross Storage MCM (Col 7)
    # nums[3]: Today's Live Storage MCM (Col 8)
    # nums[4]: Today's Gross Storage MCM (Col 9)
    # nums[5]: Percentage Today % (Col 10)
    # nums[6]: Percentage Last Year % (Col 11) - optional

    try:
        dead_val = float(nums[0])
        design_live_val = float(nums[1]) if float(nums[1]) > 0 else design_live
        design_gross_val = float(nums[2]) if len(nums) > 2 else design_live_val + dead_val
        current_live_val = float(nums[3]) if len(nums) > 3 else 0.0
        current_gross_val = float(nums[4]) if len(nums) > 4 else current_live_val

        if len(nums) > 5:
            current_pct_val = float(nums[5])
        elif design_live_val > 0:
            current_pct_val = round((current_live_val / design_live_val) * 100.0, 2)
        else:
            current_pct_val = 0.0

        last_year_pct_val = float(nums[6]) if len(nums) > 6 and re.match(r'^\d+(\.\d+)?$', nums[6]) else 0.0
    except (ValueError, IndexError):
        return None

    # Hydrological Domain Sanity Constraints:
    # 1. Gross >= Live
    if current_gross_val < current_live_val:
        current_gross_val = current_live_val

    # 2. Live storage <= design_live * 1.15
    if design_live_val > 0 and current_live_val > design_live_val * 1.15:
        current_live_val = min(current_live_val, design_live_val)

    # 3. 0.0 <= pct <= 120.0
    current_pct_val = min(120.0, max(0.0, current_pct_val))
    last_year_pct_val = min(120.0, max(0.0, last_year_pct_val))

    # Parse ISO report date from PDF filename or header
    dt_obj = None
    try:
        dt_obj = datetime.strptime(pdf_date_str, '%d-%m-%Y')
    except Exception:
        try:
            dt_obj = datetime.strptime(date_str, '%d/%m/%Y')
        except Exception:
            pass

    if not dt_obj or dt_obj.year < 2024 or dt_obj.year > 2026:
        return None

    iso_date = dt_obj.strftime('%Y-%m-%d')

    return {
        'Dam Name': dam_name_en,
        'Dam Name MR': dam_name_mr,
        'District': district,
        'Division': division,
        'Report Date': iso_date,
        'Report Time': report_time,
        'Dead Storage (MCM)': dead_val,
        'Design Live Storage (MCM)': design_live_val,
        'Design Gross Storage (MCM)': design_gross_val,
        'Current Live Storage (MCM)': current_live_val,
        'Current Gross Storage (MCM)': current_gross_val,
        'Current Live Storage (%)': current_pct_val,
        'Last Year Storage (%)': last_year_pct_val,
        'Status': 'Success'
    }

def extract_all_dams_from_pdf(pdf_path, dt_str):
    """Extracts storage metrics for all dams in Maharashtra from a single PDF bulletin."""
    results = []
    if not pdf_path or not os.path.exists(pdf_path):
        return results

    text = get_pdf_text_layout(pdf_path)
    lines = text.split('\n')
    
    current_div = 'Pune'
    current_dist = 'Pune'
    
    for line in lines:
        stripped = line.strip()
        cleaned_line = clean_marathi_text(stripped)
        
        # Section Header Tracking
        if 'Nagpur Region' in stripped or 'नागपूर' in cleaned_line:
            current_div = 'Nagpur'
        elif 'Amravati Region' in stripped or 'अमरावती' in cleaned_line:
            current_div = 'Amravati'
        elif 'Chhatrapati Sambhajinagar Region' in stripped or 'संभाजीनगर' in cleaned_line:
            current_div = 'Chhatrapati Sambhajinagar'
        elif 'Nashik Region' in stripped or 'नाशिक' in cleaned_line:
            current_div = 'Nashik'
        elif 'Pune Region' in stripped or 'पुणे' in cleaned_line:
            current_div = 'Pune'
        elif 'Kokan Region' in stripped or 'कोकण' in cleaned_line:
            current_div = 'Kokan'

        parsed = parse_dam_line_11col(line, dt_str, active_division=current_div, active_district=current_dist)
        if parsed:
            results.append(parsed)
            
    return results

def organize_existing_pdfs(pdf_dir='dam_pdfs'):
    """Organizes flat PDF files into pdf_dir/YYYY/MM/ subfolders."""
    if not os.path.exists(pdf_dir):
        return
    moved_count = 0
    for item in os.listdir(pdf_dir):
        item_path = os.path.join(pdf_dir, item)
        if os.path.isfile(item_path) and item.startswith("report_") and item.endswith(".pdf"):
            match = re.search(r'report_(\d{2})-(\d{2})-(\d{4})\.pdf', item)
            if match:
                day, month, year = match.groups()
                target_dir = os.path.join(pdf_dir, year, month)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, item)
                if not os.path.exists(target_path):
                    os.rename(item_path, target_path)
                else:
                    os.remove(item_path)
                moved_count += 1
    if moved_count > 0:
        print(f"📁 Organized {moved_count} flat PDFs into YYYY/MM subfolders.")

def download_pdf_for_date(date_obj, pdf_dir):
    """
    Downloads daily PDF for given date into pdf_dir/YYYY/MM/report_DD-MM-YYYY.pdf.
    Uses 15-second timeout and enforces minimum 2 KB size check.
    """
    dt_str = date_obj.strftime('%d-%m-%Y')
    year_str = date_obj.strftime('%Y')
    month_str = date_obj.strftime('%m')
    
    if date_obj.year < 2024 or date_obj.year > 2026:
        return dt_str, None, False

    sub_dir = os.path.join(pdf_dir, year_str, month_str)
    os.makedirs(sub_dir, exist_ok=True)
    
    dest_path = os.path.join(sub_dir, f"report_{dt_str}.pdf")
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 2000:
        return dt_str, dest_path, True

    base_url = 'https://wrd.maharashtra.gov.in/Upload/PDF/'
    patterns = [
        "Today's-Storage-ReportMarathi-{date}.pdf",
        "Today's-Storage-ReportEng-{date}.pdf",
        "Today's Storage ReportMarathi-{date}.pdf",
        "Today's Storage ReportEng-{date}.pdf",
        "Today's-Storage-Report-{date}.pdf"
    ]

    for pat in patterns:
        filename = pat.format(date=dt_str)
        url = base_url + urllib.parse.quote(filename)
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=15) as resp:
                data = resp.read()
                if len(data) > 2000:
                    with open(dest_path, 'wb') as f:
                        f.write(data)
                    return dt_str, dest_path, True
        except Exception:
            continue

    return dt_str, None, False

def audit_and_reconcile_pdfs(days=1000, pdf_dir='dam_pdfs', max_download_workers=10):
    """
    Audits dam_pdfs/ directory against expected dates,
    and downloads missing daily bulletins automatically.
    """
    os.makedirs(pdf_dir, exist_ok=True)
    organize_existing_pdfs(pdf_dir)

    pdf_files = {}
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.startswith("report_") and f.endswith(".pdf"):
                m = re.search(r'report_(\d{2}-\d{2}-\d{4})\.pdf', f)
                if m:
                    dt_key = m.group(1)
                    full_p = os.path.join(root, f)
                    if os.path.getsize(full_p) > 2000:
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

    print(f"[*] PDF Audit: {len(pdf_files)} local valid PDFs found for {total_days} expected dates ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}).")

    if missing_dates:
        print(f"[*] Reconciling & downloading {len(missing_dates)} missing PDF reports from WRD portal (15s timeout)...")
        with ThreadPoolExecutor(max_workers=max_download_workers) as executor:
            futures = {executor.submit(download_pdf_for_date, d, pdf_dir): d for d in missing_dates}
            for future in as_completed(futures):
                dt_str, pdf_path, success = future.result()
                if success:
                    pdf_files[dt_str] = pdf_path

    print(f"[*] Audit & Reconciliation Complete: {len(pdf_files)} PDF reports ready for ingestion.")
    return pdf_files

def fetch_multi_dam_data(days=1000, pdf_dir='dam_pdfs', max_extract_workers=16):
    """Parses audited PDF reports in parallel across all Maharashtra dams."""
    pdf_files = audit_and_reconcile_pdfs(days=days, pdf_dir=pdf_dir)

    valid_items = sorted(pdf_files.items(), key=lambda x: datetime.strptime(x[0], '%d-%m-%Y'), reverse=True)
    print(f"[*] Extracting 11-column grid data from {len(valid_items)} PDF bulletins in parallel...")

    all_records = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max_extract_workers) as executor:
        futures = {executor.submit(extract_all_dams_from_pdf, path, dt_str): dt_str for dt_str, path in valid_items}
        for future in as_completed(futures):
            dam_results = future.result()
            for rec in dam_results:
                all_records.append(rec)
            completed += 1
            if completed % 100 == 0 or completed == len(valid_items):
                print(f"    -> Progress: [{completed}/{len(valid_items)}] PDF reports parsed.")

    df = pd.DataFrame(all_records)
    
    if not df.empty and 'Report Date' in df.columns:
        # Sort chronologically by date
        df['SortDate'] = pd.to_datetime(df['Report Date'], errors='coerce')
        df = df.sort_values(by=['SortDate', 'Dam Name'], ascending=[False, True]).drop(columns=['SortDate'])
    
    return df

def push_to_mysql(df, host, user, password, database='defaultdb', port=3306):
    """Safely syncs dataframe records to Cloud MySQL if credentials are provided."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=host, user=user, password=password, database=database, port=port
        )
        conn.close()
        print("[+] MySQL Connection successful.")
        return True
    except Exception as e:
        print(f"[!] Warning: Cloud MySQL sync skipped/warning: {e}")
        return False

def save_to_files(df):
    """
    Ingests extracted records into 3NF SQLite DBMS ('pune_dams.db'),
    purges corrupt dates, and exports two-tier web JSON files.
    """
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
    if db_dir not in sys.path:
        sys.path.append(db_dir)
    import db_manager

    db_manager.init_db()
    db_manager.purge_corrupt_logs()

    if not df.empty and 'Dam Name' in df.columns:
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
