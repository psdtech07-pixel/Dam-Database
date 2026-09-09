import time
import os
import sys
import schedule
from datetime import datetime

# Ensure local scraper module can be imported
sys.path.append(os.path.dirname(__file__))
import fetch_dam_data

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'parth',
    'password': 'Parth@07',
    'database': 'maharashtra_water_db',
    'port': 3306
}

def run_daily_job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting daily dam data collection...")
    try:
        # Fetch data for the last 2 days to account for daily report upload timing
        df = fetch_dam_data.fetch_multi_dam_data(days=2)
        
        # Save to SQLite DBMS & export dashboard JSON
        fetch_dam_data.save_to_files(df)

        # Sync/Upsert to MySQL database (separate table for each dam)
        success = fetch_dam_data.push_to_mysql(
            df,
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            port=MYSQL_CONFIG['port']
        )
        
        if success:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily job completed successfully!")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily job completed with MySQL warnings.")

    except Exception as e:
        print(f"[!] Error during daily execution: {e}")

if __name__ == '__main__':
    # Run immediately once on start
    run_daily_job()

    # Schedule job every day at 09:00 AM
    schedule.every().day.at("09:00").do(run_daily_job)

    print("[*] Daily worker started. Scheduled to run every day at 09:00 AM. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)

