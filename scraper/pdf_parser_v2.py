import os
import re
import sys
import json
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(BASE_DIR, 'database', 'dam_registry.json')

def load_dam_lookup(registry_path=REGISTRY_PATH):
    """
    Loads dam registry mapping names, slugs, and aliases to canonical dam info.
    Enforces collision detection (B07.4) and merges 'tillari-kokan-sindhudurg' into 'tillari'.
    """
    if not os.path.exists(registry_path):
        raise FileNotFoundError(f"Registry not found: {registry_path}")

    with open(registry_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter out duplicate tillari-kokan-sindhudurg
    clean_registry = [d for d in data if d.get('slug') != 'tillari-kokan-sindhudurg']

    lookup = {}
    slug_ownership = {}

    for entry in clean_registry:
        slug = entry['slug']
        info = {
            'slug': slug,
            'en': entry['en'],
            'mr': entry.get('mr', entry['en']),
            'district': entry['district'],
            'division': entry['division'],
            'basin': entry.get('basin', 'Krishna'),
            'type': entry.get('type', 'MAJOR'),
            'dead': float(entry['dead']) if entry.get('dead') is not None else None,
            'live': float(entry['live']) if entry.get('live') is not None else (float(entry['design_live_mcm']) if entry.get('design_live_mcm') is not None else None),
            'gross': float(entry['gross']) if entry.get('gross') is not None else (float(entry['design_gross_mcm']) if entry.get('design_gross_mcm') is not None else None)
        }

        # Build alias tokens
        keys = [slug.lower(), entry['en'].lower()]
        if entry.get('mr'):
            keys.append(entry['mr'].lower())
        for k in entry.get('keys', []):
            keys.append(k.lower())
        for a in entry.get('aliases_mr', []):
            keys.append(a.lower())

        for k in keys:
            k = k.strip()
            if not k:
                continue
            if k in slug_ownership and slug_ownership[k] != slug:
                raise ValueError(f"Alias collision detected for key '{k}' between slugs '{slug_ownership[k]}' and '{slug}' (B07 guard)")
            slug_ownership[k] = slug
            lookup[k] = info

    return lookup

def parse_bulletin_pdf(pdf_path, dam_lookup=None):
    """
    Extracts dam storage records from a WRD bulletin PDF using column right-edge alignment.
    Returns:
        report_date: ISO string 'YYYY-MM-DD' from bulletin header
        records: list of parsed dicts with named fields
        errors: list of error strings if any
    """
    if not os.path.exists(pdf_path):
        return None, [], [f"File not found: {pdf_path}"]

    if dam_lookup is None:
        dam_lookup = load_dam_lookup()

    res = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return None, [], [f"pdftotext failed with exit code {res.returncode}"]

    text = res.stdout
    pages = text.split('\x0c')

    # 1. Parse report status date from top of document
    report_date = None
    date_header_match = re.search(r'Status\s+as\s+on\s+Date\s*:\s*(\d{2}/\d{2}/\d{4})', text[:3000], re.IGNORECASE)
    if date_header_match:
        try:
            report_date = datetime.strptime(date_header_match.group(1), '%d/%m/%Y').strftime('%Y-%m-%d')
        except Exception:
            pass

    records = []
    errors = []

    current_div = 'Nagpur'
    current_dist = 'Bhandara'

    for page_idx, page in enumerate(pages):
        lines = page.split('\n')
        header_line = None

        for line in lines:
            if 'DEAD' in line and 'LIVE' in line and 'GROSS' in line and ('DATE' in line or 'TIME' in line):
                header_line = line
                break

        if not header_line:
            continue

        # Extract column header end positions
        headers = []
        for m in re.finditer(r'(DEAD|LIVE|GROSS|TODAY|SAME DATE|DATE OF|LAST YEAR)', header_line):
            headers.append((m.group(), m.end()))

        dead_h = [h for h in headers if h[0] == 'DEAD']
        live_h = [h for h in headers if h[0] == 'LIVE']
        gross_h = [h for h in headers if h[0] == 'GROSS']
        today_h = [h for h in headers if h[0] == 'TODAY']
        last_h = [h for h in headers if h[1] > (today_h[0][1] if today_h else 0)]

        if not (dead_h and len(live_h) >= 2 and len(gross_h) >= 2 and today_h):
            continue

        col_names = ['dead', 'des_live', 'des_gross', 'live', 'gross', 'pct', 'last_year_pct']
        col_ends = [
            dead_h[0][1],
            live_h[0][1],
            gross_h[0][1],
            live_h[1][1],
            gross_h[1][1],
            today_h[0][1],
            last_h[0][1] if last_h else (today_h[0][1] + 14)
        ]

        for line in lines:
            s = line.strip()

            # Track division & district headers
            for div in ['Nagpur', 'Amravati', 'Chhatrapati Sambhajinagar', 'Nashik', 'Pune', 'Kokan']:
                if f'{div} Region' in s or (div == 'Amravati' and 'Amravti Region' in s):
                    current_div = div
                    break

            # Check table row: {SrNo} {Dam Name} {DD/MM/YYYY} {HH:MM AM/PM} ...
            m = re.search(r'^\s*(\d+)\s+([A-Za-z0-9\(\)\.\s\-\/\']+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}\s*(?:AM|PM|am|pm)?)\s+', line)
            if not m:
                continue

            sr, raw_name, line_date_str, line_time = m.groups()
            dam_name = raw_name.strip()

            if any(h in dam_name for h in ['UPDATION', 'NAME OF', 'STORAGE', 'PROJECT', 'TOTAL', 'REGION']):
                continue

            time_m = re.search(r'\d{2}:\d{2}\s*(?:AM|PM|am|pm)?', line)
            nums_part = line[time_m.end():]
            base_offset = time_m.end()

            # Right-edge column slotting
            row_vals = {c: None for c in col_names}
            for num_m in re.finditer(r'[-+]?\d*\.?\d+', nums_part):
                val = float(num_m.group())
                end = base_offset + num_m.end()

                best_idx = min(range(len(col_ends)), key=lambda i: abs(end - col_ends[i]))
                if abs(end - col_ends[best_idx]) <= 8:
                    row_vals[col_names[best_idx]] = val

            # Resolve line date
            try:
                line_date_iso = datetime.strptime(line_date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            except Exception:
                line_date_iso = None

            # Resolve canonical dam info
            clean_name = dam_name.lower()
            info = dam_lookup.get(clean_name)
            if not info:
                # Try without parentheses
                no_parens = re.sub(r'\(.*?\)', '', clean_name).strip()
                info = dam_lookup.get(no_parens)

            record = {
                'raw_name': dam_name,
                'slug': info['slug'] if info else None,
                'en': info['en'] if info else dam_name,
                'district': info['district'] if info else current_dist,
                'division': info['division'] if info else current_div,
                'basin': info['basin'] if info else 'Krishna',
                'reading_date': line_date_iso or report_date,
                'reading_time': line_time.strip(),
                'dead_storage_mcm': row_vals['dead'],
                'design_live_mcm': row_vals['des_live'],
                'design_gross_mcm': row_vals['des_gross'],
                'live_storage_mcm': row_vals['live'],
                'gross_storage_mcm': row_vals['gross'],
                'storage_pct': row_vals['pct'],
                'last_year_pct': row_vals['last_year_pct'],
                'raw_line': line
            }
            records.append(record)

    return report_date, records, errors

def validate_record(rec, design_live, tol_pp=2.0):
    """
    Validates a parsed dam record against hydrological consistency constraints.
    Returns a list of violation error strings (empty if record passes).
    """
    errs = []
    live = rec.get('live_storage_mcm')
    pct = rec.get('storage_pct')
    gross = rec.get('gross_storage_mcm')

    if live is None:
        errs.append("live_missing")
    elif live < 0 or (design_live > 0 and live > design_live * 1.10):
        errs.append("live_out_of_range")

    if live is not None and pct is not None and design_live > 0:
        calc_pct = 100.0 * live / design_live
        # Legitimate monsoon overflow (e.g. 100-110%) where WRD caps table pct at 100% is allowed
        if calc_pct >= 100.0 and pct == 100.0 and calc_pct <= 110.0:
            pass
        elif abs(calc_pct - pct) > tol_pp:
            errs.append("pct_mismatch")

    if gross is not None and live is not None and gross < live:
        errs.append("gross_lt_live")

    if live == 100.0 and design_live != 100.0:
        # If pct also strongly disagrees with 100.0 MCM being genuine
        if pct is not None and abs(100.0 - pct) > tol_pp:
            errs.append("suspect_default_100")

    return errs
