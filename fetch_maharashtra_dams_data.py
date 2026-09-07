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

# Try importing optional libraries
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

# Target 5 dams mapping with English name and Marathi/English keywords
TARGET_DAMS = {
    'Khadakwasla': ['खडकवासला', 'khadakwasla'],
    'Panshet': ['पानशेत', 'पानशत', 'panshet'],
    'Mulshi': ['मुळशी', 'मळशी', 'mulshi'],
    'Gunjawani': ['गुंजवणी', 'गजवणी', 'gunjawani', 'gaunjawane'],
    'Temghar': ['टेमघर', 'टमघर', 'temghar']
}

MARATHI_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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

def parse_dam_line(line):
    """Parses a line containing dam storage data after converting Marathi numerals."""
    line_trans = line.translate(MARATHI_DIGITS)
    tokens = line_trans.split()
    
    date_idx = -1
    for i, t in enumerate(tokens):
        if re.match(r'\d{2}/\d{2}/\d{4}', t):
            date_idx = i
            break

    if date_idx != -1 and len(tokens) >= date_idx + 9:
        report_date = tokens[date_idx]
        report_time = f"{tokens[date_idx+1]} {tokens[date_idx+2]}" if date_idx+2 < len(tokens) else tokens[date_idx+1]
        
        dead_storage = tokens[date_idx + 3]
        design_live = tokens[date_idx + 4]
        design_gross = tokens[date_idx + 5]
        current_live = tokens[date_idx + 6]
        current_gross = tokens[date_idx + 7]
        current_pct = tokens[date_idx + 8].replace('%', '')
        
        prev_year_pct = ""
        for token in tokens[date_idx + 9:]:
            cleaned = token.replace('%', '')
            if re.match(r'^\d+(\.\d+)?$', cleaned):
                prev_year_pct = cleaned
                break

        return {
            'Report Date': report_date,
            'Report Time': report_time,
            'Dead Storage (MCM)': float(dead_storage) if re.match(r'^\d+(\.\d+)?$', dead_storage) else dead_storage,
            'Design Live Storage (MCM)': float(design_live) if re.match(r'^\d+(\.\d+)?$', design_live) else design_live,
            'Design Gross Storage (MCM)': float(design_gross) if re.match(r'^\d+(\.\d+)?$', design_gross) else design_gross,
            'Current Live Storage (MCM)': float(current_live) if re.match(r'^\d+(\.\d+)?$', current_live) else current_live,
            'Current Gross Storage (MCM)': float(current_gross) if re.match(r'^\d+(\.\d+)?$', current_gross) else current_gross,
            'Current Live Storage (%)': float(current_pct) if re.match(r'^\d+(\.\d+)?$', current_pct) else current_pct,
            'Last Year Storage (%)': float(prev_year_pct) if re.match(r'^\d+(\.\d+)?$', prev_year_pct) else prev_year_pct,
            'Status': 'Success'
        }
    return None

def extract_5_dams_from_pdf(pdf_path, dt_str):
    """Extracts storage metrics for all 5 target dams from a single PDF."""
    results = {}
    if not pdf_path or not os.path.exists(pdf_path):
        for dam_name in TARGET_DAMS:
            results[dam_name] = {'Dam Name': dam_name, 'Report Date': dt_str, 'Status': 'PDF Not Available'}
        return results

    text = get_pdf_text(pdf_path)
    lines = text.split('\n')
    
    found_dams = set()
    for i, line in enumerate(lines):
        for dam_name, keywords in TARGET_DAMS.items():
            if dam_name in found_dams:
                continue
            if any(kw in line for kw in keywords):
                # Try single line first, then combined with next line for split headers
                combined = line + ' ' + (lines[i+1] if i+1 < len(lines) else '')
                parsed = parse_dam_line(line) or parse_dam_line(combined)
                if parsed:
                    parsed['Dam Name'] = dam_name
                    results[dam_name] = parsed
                    found_dams.add(dam_name)

    # Fill missing dams
    for dam_name in TARGET_DAMS:
        if dam_name not in results:
            results[dam_name] = {'Dam Name': dam_name, 'Report Date': dt_str, 'Status': 'Data Not Found in PDF'}
            
    return results

def download_pdf_for_date(date_obj, pdf_dir):
    """Downloads daily PDF for given date trying common filename variations."""
    dt_str = date_obj.strftime('%d-%m-%Y')
    dest_path = os.path.join(pdf_dir, f"report_{dt_str}.pdf")
    
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return dt_str, dest_path, True

    base_url = 'https://wrd.maharashtra.gov.in/Upload/PDF/'
    patterns = [
        "Today's-Storage-ReportMarathi-{date}.pdf",
        "Today's Storage ReportMarathi-{date}.pdf",
        "Today's-Storage-Report-{date}.pdf",
        "Today-Storage-ReportMarathi-{date}.pdf",
        "Todays-Storage-ReportMarathi-{date}.pdf"
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
    """Downloads PDFs for date range and extracts data for all 5 dams."""
    os.makedirs(pdf_dir, exist_ok=True)
    today = datetime.now()
    dates = [today - timedelta(days=i) for i in range(days)]
    
    print(f"[*] Starting download & extraction for 5 Dams ({', '.join(TARGET_DAMS.keys())}) across {days} days...")
    
    pdf_files = {}
    with ThreadPoolExecutor(max_workers=max_download_workers) as executor:
        futures = {executor.submit(download_pdf_for_date, d, pdf_dir): d for d in dates}
        for future in as_completed(futures):
            dt_str, pdf_path, success = future.result()
            if success:
                pdf_files[dt_str] = pdf_path

    print(f"[*] Downloaded/Cached {len(pdf_files)} PDF reports out of {days} requested dates.")
    print(f"[*] Parsing 5 dams from {len(dates)} dates in parallel...")

    all_records = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max_extract_workers) as executor:
        futures = {executor.submit(extract_5_dams_from_pdf, pdf_files.get(d.strftime('%d-%m-%Y')), d.strftime('%d/%m/%Y')): d for d in dates}
        for future in as_completed(futures):
            dam_results = future.result()
            for dam_name, rec in dam_results.items():
                all_records.append(rec)
            completed += 1
            if completed % 100 == 0 or completed == len(dates):
                print(f"    -> Progress: [{completed}/{len(dates)}] dates processed.")

    df = pd.DataFrame(all_records)
    
    # Sort by Date descending and Dam Name
    def sort_key(rec):
        try:
            return datetime.strptime(str(rec.get('Report Date', '')), '%d/%m/%Y')
        except Exception:
            return datetime.min

    df['SortDate'] = df['Report Date'].apply(lambda x: datetime.strptime(str(x), '%d/%m/%Y') if re.match(r'\d{2}/\d{2}/\d{4}', str(x)) else datetime.min)
    df = df.sort_values(by=['SortDate', 'Dam Name'], ascending=[False, True]).drop(columns=['SortDate'])
    
    return df

def save_to_files(df, output_excel='Maharashtra_5_Dams_Data.xlsx', output_csv='Maharashtra_5_Dams_Data.csv'):
    """Saves combined data to CSV and multi-tab Excel sheet."""
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"[+] Saved Combined CSV to: {output_csv}")

    try:
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            # 1. Combined Sheet
            df.to_excel(writer, index=False, sheet_name='All 5 Dams')
            worksheet = writer.sheets['All 5 Dams']
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

            # 2. Individual tab for each dam
            for dam_name in TARGET_DAMS:
                dam_df = df[df['Dam Name'] == dam_name]
                sheet_title = dam_name[:31]  # Excel max sheet name limit
                dam_df.to_excel(writer, index=False, sheet_name=sheet_title)
                ws = writer.sheets[sheet_title]
                for col in ws.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        print(f"[+] Saved Formatted Multi-Tab Excel to: {output_excel}")
    except Exception as e:
        print(f"[!] Note: Could not format Excel via openpyxl ({e}). CSV is ready.")

def push_to_mysql(df, host='localhost', user='root', password='', database='maharashtra_water_db', port=3306):
    """Inserts/upserts dam storage data into MySQL database with separate tables per dam."""
    try:
        import mysql.connector
    except ImportError:
        print("[!] mysql-connector-python module not installed. Install with: pip install mysql-connector-python")
        return False

    print(f"[*] Connecting to MySQL database '{database}' on {host}:{port}...")
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE {database}")
        
        # Process data dam by dam
        grouped = df.groupby('Dam Name')
        total_synced = 0

        for dam_name, dam_df in grouped:
            table_name = f"dam_{re.sub(r'[^a-zA-Z0-9_]', '', dam_name.lower())}"
            
            # Create separate table for this dam
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
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
            """
            cursor.execute(create_table_sql)

            upsert_sql = f"""
            INSERT INTO {table_name} (
                report_date, report_time, dead_storage_mcm,
                design_live_storage_mcm, design_gross_storage_mcm, current_live_storage_mcm,
                current_gross_storage_mcm, current_live_storage_pct, last_year_storage_pct, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                report_time = VALUES(report_time),
                dead_storage_mcm = VALUES(dead_storage_mcm),
                design_live_storage_mcm = VALUES(design_live_storage_mcm),
                design_gross_storage_mcm = VALUES(design_gross_storage_mcm),
                current_live_storage_mcm = VALUES(current_live_storage_mcm),
                current_gross_storage_mcm = VALUES(current_gross_storage_mcm),
                current_live_storage_pct = VALUES(current_live_storage_pct),
                last_year_storage_pct = VALUES(last_year_storage_pct),
                status = VALUES(status);
            """

            rows_to_insert = []
            for _, r in dam_df.iterrows():
                if r.get('Status') == 'Success':
                    try:
                        formatted_date = datetime.strptime(str(r['Report Date']), '%d/%m/%Y').strftime('%Y-%m-%d')
                    except Exception:
                        continue

                    rows_to_insert.append((
                        formatted_date,
                        str(r.get('Report Time', '')),
                        float(r['Dead Storage (MCM)']) if isinstance(r.get('Dead Storage (MCM)'), (int, float)) else None,
                        float(r['Design Live Storage (MCM)']) if isinstance(r.get('Design Live Storage (MCM)'), (int, float)) else None,
                        float(r['Design Gross Storage (MCM)']) if isinstance(r.get('Design Gross Storage (MCM)'), (int, float)) else None,
                        float(r['Current Live Storage (MCM)']) if isinstance(r.get('Current Live Storage (MCM)'), (int, float)) else None,
                        float(r['Current Gross Storage (MCM)']) if isinstance(r.get('Current Gross Storage (MCM)'), (int, float)) else None,
                        float(r['Current Live Storage (%)']) if isinstance(r.get('Current Live Storage (%)'), (int, float)) else None,
                        float(r['Last Year Storage (%)']) if isinstance(r.get('Last Year Storage (%)'), (int, float)) else None,
                        str(r.get('Status', 'Success'))
                    ))

            if rows_to_insert:
                cursor.executemany(upsert_sql, rows_to_insert)
                total_synced += len(rows_to_insert)
                print(f"    -> Synced {len(rows_to_insert)} records to table '{table_name}'")

        conn.commit()
        print(f"[+] Successfully synced total {total_synced} records across separate dam tables in MySQL database '{database}'.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[!] MySQL sync failed: {e}")
        return False

if __name__ == '__main__':
    days = 3650  # Default 10 years (3650 days)
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass

    df = fetch_multi_dam_data(days=days)
    save_to_files(df, output_excel='Maharashtra_5_Dams_10Year_Data.xlsx', output_csv='Maharashtra_5_Dams_10Year_Data.csv')
