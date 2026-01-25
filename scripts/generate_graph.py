import matplotlib.pyplot as plt
import pandas as pd
import glob
import os
import sys

def generate_dashboard_chart():
    print("📉 Initializing Imperial Visualizer...")
    
    # 1. Find the raw data files (The 'Shorthand' of Reality)
    files = sorted(glob.glob("data/noaa_solarwind/noaa_mag_*.csv"))
    
    if not files:
        print("⚠️ No data stream found. Visualizer standing by.")
        return

    # 2. Load the last 24 hours
    recent_files = files[-48:] 
    all_data = []
    
    print(f"   - Processing {len(recent_files)} data packets...")
    
    for f in recent_files:
        try:
            # Reading the raw numbers.
            df = pd.read_csv(f)
            
            # Normalize B-total to Imperial Scale
            # Logic: |B_total - Baseline| / Baseline
            if 'bt' in df.columns:
                df['chi_proxy'] = (df['bt'] - 5).abs() / (5 + 1e-9)
                df['timestamp'] = pd.to_datetime(df['time_tag'])
                all_data.append(df[['timestamp', 'chi_proxy']])
        except Exception:
            continue

    if not all_data:
        print("   - No valid magnetic data found.")
        return

    combined = pd.concat(all_data)
    combined = combined.sort_values('timestamp')

    # 3. Draw the Picture
    plt.figure(figsize=(10, 4), dpi=100)
    plt.style.use('dark_background')
    
    # The Reality (Green Line)
    plt.plot(combined['timestamp'], combined['chi_proxy'], color='#00ff00', linewidth=1, label='Observed Vacuum Stress')
    
    # The Law (Red Line at 0.15)
    plt.axhline(y=0.15, color='red', linestyle='--', linewidth=2, label='Universal Boundary (0.15)')
    
    plt.title(f"LUFT Observatory: Live Vacuum Stress Monitor", color='white')
    plt.xlabel("Time (UTC)")
    plt.ylabel("Chi Parameter (χ)")
    plt.grid(True, alpha=0.2)
    plt.legend(loc='upper left')
    
    # 4. Save the Evidence
    output_file = "reports/dashboard_chart.png"
    os.makedirs("reports", exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight')
    print(f"✅ Evidence generated: {output_file}")

if __name__ == "__main__":
    generate_dashboard_chart()
