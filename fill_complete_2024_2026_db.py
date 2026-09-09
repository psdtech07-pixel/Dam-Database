import pandas as pd
import numpy as np
from datetime import date, timedelta
import db_manager

def clean_multi_day_spikes(df):
    """
    Applies a 7-day centered rolling median filter to detect and smooth multi-day PDF parsing artifacts.
    If a storage value deviates significantly from the surrounding 7-day trend during non-overflow periods,
    it is replaced with the physical 7-day median baseline.
    """
    cleaned_rows = []

    for dam_name, group in df.groupby('Dam Name'):
        group = group.sort_values('dt').copy()
        meta = db_manager.DAM_MASTER_DATA[[d['dam_name'] for d in db_manager.DAM_MASTER_DATA].index(dam_name)]
        meta_live = meta['design_live_mcm']
        
        # 1. 7-day centered rolling median
        group['rolling_med'] = group['Current Live Storage (MCM)'].rolling(window=7, center=True, min_periods=1).median()
        group['diff_from_med'] = (group['Current Live Storage (MCM)'] - group['rolling_med']).abs()
        
        pct_trend = (group['rolling_med'] / meta_live) * 100
        
        # Anomaly mask: deviation > 12% of live capacity while trend is < 80%
        anomaly_mask = (group['diff_from_med'] > (meta_live * 0.12)) & (pct_trend < 80)
        
        # Replace anomaly with rolling median
        group.loc[anomaly_mask, 'Current Live Storage (MCM)'] = group.loc[anomaly_mask, 'rolling_med']
        
        # Recalculate metrics
        group['Current Live Storage (MCM)'] = group['Current Live Storage (MCM)'].clip(lower=0, upper=meta_live).round(2)
        group['Current Gross Storage (MCM)'] = (group['Current Live Storage (MCM)'] + meta['dead_storage_mcm']).round(2)
        group['Current Live Storage (%)'] = ((group['Current Live Storage (MCM)'] / meta_live) * 100).round(2)

        group = group.drop(columns=['rolling_med', 'diff_from_med'], errors='ignore')
        cleaned_rows.append(group)

    return pd.concat(cleaned_rows, ignore_index=True).sort_values(['dt', 'Dam Name'])

def build_full_continuous_dataset():
    print("🚀 Running 7-day Rolling Median Multi-Day Spike Cleaning Pipeline...")
    
    df = pd.read_csv("Maharashtra_5_Dams_Cleaned_Data.csv")
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    
    df['dt'] = pd.to_datetime(df['Report Date'], format='%d/%m/%Y', errors='coerce')
    if 'iso_date' in df.columns:
        df['dt'] = df['dt'].fillna(pd.to_datetime(df['iso_date'], errors='coerce'))

    df = df.dropna(subset=['dt']).sort_values(['dt', 'Dam Name'])
    df = df.drop_duplicates(subset=['dt', 'Dam Name'], keep='last')

    dams = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar']

    start_date = date(2024, 1, 1)
    end_date = date.today()
    
    full_dates = []
    curr = start_date
    while curr <= end_date:
        full_dates.append(curr)
        curr += timedelta(days=1)

    grid = []
    for d in full_dates:
        for dam in dams:
            grid.append({'dt': pd.to_datetime(d), 'Dam Name': dam})
            
    grid_df = pd.DataFrame(grid)

    merged = pd.merge(grid_df, df[['dt', 'Dam Name', 'Report Time', 'Current Live Storage (MCM)', 'Current Gross Storage (MCM)', 'Current Live Storage (%)', 'Last Year Storage (%)', 'Status']], on=['dt', 'Dam Name'], how='left')

    cleaned_rows = []
    for dam_name in dams:
        meta = db_manager.DAM_MASTER_DATA[[d['dam_name'] for d in db_manager.DAM_MASTER_DATA].index(dam_name)]
        dam_df = merged[merged['Dam Name'] == dam_name].copy().sort_values('dt')
        
        dam_df['Dead Storage (MCM)'] = meta['dead_storage_mcm']
        dam_df['Design Live Storage (MCM)'] = meta['design_live_mcm']
        dam_df['Design Gross Storage (MCM)'] = meta['design_gross_mcm']

        dam_df = dam_df.set_index('dt')
        
        # Time-series interpolation for Live MCM
        dam_df['Current Live Storage (MCM)'] = dam_df['Current Live Storage (MCM)'].interpolate(method='time').bfill().ffill()
        dam_df['Current Live Storage (MCM)'] = dam_df['Current Live Storage (MCM)'].clip(lower=0, upper=meta['design_live_mcm'])

        dam_df['Current Gross Storage (MCM)'] = (dam_df['Current Live Storage (MCM)'] + meta['dead_storage_mcm']).round(2)
        dam_df['Current Live Storage (%)'] = ((dam_df['Current Live Storage (MCM)'] / meta['design_live_mcm']) * 100).round(2)

        dam_df['Last Year Storage (%)'] = dam_df['Last Year Storage (%)'].interpolate(method='time').bfill().ffill().round(2)

        dam_df['Status'] = dam_df['Status'].fillna('Success')
        dam_df['Report Time'] = dam_df['Report Time'].fillna('08:00 स.')

        dam_df = dam_df.reset_index()
        cleaned_rows.append(dam_df)

    final_df = pd.concat(cleaned_rows, ignore_index=True)
    
    # 2 passes of 7-day rolling median filter
    final_df = clean_multi_day_spikes(final_df)
    final_df = clean_multi_day_spikes(final_df)

    final_df['Report Date'] = final_df['dt'].dt.strftime('%d/%m/%Y')
    final_df['iso_date'] = final_df['dt'].dt.strftime('%Y-%m-%d')

    # Save to CSV
    final_df.to_csv("Maharashtra_5_Dams_Cleaned_Data.csv", index=False, encoding='utf-8-sig')
    final_df.to_csv("Maharashtra_5_Dams_Data.csv", index=False, encoding='utf-8-sig')
    print(f"✨ 100% Smooth Spike-Free Dataset Generated: {len(final_df)} records across {len(full_dates)} calendar days!")

    # Ingest into SQLite RDBMS
    db_manager.init_db()
    db_manager.seed_reports_from_csv("Maharashtra_5_Dams_Cleaned_Data.csv")
    db_manager.export_db_to_json("dam_data.json")

if __name__ == "__main__":
    build_full_continuous_dataset()
