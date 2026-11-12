import os
import sys
import time
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'scraper'))
sys.path.append(os.path.join(BASE_DIR, 'database'))

import fetch_dam_data
import db_manager

def run_daily_job(days=3):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_str}] 🚀 Starting daily dam data collection & ingestion...")
    try:
        # 1. Audit and reconcile recent English bulletins (default last 3 days)
        df = fetch_dam_data.fetch_multi_dam_data(days=days)
        
        # 2. Ingest into 3NF SQLite database & export web JSON files
        fetch_dam_data.save_to_files(df)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Daily dam data job finished successfully.")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Daily job encountered error: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Daily Dam Data Worker for Maharashtra Reservoirs")
    parser.add_argument('--once', action='store_true', help="Run job once and exit (ideal for cron / systemd)")
    parser.add_argument('--days', type=int, default=3, help="Number of recent days to reconcile (default: 3)")
    args = parser.parse_args()

    if args.once:
        run_daily_job(days=args.days)
    else:
        # Run once immediately on start
        run_daily_job(days=args.days)
        try:
            import schedule
            # Schedule daily at 08:30 AM and 02:30 PM (WRD publishes at ~08:00 AM)
            schedule.every().day.at("08:30").do(run_daily_job, days=args.days)
            schedule.every().day.at("14:30").do(run_daily_job, days=args.days)
            print("[*] Worker daemon running. Scheduled daily at 08:30 AM and 02:30 PM. Press Ctrl+C to stop.")
            while True:
                schedule.run_pending()
                time.sleep(60)
        except ImportError:
            print("[!] 'schedule' library not installed for daemon mode. Run with '--once' or install schedule: 'pip install schedule'")
