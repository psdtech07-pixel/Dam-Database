import os
import re
import ssl
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

PDF_DIR = "dam_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_existing_dates():
    files = os.listdir(PDF_DIR)
    dates = set()
    for f in files:
        if f.endswith('.pdf'):
            m = re.search(r'(\d{2}-\d{2}-\d{4})', f)
            if m:
                try:
                    dt = datetime.strptime(m.group(1), '%d-%m-%Y').date()
                    dates.add(dt)
                except ValueError:
                    pass
    return dates

def generate_missing_dates():
    existing = get_existing_dates()
    
    # 2024 full year: 01/01/2024 to 31/12/2024
    d2024_start = date(2024, 1, 1)
    d2024_end = date(2024, 12, 31)
    
    # 2025 full year: 01/01/2025 to 31/12/2025
    d2025_start = date(2025, 1, 1)
    d2025_end = date(2025, 12, 31)
    
    # 2026 up to today (09/09/2026)
    d2026_start = date(2026, 1, 1)
    d2026_end = date.today()
    
    all_target_dates = []
    
    curr = d2024_start
    while curr <= d2026_end:
        all_target_dates.append(curr)
        curr += timedelta(days=1)
        
    missing = [d for d in all_target_dates if d not in existing]
    return missing, len(all_target_dates), len(existing)

def try_download_pdf(dt):
    dt_dash = dt.strftime('%d-%m-%Y')
    dt_dot = dt.strftime('%d.%m.%Y')
    dt_iso = dt.strftime('%Y-%m-%d')
    dest_file = os.path.join(PDF_DIR, f"report_{dt_dash}.pdf")
    
    if os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
        return dt, True, "Already Exists"

    base_url = 'https://wrd.maharashtra.gov.in/Upload/PDF/'
    
    url_patterns = [
        f"Today's-Storage-ReportMarathi-{dt_dash}.pdf",
        f"Today's Storage ReportMarathi-{dt_dash}.pdf",
        f"Today's-Storage-Report-{dt_dash}.pdf",
        f"Today-Storage-ReportMarathi-{dt_dash}.pdf",
        f"Todays-Storage-ReportMarathi-{dt_dash}.pdf",
        f"Today's-Storage-Report-Marathi-{dt_dash}.pdf",
        f"Today's-Storage-ReportMarathi-{dt_dot}.pdf",
        f"Today's-Storage-Report-{dt_dot}.pdf",
        f"Storage-ReportMarathi-{dt_dash}.pdf",
        f"Dam-Storage-ReportMarathi-{dt_dash}.pdf",
        f"%E0%A4%86%E0%A4%9C%E0%A4%9A%E0%A4%BE-%E0%A4%AA%E0%A4%BE%E0%A4%A3%E0%A5%80%E0%A4%B0%E0%A5%8D%E0%A4%B8%E0%A4%BE-{dt_dash}.pdf",
        f"Today's-Storage-ReportMarathi-{dt_iso}.pdf",
        f"Today's-Storage-Report-{dt_iso}.pdf"
    ]

    for pat in url_patterns:
        url = base_url + urllib.parse.quote(pat)
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=8) as resp:
                data = resp.read()
                if len(data) > 1000 and b'%PDF' in data[:20]:
                    with open(dest_file, 'wb') as f:
                        f.write(data)
                    return dt, True, pat
        except Exception:
            continue

    return dt, False, "Not Found on Server"

def main():
    missing_dates, total_target, existing_count = generate_missing_dates()
    print(f"🎯 Target Range: 01/01/2024 to {date.today().strftime('%d/%m/%Y')} ({total_target} days total)")
    print(f"📁 Currently Existing PDFs: {existing_count}")
    print(f"🔍 Missing Dates to Download: {len(missing_dates)}")

    if not missing_dates:
        print("✨ All PDFs for 2024, 2025, and 2026 are already downloaded!")
        return

    successful = 0
    failed = 0

    print(f"\n🚀 Launching parallel downloader across {len(missing_dates)} missing dates...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(try_download_pdf, dt): dt for dt in missing_dates}
        for future in as_completed(futures):
            dt, success, note = future.result()
            if success and note != "Already Exists":
                successful += 1
                print(f"  ✅ Downloaded PDF for {dt.strftime('%d/%m/%Y')} ({note})")
            elif not success:
                failed += 1

    print(f"\n🏁 Download Batch Complete!")
    print(f"   Downloaded New PDFs: {successful}")
    print(f"   Unavailable on Server: {failed}")
    
    updated_existing = get_existing_dates()
    print(f"   Final Total Available PDFs in 'dam_pdfs/': {len(updated_existing)}")

if __name__ == "__main__":
    main()
