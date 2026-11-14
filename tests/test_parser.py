import os
import glob
import pytest
from scraper.pdf_parser_v2 import validate_record, parse_bulletin_pdf, load_dam_lookup

def test_validate_record_clean():
    rec = {
        'live_storage_mcm': 500.0,
        'storage_pct': 50.0,
        'gross_storage_mcm': 600.0
    }
    errs = validate_record(rec, design_live=1000.0)
    assert len(errs) == 0, f"Expected clean record, got errors: {errs}"

def test_validate_record_live_missing():
    rec = {'live_storage_mcm': None, 'storage_pct': 50.0}
    errs = validate_record(rec, design_live=1000.0)
    assert 'live_missing' in errs

def test_validate_record_live_out_of_range():
    rec = {'live_storage_mcm': 1200.0, 'storage_pct': 120.0, 'gross_storage_mcm': 1300.0}
    errs = validate_record(rec, design_live=1000.0)
    assert 'live_out_of_range' in errs

def test_validate_record_pct_mismatch():
    rec = {'live_storage_mcm': 500.0, 'storage_pct': 90.0, 'gross_storage_mcm': 600.0}
    errs = validate_record(rec, design_live=1000.0)
    assert 'pct_mismatch' in errs

def test_validate_record_gross_lt_live():
    rec = {'live_storage_mcm': 500.0, 'storage_pct': 50.0, 'gross_storage_mcm': 400.0}
    errs = validate_record(rec, design_live=1000.0)
    assert 'gross_lt_live' in errs

def test_validate_record_suspect_default_100():
    # live is 100.0 MCM but design capacity is 2835 MCM and pct is 97.8% (column shift artifact)
    rec = {'live_storage_mcm': 100.0, 'storage_pct': 97.8, 'gross_storage_mcm': 2800.0}
    errs = validate_record(rec, design_live=2835.0)
    assert 'suspect_default_100' in errs or 'pct_mismatch' in errs

def test_validate_monsoon_overflow_allowed():
    # Mulshi or Punegaon at 103% capacity with printed pct capped at 100% by WRD
    rec = {'live_storage_mcm': 1030.0, 'storage_pct': 100.0, 'gross_storage_mcm': 1100.0}
    errs = validate_record(rec, design_live=1000.0)
    assert len(errs) == 0, f"Expected legitimate monsoon overflow to pass, got: {errs}"

def test_parse_bulletin_on_sample_pdf():
    pdfs = glob.glob('dam_pdf/**/*.pdf', recursive=True)
    if not pdfs:
        pytest.skip("No sample PDFs found in dam_pdf/")
    sample_pdf = pdfs[0]
    dam_lookup = load_dam_lookup()
    report_date, records, errors = parse_bulletin_pdf(sample_pdf, dam_lookup)
    assert report_date is not None, f"Failed to parse report date from {sample_pdf}"
    assert len(records) > 50, f"Too few records parsed from {sample_pdf}: {len(records)}"
