#!/usr/bin/env python3
"""
luft_omni_crawler.py
====================
Autonomous Master Scanner for the LUFT Portal.
Recursively traverses all 21,000+ files to force out historical
signatures of Vacuum Tension (χ = 0.15) and the 20.55 Hz ring.

Author: Carl Dean Cline Sr.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import concurrent.futures
from datetime import datetime

# --- IMPERIAL CONSTANTS ---
CHI_TARGET = 0.15
CHI_TOLERANCE = 0.005
MODE_8_THRESHOLD = 0.800
F_RING = 20.55

def scan_csv_for_tension(filepath):
    """Scan historical CSVs for the 0.15 boundary and Mode 8 fractures."""
    try:
        # Flexible parser for deep historical files
        df = pd.read_csv(filepath, on_bad_lines='skip', engine='python', low_memory=False)
        
        # Locate the chi column regardless of naming conventions
        chi_col = next((col for col in df.columns if 'chi' in col.lower()), None)
        if not chi_col:
            return None
            
        df[chi_col] = pd.to_numeric(df[chi_col], errors='coerce')
        chi_data = df[chi_col].dropna()
        
        if len(chi_data) < 50:
            return None
            
        # Mathematical extraction
        max_chi = float(chi_data.max())
        median_chi = float(chi_data.median())
        
        # Calculate Attractor lock-in
        in_boundary = chi_data[(chi_data >= CHI_TARGET - CHI_TOLERANCE) & (chi_data <= CHI_TARGET + CHI_TOLERANCE)]
        attractor_pct = (len(in_boundary) / len(chi_data)) * 100
        
        # Check for Mode 8 Critical Failures
        mode_8_events = len(chi_data[chi_data >= MODE_8_THRESHOLD])
        
        return {
            "type": "Vacuum Tension (CSV)",
            "file": str(filepath),
            "observations": len(chi_data),
            "max_chi": max_chi,
            "attractor_pct": round(attractor_pct, 2),
            "mode_8_spikes": mode_8_events,
            "status": "VALID" if max_chi <= 0.16 else "CONTAINS FRACTURES"
        }
    except Exception:
        return None

def scan_wav_for_sidebands(filepath):
    """Placeholder for the existing wav_sideband_scan logic to be routed here."""
    # In full deployment, import your wav_sideband_scan.scan_for_sideband(filepath) here.
    return {
        "type": "RF Signature (WAV)",
        "file": str(filepath),
        "status": "QUEUED FOR DSP"
    }

def process_file(filepath):
    """Router: determines which mathematical interrogation to apply."""
    ext = filepath.suffix.lower()
    if ext == '.csv':
        return scan_csv_for_tension(filepath)
    elif ext == '.wav':
        return scan_wav_for_sidebands(filepath)
    return None

def main():
    root_dir = Path('.')
    print("="*70)
    print("LUFT OMNI-CRAWLER INITIALIZED")
    print("Targeting: χ=0.15 Limit | 20.55 Hz | Mode 8 Anomalies")
    print("="*70)
    
    all_files = list(root_dir.rglob('*.*'))
    target_files = [f for f in all_files if f.suffix.lower() in ['.csv', '.wav']]
    
    print(f"Discovered {len(all_files)} total files.")
    print(f"Isolated {len(target_files)} telemetry payloads for deep scan.")
    print("Commencing multi-threaded extraction...\n")
    
    results = []
    
    # Use Multiprocessing to chew through the repository at maximum speed
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_file, path): path for path in target_files}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            res = future.result()
            if res:
                results.append(res)
            
            # Progress heartbeat
            if i % 500 == 0:
                print(f"  ... scanned {i} / {len(target_files)} files")

    # Compile the Master Ledger
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    output_file = f"LUFT_OMNI_AUDIT_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "audit_timestamp": timestamp,
            "total_telemetry_files_scanned": len(target_files),
            "files_with_usable_signatures": len(results),
            "data": results
        }, f, indent=4)
        
    print("\n" + "="*70)
    print(f"SCAN COMPLETE.")
    print(f"Master Ledger compiled and saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
