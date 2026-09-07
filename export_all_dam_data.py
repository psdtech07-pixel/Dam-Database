import pandas as pd
import json
from pathlib import Path

def export_data():
    csv_file = Path("Maharashtra_5_Dams_Data.csv")
    csv_10y = Path("Maharashtra_5_Dams_10Year_Data.csv")
    
    dfs = []
    if csv_file.exists():
        dfs.append(pd.read_csv(csv_file))
    if csv_10y.exists():
        dfs.append(pd.read_csv(csv_10y))
        
    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')

    # Standardize column names
    col_map = {
        'Report Date': 'date',
        'Report Time': 'time',
        'Dead Storage (MCM)': 'dead_mcm',
        'Design Live Storage (MCM)': 'design_live_mcm',
        'Design Gross Storage (MCM)': 'design_gross_mcm',
        'Current Live Storage (MCM)': 'current_live_mcm',
        'Current Gross Storage (MCM)': 'current_gross_mcm',
        'Current Live Storage (%)': 'current_pct',
        'Last Year Storage (%)': 'last_year_pct',
        'Status': 'status',
        'Dam Name': 'dam_name'
    }
    df = df.rename(columns=col_map)
    
    # Drop exact duplicates
    df = df.drop_duplicates(subset=['date', 'dam_name'])

    # Parse ISO date for proper sorting
    df['iso_date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['iso_date']).sort_values('iso_date')

    dams = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar']

    # Get latest record for each dam
    latest_records = {}
    for dam in dams:
        dam_df = df[df['dam_name'] == dam]
        if not dam_df.empty:
            last_row = dam_df.iloc[-1]
            latest_records[dam] = {
                'date': last_row['date'],
                'time': last_row['time'],
                'dead_mcm': float(last_row['dead_mcm']) if pd.notnull(last_row['dead_mcm']) else 0,
                'design_live_mcm': float(last_row['design_live_mcm']) if pd.notnull(last_row['design_live_mcm']) else 0,
                'design_gross_mcm': float(last_row['design_gross_mcm']) if pd.notnull(last_row['design_gross_mcm']) else 0,
                'current_live_mcm': float(last_row['current_live_mcm']) if pd.notnull(last_row['current_live_mcm']) else 0,
                'current_gross_mcm': float(last_row['current_gross_mcm']) if pd.notnull(last_row['current_gross_mcm']) else 0,
                'current_pct': float(last_row['current_pct']) if pd.notnull(last_row['current_pct']) else 0,
                'last_year_pct': float(last_row['last_year_pct']) if pd.notnull(last_row['last_year_pct']) else 0,
                'status': str(last_row['status'])
            }

    # Time series pivoting
    unique_dates = df['iso_date'].unique()
    time_series = []
    
    for dt in unique_dates:
        dt_str = pd.to_datetime(dt).strftime('%Y-%m-%d')
        date_fmt = pd.to_datetime(dt).strftime('%d/%m/%Y')
        sub = df[df['iso_date'] == dt]
        
        row_dict = {'date': dt_str, 'date_fmt': date_fmt}
        for dam in dams:
            dam_sub = sub[sub['dam_name'] == dam]
            if not dam_sub.empty:
                row_dict[f"{dam}_pct"] = float(dam_sub.iloc[0]['current_pct']) if pd.notnull(dam_sub.iloc[0]['current_pct']) else None
                row_dict[f"{dam}_mcm"] = float(dam_sub.iloc[0]['current_live_mcm']) if pd.notnull(dam_sub.iloc[0]['current_live_mcm']) else None
            else:
                row_dict[f"{dam}_pct"] = None
                row_dict[f"{dam}_mcm"] = None
        time_series.append(row_dict)

    # All individual records
    all_records = []
    for _, r in df.iterrows():
        all_records.append({
            'date': r['date'],
            'iso_date': r['iso_date'].strftime('%Y-%m-%d'),
            'time': r['time'] if pd.notnull(r['time']) else '',
            'dam_name': r['dam_name'],
            'current_live_mcm': float(r['current_live_mcm']) if pd.notnull(r['current_live_mcm']) else 0,
            'design_live_mcm': float(r['design_live_mcm']) if pd.notnull(r['design_live_mcm']) else 0,
            'current_pct': float(r['current_pct']) if pd.notnull(r['current_pct']) else 0,
            'last_year_pct': float(r['last_year_pct']) if pd.notnull(r['last_year_pct']) else 0,
            'status': str(r['status']) if pd.notnull(r['status']) else 'Success'
        })

    out_data = {
        'total_dates': len(unique_dates),
        'total_records': len(all_records),
        'latest': latest_records,
        'time_series': time_series,
        'all_records': all_records
    }

    with open("dam_data.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully exported {len(all_records)} records across {len(unique_dates)} dates to dam_data.json")

if __name__ == "__main__":
    export_data()
