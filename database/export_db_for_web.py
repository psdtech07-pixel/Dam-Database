#!/usr/bin/env python3
"""
Decoupled Static Export Script for Maharashtra Dam Monitoring System.
Exports SQLite database tables into:
1. web/data/latest_snapshot.json (~25 KB)
2. web/data/history/{dam_slug}.json (~10-15 KB per dam)
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "database"))

import db_manager

if __name__ == '__main__':
    print("[*] Exporting decoupled static web datasets from SQLite DBMS...")
    db_manager.export_decoupled_json()
    print("[+] Decoupled static export successfully completed.")
