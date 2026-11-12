import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(BASE_DIR, 'dam_pdf')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_URL = 'https://wrd.maharashtra.gov.in/Upload/PDF/'

# Primary reference URL pattern as provided by user, plus space variation
PATTERNS = [
    "Today's-Storage-ReportEng-{date}.pdf",
    "Today's Storage ReportEng-{date}.pdf"
]

def is_valid_pdf(file_path):
    """Check if file exists, is larger than 2KB, and begins with the PDF magic header."""
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

def download_english_pdf_for_date(dt_obj, base_output_dir=TARGET_DIR, timeout=5):
    """
    Downloads the English PDF for a given date into base_output_dir/YYYY/MM/report_DD-MM-YYYY.pdf.
    Enforces format validation (readable valid PDF only).
    """
    dt_str = dt_obj.strftime('%d-%m-%Y')
    year_str = dt_obj.strftime('%Y')
    month_str = dt_obj.strftime('%m')

    year_month_dir = os.path.join(base_output_dir, year_str, month_str)
    os.makedirs(year_month_dir, exist_ok=True)
    dest_path = os.path.join(year_month_dir, f"report_{dt_str}.pdf")

    # If already downloaded and valid, skip immediately
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
                    # 404 means file doesn't exist under this pattern; do not retry, try next pattern
                    break
                # On 502/503/504 transient gateway errors, short wait and retry once
                time.sleep(0.5)
                continue
            except Exception:
                time.sleep(0.5)
                continue

    return dt_str, None, False, 'NOT_FOUND'

def run_download_all(start_date_str="01-01-2024", end_date_str=None, workers=20):
    """
    Orchestrates the parallel download of English dam storage PDFs for the date range.
    """
    start_dt = datetime.strptime(start_date_str, "%d-%m-%Y")
    if end_date_str:
        end_dt = datetime.strptime(end_date_str, "%d-%m-%Y")
    else:
        end_dt = datetime.now()

    os.makedirs(TARGET_DIR, exist_ok=True)
    total_days = (end_dt - start_dt).days + 1
    dates = [start_dt + timedelta(days=i) for i in range(total_days)]

    print(f"============================================================", flush=True)
    print(f"📥 Starting English Dam PDF Downloader (WRD Maharashtra)", flush=True)
    print(f"📁 Target Folder : {TARGET_DIR}", flush=True)
    print(f"📅 Date Range    : {start_dt.strftime('%d-%m-%Y')} to {end_dt.strftime('%d-%m-%Y')} ({len(dates)} days)", flush=True)
    print(f"⚙️  Concurrency    : {workers} workers", flush=True)
    print(f"============================================================", flush=True)

    stats = {
        'DOWNLOADED': 0,
        'ALREADY_EXISTS': 0,
        'NOT_FOUND': 0,
        'TOTAL': len(dates)
    }

    processed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(download_english_pdf_for_date, dt): dt for dt in dates}
        for future in as_completed(futures):
            processed += 1
            dt_str, dest_path, success, reason = future.result()
            stats[reason] = stats.get(reason, 0) + 1

            if reason == 'DOWNLOADED':
                print(f"  [+] Downloaded: report_{dt_str}.pdf ({processed}/{len(dates)})", flush=True)

            if processed % 25 == 0 or processed == len(dates):
                elapsed = time.time() - start_time
                pct = (processed / len(dates)) * 100
                print(f"[{processed:4d}/{len(dates):4d} - {pct:5.1f}%] "
                      f"✅ Downloaded: {stats['DOWNLOADED']} | "
                      f"⚡ Existing: {stats['ALREADY_EXISTS']} | "
                      f"⚠️  Not Available: {stats['NOT_FOUND']} "
                      f"({elapsed:.1f}s elapsed)", flush=True)

    print(f"\n============================================================", flush=True)
    print(f"🏁 English PDF Download Complete!", flush=True)
    print(f"Total Dates Checked: {stats['TOTAL']}", flush=True)
    print(f"Successfully Downloaded: {stats['DOWNLOADED']}", flush=True)
    print(f"Already Available: {stats['ALREADY_EXISTS']}", flush=True)
    print(f"Reports Not Published/Unavailable: {stats['NOT_FOUND']}", flush=True)
    print(f"============================================================", flush=True)

    # Calculate summary per year
    total_size_bytes = 0
    total_pdf_count = 0
    year_counts = {}

    for root, _, files in os.walk(TARGET_DIR):
        for f in files:
            if f.endswith('.pdf'):
                total_pdf_count += 1
                sz = os.path.getsize(os.path.join(root, f))
                total_size_bytes += sz
                rel = os.path.relpath(os.path.join(root, f), TARGET_DIR)
                parts = rel.split(os.sep)
                if len(parts) >= 2:
                    yr = parts[0]
                    year_counts[yr] = year_counts.get(yr, 0) + 1

    mb_size = total_size_bytes / (1024 * 1024)
    print(f"📊 Summary in '{TARGET_DIR}':", flush=True)
    print(f"   - Total Valid English PDFs: {total_pdf_count}", flush=True)
    for yr in sorted(year_counts.keys()):
        print(f"     * {yr}: {year_counts[yr]} PDFs", flush=True)
    print(f"   - Total Disk Size : {mb_size:.2f} MB", flush=True)
    print(f"============================================================\n", flush=True)

if __name__ == '__main__':
    start_arg = sys.argv[1] if len(sys.argv) > 1 else "01-01-2024"
    end_arg = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%d-%m-%Y")
    workers_arg = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    run_download_all(start_arg, end_arg, workers=workers_arg)
