#!/usr/bin/env python3
"""
Compute True Plasma χ from INTERMAGNET CSV data
Decouples the static Earth iron core from the dynamic external plasma medium.
"""
import argparse
import pandas as pd
import numpy as np

def compute_chi(input_csv, output_csv, baseline_hours=24):
    print(f"Processing ground station telemetry: {input_csv}")
    
    # Load the raw telemetry
    df = pd.read_csv(input_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Ensure data is sorted temporally
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 1. Isolate the Iron Core (The Static Field)
    # Using the 5th percentile establishes the quietest baseline of the local environment
    # representing the static iron core (~49,000 nT), while ignoring artificial zero-dropouts.
    core_field = df['B_total'].quantile(0.05)
    
    # 2. Extract the Plasma Medium (The External Field)
    # Subtracting the core leaves only the magnetic footprint of the plasma 
    # sitting above the station (typically 10 nT to 60 nT).
    df['B_plasma_raw'] = df['B_total'] - core_field
    
    # Prevent negative physical baselines caused by slight core diurnal shifts
    df['B_plasma_raw'] = df['B_plasma_raw'].clip(lower=0.1)
    
    # 3. Establish the Dynamic Plasma Baseline
    # INTERMAGNET provides 1-minute data. 24 hours = 1440 minutes.
    window_size = int(baseline_hours * 60)
    
    # Calculate rolling baseline of the plasma medium itself
    df['B_plasma_baseline'] = df['B_plasma_raw'].rolling(
        window=window_size, 
        min_periods=1, 
        center=True
    ).median()
    
    # 4. Calculate the Kinetic Perturbation (Delta B)
    # How hard is the plasma being displaced from its local resting state?
    df['delta_B'] = df['B_plasma_raw'] - df['B_plasma_baseline']
    
    # 5. Calculate True Structural Chi
    # Delta B divided by the Plasma Baseline (not the iron core).
    df['chi'] = np.abs(df['delta_B']) / df['B_plasma_baseline']
    
    # Include original total field for auditing, but export the corrected metrics
    columns_to_export = ['timestamp', 'Bx', 'By', 'Bz', 'B_total', 'B_plasma_raw', 'B_plasma_baseline', 'delta_B', 'chi']
    
    # Save the mathematical audit
    df[columns_to_export].to_csv(output_csv, index=False)
    
    print("==================================================")
    print(f"Local Iron Core Subtracted: {core_field:.2f} nT")
    print(f"Max Ground Plasma Tension (\u03c7): {df['chi'].max():.3f}")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--baseline-hours', type=int, default=24)
    args = parser.parse_args()
    
    compute_chi(args.input, args.output, args.baseline_hours)
