import pandas as pd
import numpy as np
import sys
import os

# --- THE RESONANCE TARGETS ---
TARGET_PHASES = {
    'CHARGE_MODE': {'val': 1.3526, 'tol': 0.05, 'desc': 'Vacuum Compression (77.5°)'},
    'RELEASE_MODE': {'val': 4.0143, 'tol': 0.05, 'desc': 'Vacuum Snapback (230°)'}
}

def analyze_phase_data(file_path):
    print(f"\n--- INITIATING RESONANCE SCAN: {file_path} ---")
    
    try:
        # Load Data
        df = pd.read_csv(file_path)
        # Clean columns
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        
        # Look for the phase column (handle variations)
        phase_col = None
        for col in df.columns:
            if 'phase' in col and 'rad' in col:
                phase_col = col
                break
        
        if not phase_col:
            print("[ERROR] No 'phase_radians' column found.")
            return

        print(f"Data Loaded: {len(df)} records.")
        
        # Convert phase column to numeric, coercing errors to NaN
        df[phase_col] = pd.to_numeric(df[phase_col], errors='coerce')
        
        # Filter out rows with NaN phase values
        df_valid = df[df[phase_col].notna()].copy()
        print(f"Valid phase records: {len(df_valid)}")
        
        # 1. SEARCH FOR RESONANCE TARGETS
        print("\n[1] TARGET LOCK CHECK")
        print("------------------------------------------------")
        for name, target in TARGET_PHASES.items():
            # Filter for values within tolerance
            hits = df_valid[
                (df_valid[phase_col] >= target['val'] - target['tol']) & 
                (df_valid[phase_col] <= target['val'] + target['tol'])
            ]
            count = len(hits)
            pct = (count / len(df_valid)) * 100
            print(f"TARGET: {name} ({target['val']})")
            print(f"   -> COUNT: {count} events ({pct:.1f}%)")
            print(f"   -> PHYSICS: {target['desc']}")
            
            if count > 0:
                print(f"   -> LATEST: {hits['timestamp_utc'].iloc[-1] if 'timestamp_utc' in hits.columns else 'N/A'}")
            print("------------------------------------------------")

        # 2. CHI LIMIT CORRELATION
        if 'chi_amplitude' in df_valid.columns:
            print("\n[2] CHI SATURATION CORRELATION (Chi >= 0.15)")
            high_chi = df_valid[df_valid['chi_amplitude'] >= 0.15]
            print(f"   -> Saturation Events: {len(high_chi)}")
            
            if not high_chi.empty:
                # Check mean phase during saturation
                mean_phase = high_chi[phase_col].mean()
                print(f"   -> MEAN PHASE DURING SATURATION: {mean_phase:.4f} rad")
                
                # Check alignment with targets
                for name, target in TARGET_PHASES.items():
                    matches = high_chi[
                        (high_chi[phase_col] >= target['val'] - target['tol']) & 
                        (high_chi[phase_col] <= target['val'] + target['tol'])
                    ]
                    if not matches.empty:
                        print(f"   -> LOCKED TO {name} during {len(matches)} saturation events.")

    except Exception as e:
        print(f"[SYSTEM FAILURE] {e}")

if __name__ == "__main__":
    # Auto-run on 'data/solar_wind.csv' if no arg provided
    target_file = sys.argv[1] if len(sys.argv) > 1 else 'reports/latest_solar_data.csv'
    if os.path.exists(target_file):
        analyze_phase_data(target_file)
    else:
        print(f"File not found: {target_file}")
        print("Usage: python src/phase_correlator.py <path_to_csv>")
