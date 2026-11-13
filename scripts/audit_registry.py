#!/usr/bin/env python3
"""
scripts/audit_registry.py — B07.5
Compares each dam's dead/live/gross design capacity in dam_registry.json
with the official capacity columns printed in the latest PDF bulletin.
"""

import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scraper.pdf_parser_v2 import parse_bulletin_pdf, load_dam_lookup

def audit_registry_capacities(pdf_path=None):
    if pdf_path is None:
        pdf_path = BASE_DIR / 'dam_pdf' / '2026' / '11' / 'report_12-11-2026.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"Error: Sample PDF not found at {pdf_path}")
        return 1

    lookup = load_dam_lookup()
    dt, recs, errs = parse_bulletin_pdf(str(pdf_path), lookup)
    if errs:
        print("Parser errors:", errs)
        return 1

    reg_path = BASE_DIR / 'database' / 'dam_registry.json'
    with open(reg_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    reg_by_slug = {d['slug']: d for d in registry}
    pdf_by_slug = {r['slug']: r for r in recs if r['slug']}

    print(f"Auditing {len(reg_by_slug)} registry dams against {len(pdf_by_slug)} parsed from {pdf_path.name} ({dt}):\n")

    mismatches = []
    missing_in_pdf = []

    for slug, reg in sorted(reg_by_slug.items()):
        if slug not in pdf_by_slug:
            missing_in_pdf.append(slug)
            continue

        pdf = pdf_by_slug[slug]
        diffs = []
        for field, reg_key, pdf_key in [('dead', 'dead', 'dead_storage_mcm'),
                                         ('live', 'live', 'design_live_mcm'),
                                         ('gross', 'gross', 'design_gross_mcm')]:
            reg_val = reg.get(reg_key)
            if reg_val is None and field == 'live':
                reg_val = reg.get('design_live_mcm')
            if reg_val is None and field == 'gross':
                reg_val = reg.get('design_gross_mcm')
            
            pdf_val = pdf.get(pdf_key)

            if reg_val is not None and pdf_val is not None:
                if abs(float(reg_val) - float(pdf_val)) > 0.05:
                    diffs.append(f"{field}: reg={reg_val} != pdf={pdf_val}")
            elif reg_val is None and pdf_val is not None:
                diffs.append(f"{field}: reg=None, pdf={pdf_val}")
            elif reg_val is not None and pdf_val is None:
                diffs.append(f"{field}: reg={reg_val}, pdf=None")

        if diffs:
            mismatches.append((slug, reg['en'], diffs))

    if mismatches:
        print(f"⚠️ Found {len(mismatches)} capacity differences between registry and bulletin PDF:")
        for slug, name, diffs in mismatches:
            print(f"  • {name} ({slug}): {', '.join(diffs)}")
    else:
        print("✅ All registry design capacities match the official PDF bulletin perfectly!")

    if missing_in_pdf:
        print(f"\n⚠️ {len(missing_in_pdf)} dams in registry were not present in this PDF: {missing_in_pdf}")

    return len(mismatches)

if __name__ == '__main__':
    sys.exit(audit_registry_capacities())
