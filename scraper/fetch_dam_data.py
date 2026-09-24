import os
import re
import ssl
import sys
import subprocess
import urllib.request
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

MARATHI_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Dam Name Translation Map for English UI Standard
DAM_NAME_EN_MAP = {
    'खडकवासला': 'Khadakwasla',
    'पानशेत': 'Panshet',
    'मुळशी': 'Mulshi',
    'गुंजवणी': 'Gunjawani',
    'टेमघर': 'Temghar',
    'कोयना': 'Koyna',
    'उजनी': 'Ujani',
    'भातासा': 'Bhatsa',
    'भातसा': 'Bhatsa',
    'जयकवाडी': 'Paithan (Jayakwadi)',
    'पैठण': 'Paithan (Jayakwadi)',
    'तोतलाडोह': 'Totladoh',
    'गोसीखद': 'Gosikhurd',
    'बावनथडी': 'Bawanthadi',
    'भांडारदरा': 'Bhandardara',
    'निळवंडे': 'Nilwande',
    'मुळा': 'Mula',
    'वरसगाव': 'Varasgaon',
    'चासकमान': 'Chaskaman',
    'डिंभे': 'Dimbhe',
    'वीर': 'Veer',
    'दूधगंगा': 'Dudhganga',
    'राधानगरी': 'Radhanagari'
}

def get_pdf_text(pdf_path):
    """Extract text from PDF using pdftotext CLI, pypdf, or pdfplumber."""
    try:
        res = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    if HAS_PYPDF:
        try:
            reader = pypdf.PdfReader(pdf_path)
            text = "".join(page.extract_text() or "" for page in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass

    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "".join((page.extract_text() or "") + "\n" for page in pdf.pages)
                if text.strip():
                    return text
        except Exception:
            pass

    return ""

def parse_dam_line(line, default_date=""):
    """Parses a single line containing dam storage data from English or Marathi PDF."""
    line_trans = line.translate(MARATHI_DIGITS)
    tokens = line_trans.split()
    
    date_idx = -1
    for i, t in enumerate(tokens):
        if re.match(r'^\d{2}/\d{2}/\d{4}$', t):
            date_idx = i
            break

    if date_idx >= 1 and len(tokens) >= date_idx + 7:
        name_tokens = [t for t in tokens[:date_idx] if not re.match(r'^\d+$', t)]
        raw_dam_name = ' '.join(name_tokens).strip()
        if not raw_dam_name:
            raw_dam_name = tokens[date_idx - 1]
            
        dam_name = DAM_NAME_EN_MAP.get(raw_dam_name, raw_dam_name)
        report_date = tokens[date_idx]
        
        report_time = tokens[date_idx+1]
        if date_idx + 2 < len(tokens) and tokens[date_idx+2] in ['स.', 'वा.', 'AM', 'PM', 'am', 'pm']:
            report_time += ' ' + tokens[date_idx+2]
            idx_offset = date_idx + 3
        else:
            idx_offset = date_idx + 2
            
        if len(tokens) >= idx_offset + 6:
            dead = tokens[idx_offset]
            design_live = tokens[idx_offset+1]
            design_gross = tokens[idx_offset+2]
            current_live = tokens[idx_offset+3]
            current_gross = tokens[idx_offset+4]
            current_pct_raw = tokens[idx_offset+5].replace('%', '')
            
            last_year_pct = "0"
            if len(tokens) > idx_offset + 6:
                for tok in tokens[idx_offset+6:]:
                    cleaned = tok.replace('%', '')
                    if re.match(r'^\d+(\.\d+)?$', cleaned):
                        last_year_pct = cleaned
                        break

            dead_val = float(dead) if re.match(r'^\d+(\.\d+)?$', dead) else 0.0
            design_live_val = float(design_live) if re.match(r'^\d+(\.\d+)?$', design_live) else 0.0
            design_gross_val = float(design_gross) if re.match(r'^\d+(\.\d+)?$', design_gross) else 0.0
            current_live_val = float(current_live) if re.match(r'^\d+(\.\d+)?$', current_live) else 0.0
            current_gross_val = float(current_gross) if re.match(r'^\d+(\.\d+)?$', current_gross) else 0.0
            
            if re.match(r'^\d+(\.\d+)?$', current_pct_raw) and float(current_pct_raw) > 0:
                current_pct_val = float(current_pct_raw)
            elif design_live_val > 0 and current_live_val >= 0:
                current_pct_val = round((current_live_val / design_live_val) * 100, 2)
            else:
                current_pct_val = 0.0

            return {
                'Dam Name': dam_name,
                'Report Date': report_date,
                'Report Time': report_time,
                'Dead Storage (MCM)': dead_val,
                'Design Live Storage (MCM)': design_live_val,
                'Design Gross Storage (MCM)': design_gross_val,
                'Current Live Storage (MCM)': current_live_val,
                'Current Gross Storage (MCM)': current_gross_val,
                'Current Live Storage (%)': current_pct_val,
                'Last Year Storage (%)': float(last_year_pct) if re.match(r'^\d+(\.\d+)?$', last_year_pct) else 0.0,
                'Status': 'Success'
            }
    return None

def extract_all_dams_from_pdf(pdf_path, dt_str):
    """Extracts storage metrics for all dams in Maharashtra from a single PDF."""
    results = []
    if not pdf_path or not os.path.exists(pdf_path):
        return results

    text = get_pdf_text(pdf_path)
    lines = text.split('\n')
    
    for line in lines:
        parsed = parse_dam_line(line, default_date=dt_str)
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
        print(f"📁 Organized {moved_count} existing flat PDFs into YYYY/MM subfolders.")

def download_pdf_for_date(date_obj, pdf_dir):
    """Downloads daily PDF for given date into pdf_dir/YYYY/MM/report_DD-MM-YYYY.pdf."""
    dt_str = date_obj.strftime('%d-%m-%Y')
    year_str = date_obj.strftime('%Y')
    month_str = date_obj.strftime('%m')
    
    if date_obj.year < 2024:
        return dt_str, None, False

    sub_dir = os.path.join(pdf_dir, year_str, month_str)
    os.makedirs(sub_dir, exist_ok=True)
    
    dest_path = os.path.join(sub_dir, f"report_{dt_str}.pdf")
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return dt_str, dest_path, True

    base_url = 'https://wrd.maharashtra.gov.in/Upload/PDF/'
    patterns = [
        "Today's-Storage-ReportEng-{date}.pdf",
        "Today's Storage ReportEng-{date}.pdf",
        "Today-Storage-ReportEng-{date}.pdf",
        "Today's-Storage-ReportMarathi-{date}.pdf",
        "Today's Storage ReportMarathi-{date}.pdf",
        "Today's-Storage-Report-{date}.pdf"
    ]

    for pat in patterns:
        filename = pat.format(date=dt_str)
        url = base_url + urllib.parse.quote(filename)
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=10) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(dest_path, 'wb') as f:
                        f.write(data)
                    return dt_str, dest_path, True
        except Exception:
            continue

    return dt_str, None, False

def fetch_multi_dam_data(days=365, pdf_dir='dam_pdfs', max_download_workers=15, max_extract_workers=16):
    """Downloads PDFs for date range and extracts data for ALL state dams."""
    os.makedirs(pdf_dir, exist_ok=True)
    organize_existing_pdfs(pdf_dir)
    today = datetime.now()
    dates = [today - timedelta(days=i) for i in range(days)]
    
    print(f"[*] Starting download & state-wide extraction across {days} requested dates...")
    
    pdf_files = {}
    with ThreadPoolExecutor(max_workers=max_download_workers) as executor:
        futures = {executor.submit(download_pdf_for_date, d, pdf_dir): d for d in dates}
        for future in as_completed(futures):
            dt_str, pdf_path, success = future.result()
            if success:
                pdf_files[dt_str] = pdf_path

    print(f"[*] Downloaded/Cached {len(pdf_files)} PDF reports out of {days} requested dates.")
    
    valid_dates = [d for d in dates if pdf_files.get(d.strftime('%d-%m-%Y'))]
    print(f"[*] Parsing all Maharashtra state dams from {len(valid_dates)} available PDF reports in parallel...")

    all_records = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max_extract_workers) as executor:
        futures = {executor.submit(extract_all_dams_from_pdf, pdf_files[d.strftime('%d-%m-%Y')], d.strftime('%d/%m/%Y')): d for d in valid_dates}
        for future in as_completed(futures):
            dam_results = future.result()
            for rec in dam_results:
                all_records.append(rec)
            completed += 1
            if completed % 100 == 0 or completed == len(valid_dates):
                print(f"    -> Progress: [{completed}/{len(valid_dates)}] PDF reports processed.")

    df = pd.DataFrame(all_records)
    
    if not df.empty and 'Report Date' in df.columns:
        df['SortDate'] = df['Report Date'].apply(lambda x: datetime.strptime(str(x), '%d/%m/%Y') if re.match(r'\d{2}/\d{2}/\d{4}', str(x)) else datetime.min)
        df = df.sort_values(by=['SortDate', 'Dam Name'], ascending=[False, True]).drop(columns=['SortDate'])
    
    return df

def save_to_files(df):
    """
    Ingests scraped state records into SQLite relational DBMS ('pune_dams.db') via UPSERT,
    and exports the complete database back to JSON for the web dashboard.
    """
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
    if db_dir not in sys.path:
        sys.path.append(db_dir)
    import db_manager

    db_manager.init_db()

    if not df.empty and 'Dam Name' in df.columns:
        db_manager.ingest_records_from_dataframe(df)

    db_manager.export_db_to_json()

if __name__ == '__main__':
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass

    df = fetch_multi_dam_data(days=days)
    save_to_files(df)
