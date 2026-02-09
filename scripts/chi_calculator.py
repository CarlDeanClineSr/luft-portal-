import argparse
import pandas as pd
import numpy as np
import sys
import os

# Import The Law
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from imperial_physics_index import VacuumConstants, FieldDefinitions
    CHI_LIMIT = VacuumConstants.CHI_MAX
except ImportError:
    CHI_LIMIT = 0.150 # Fallback

def process_chi(file_path, output_path, quiet=False):
    if not quiet: print(f"Processing: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        
        # Detect Columns
        if 'B_R' in df.columns: 
            cols = ['B_R', 'B_T', 'B_N'] # PSP/Solar
        elif 'bx_gsm' in df.columns: 
            cols = ['bx_gsm', 'by_gsm', 'bz_gsm'] # Earth
        else:
            cols = [c for c in df.columns if 'b' in c.lower()][:3]

        if len(cols) < 3:
            print("Error: Vector columns not found.")
            return

        # 1. Magnitude
        df['B_total'] = np.sqrt(df[cols[0]]**2 + df[cols[1]]**2 + df[cols[2]]**2)
        
        # 2. Baseline (Rolling Mean)
        df['B_baseline'] = df['B_total'].rolling(window=60, center=True, min_periods=1).mean()
        
        # 3. Chi Calculation
        df['chi'] = np.abs(df['B_total'] - df['B_baseline']) / df['B_baseline']
        
        # 4. Enforce Index
        df['violation'] = df['chi'] > CHI_LIMIT
        
        # 5. Classify State
        if 'FieldDefinitions' in globals():
            df['state'] = df['chi'].apply(FieldDefinitions.classify_state)

        # Output Stats
        max_chi = df['chi'].max()
        violations = df['violation'].sum()
        
        if not quiet:
            print(f"   Max Chi: {max_chi:.4f}")
            print(f"   Violations > {CHI_LIMIT}: {violations}")

        if output_path:
            df.to_csv(output_path, index=False)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--quiet", action="store_true")
    # Legacy args ignored
    parser.add_argument("--time-col")
    parser.add_argument("--bx")
    parser.add_argument("--by")
    parser.add_argument("--bz")
    
    args = parser.parse_args()
    process_chi(args.file, args.output, args.quiet)
