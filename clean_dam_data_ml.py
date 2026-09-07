import pandas as pd
import numpy as np
from pathlib import Path
import json

# Authoritative Dam Reference Metadata
DAM_METADATA = {
    'Khadakwasla': {'dead': 30.0, 'design_live': 55.91, 'design_gross': 85.91},
    'Panshet':     {'dead': 9.0,  'design_live': 301.61, 'design_gross': 310.61},
    'Mulshi':      {'dead': 230.0, 'design_live': 522.76, 'design_gross': 752.76},
    'Gunjawani':   {'dead': 0.21, 'design_live': 104.48, 'design_gross': 104.69},
    'Temghar':     {'dead': 2.95, 'design_live': 105.01, 'design_gross': 107.96}
}

def clean_and_impute():
    print("🚀 Starting Data Science Data Cleaning & Imputation Pipeline...")
    
    csv_file = Path("Maharashtra_5_Dams_Data.csv")
    csv_10y = Path("Maharashtra_5_Dams_10Year_Data.csv")
    
    dfs = []
    if csv_file.exists():
        dfs.append(pd.read_csv(csv_file))
    if csv_10y.exists():
        dfs.append(pd.read_csv(csv_10y))
        
    raw_df = pd.concat(dfs, ignore_index=True)
    raw_df.columns = raw_df.columns.str.strip().str.replace('\ufeff', '')
    
    print(f"📊 Initial Raw Records: {len(raw_df)}")

    # 1. Parse and standardize dates
    raw_df['dt'] = pd.to_datetime(raw_df['Report Date'], format='%d/%m/%Y', errors='coerce')
    raw_df = raw_df.dropna(subset=['dt']).sort_values(['dt', 'Dam Name'])

    # 2. Clean numeric columns
    num_cols = ['Dead Storage (MCM)', 'Design Live Storage (MCM)', 'Design Gross Storage (MCM)',
                'Current Live Storage (MCM)', 'Current Gross Storage (MCM)', 
                'Current Live Storage (%)', 'Last Year Storage (%)']

    for col in num_cols:
        raw_df[col] = pd.to_numeric(raw_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce')

    # Remove exact duplicate dam-date pairs (keep non-null if possible)
    raw_df = raw_df.sort_values(by=['dt', 'Dam Name', 'Current Live Storage (MCM)'], na_position='first')
    raw_df = raw_df.drop_duplicates(subset=['dt', 'Dam Name'], keep='last')

    cleaned_rows = []

    # 3. Process each dam independently
    dams = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar']

    for dam_name in dams:
        meta = DAM_METADATA[dam_name]
        dam_df = raw_df[raw_df['Dam Name'] == dam_name].copy()
        
        # Enforce canonical metadata
        dam_df['Dead Storage (MCM)'] = meta['dead']
        dam_df['Design Live Storage (MCM)'] = meta['design_live']
        dam_df['Design Gross Storage (MCM)'] = meta['design_gross']

        # Fix Column Swaps in Current Live Storage
        # If Current Live Storage MCM > Design Live Storage * 1.25, it's corrupted or swapped with gross storage
        mask_over = dam_df['Current Live Storage (MCM)'] > (meta['design_live'] * 1.25)
        dam_df.loc[mask_over, 'Current Live Storage (MCM)'] = np.nan

        # If Current Live Storage MCM < 0, set to NaN
        mask_under = dam_df['Current Live Storage (MCM)'] < 0
        dam_df.loc[mask_under, 'Current Live Storage (MCM)'] = np.nan

        # 4. Time-Series Interpolation for missing or corrupted Live MCM
        dam_df = dam_df.set_index('dt')
        
        # Linear/Time Interpolation for missing MCM values
        dam_df['Current Live Storage (MCM)'] = dam_df['Current Live Storage (MCM)'].interpolate(method='time').bfill().ffill()
        
        # Cap Live Storage MCM to Design Live Storage max
        dam_df['Current Live Storage (MCM)'] = dam_df['Current Live Storage (MCM)'].clip(lower=0, upper=meta['design_live'])

        # Recalculate Gross Storage (MCM) = Live MCM + Dead MCM
        dam_df['Current Gross Storage (MCM)'] = (dam_df['Current Live Storage (MCM)'] + meta['dead']).round(2)

        # Recalculate Storage Level (%) = (Live MCM / Design Live MCM) * 100
        dam_df['Current Live Storage (%)'] = ((dam_df['Current Live Storage (MCM)'] / meta['design_live']) * 100).round(2)

        # Interpolate Last Year Storage (%) if missing
        dam_df['Last Year Storage (%)'] = dam_df['Last Year Storage (%)'].interpolate(method='time').bfill().ffill().round(2)

        # Fill status
        dam_df['Status'] = dam_df['Status'].fillna('Success')
        dam_df['Report Time'] = dam_df['Report Time'].fillna('08:00 स.')

        dam_df = dam_df.reset_index()
        cleaned_rows.append(dam_df)

    final_df = pd.concat(cleaned_rows, ignore_index=True).sort_values(['dt', 'Dam Name'])

    # Format date back to string
    final_df['date'] = final_df['dt'].dt.strftime('%d/%m/%Y')
    final_df['iso_date'] = final_df['dt'].dt.strftime('%Y-%m-%d')

    print(f"✅ Data Cleaning Complete. Total Clean Records: {len(final_df)}")
    
    # Save cleaned CSV
    output_csv = Path("Maharashtra_5_Dams_Cleaned_Data.csv")
    final_df.to_csv(output_csv, index=False)
    print(f"📁 Cleaned dataset saved to: {output_csv}")

    # Build JSON structure for Dashboard
    latest_records = {}
    for dam_name in dams:
        dam_sub = final_df[final_df['Dam Name'] == dam_name]
        if not dam_sub.empty:
            last = dam_sub.iloc[-1]
            latest_records[dam_name] = {
                'date': last['date'],
                'time': last['Report Time'],
                'dead_mcm': float(last['Dead Storage (MCM)']),
                'design_live_mcm': float(last['Design Live Storage (MCM)']),
                'design_gross_mcm': float(last['Design Gross Storage (MCM)']),
                'current_live_mcm': float(last['Current Live Storage (MCM)']),
                'current_gross_mcm': float(last['Current Gross Storage (MCM)']),
                'current_pct': float(last['Current Live Storage (%)']),
                'last_year_pct': float(last['Last Year Storage (%)']),
                'status': str(last['Status'])
            }

    unique_dts = final_df['dt'].unique()
    time_series = []

    for u_dt in unique_dts:
        dt_str = pd.to_datetime(u_dt).strftime('%Y-%m-%d')
        date_fmt = pd.to_datetime(u_dt).strftime('%d/%m/%Y')
        sub = final_df[final_df['dt'] == u_dt]
        
        row_dict = {'date': dt_str, 'date_fmt': date_fmt}
        for dam_name in dams:
            dam_sub = sub[sub['Dam Name'] == dam_name]
            if not dam_sub.empty:
                row_dict[f"{dam_name}_pct"] = float(dam_sub.iloc[0]['Current Live Storage (%)'])
                row_dict[f"{dam_name}_mcm"] = float(dam_sub.iloc[0]['Current Live Storage (MCM)'])
            else:
                row_dict[f"{dam_name}_pct"] = None
                row_dict[f"{dam_name}_mcm"] = None
        time_series.append(row_dict)

    all_records = []
    for _, r in final_df.iterrows():
        all_records.append({
            'date': r['date'],
            'iso_date': r['iso_date'],
            'time': r['Report Time'],
            'dam_name': r['Dam Name'],
            'current_live_mcm': float(r['Current Live Storage (MCM)']),
            'design_live_mcm': float(r['Design Live Storage (MCM)']),
            'current_pct': float(r['Current Live Storage (%)']),
            'last_year_pct': float(r['Last Year Storage (%)']),
            'status': str(r['Status'])
        })

    out_data = {
        'total_dates': len(unique_dts),
        'total_records': len(all_records),
        'latest': latest_records,
        'time_series': time_series,
        'all_records': all_records
    }

    with open("dam_data.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"✨ Successfully exported clean JSON ({len(all_records)} records, {len(unique_dts)} unique dates) to dam_data.json")

if __name__ == "__main__":
    clean_and_impute()
