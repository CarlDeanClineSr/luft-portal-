#!/usr/bin/env python3
"""
Example usage of the LUFT Imperial Math Core functions.

This script demonstrates how to use compute_luft_metrics and generate_storm_report
to analyze magnetic field data according to the Cline Transform methodology.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from imperial_math import compute_luft_metrics, generate_storm_report


def example_with_synthetic_data():
    """Example using synthetic magnetic field data."""
    print("=" * 60)
    print("EXAMPLE 1: Synthetic Data - Stable System")
    print("=" * 60)
    
    # Create synthetic magnetic field data (stable period)
    timestamps = pd.date_range('2025-01-01', periods=48, freq='h')
    b_values = [50000.0] * 48  # Stable magnetic field (50,000 nT)
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    # Apply the Cline Transform
    df = compute_luft_metrics(df)
    
    # Display results
    print("\nFirst 5 rows after applying Cline Transform:")
    print(df[['B', 'B_baseline', 'delta_B', 'chi', 'status']].head())
    
    print("\nLast 5 rows:")
    print(df[['B', 'B_baseline', 'delta_B', 'chi', 'status']].tail())
    
    # Generate report
    print("\n")
    generate_storm_report(df)
    print()


def example_with_storm_event():
    """Example with a simulated storm event."""
    print("=" * 60)
    print("EXAMPLE 2: Simulated Storm Event - 15% Perturbation")
    print("=" * 60)
    
    # Create data with a storm event
    timestamps = pd.date_range('2025-01-01', periods=72, freq='h')
    
    # Phase 1: Pre-storm (stable baseline)
    b_values = [50000.0] * 30
    
    # Phase 2: Storm onset - 15% increase (chi = 0.15, at boundary)
    b_values += [57500.0] * 21
    
    # Phase 3: Recovery
    b_values += [50000.0] * 21
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    # Apply the Cline Transform
    df = compute_luft_metrics(df)
    
    # Display storm period
    print("\nData around storm onset (rows 28-35):")
    print(df[['B', 'B_baseline', 'delta_B', 'chi', 'status']].iloc[28:36])
    
    # Focus on the peak period (rows 35-55 = 21 entries during storm)
    storm_period = df.iloc[35:56]
    print("\nStorm period analysis (21 entries during storm):")
    print(f"  AT_BOUNDARY count: {(storm_period['status'] == 'AT_BOUNDARY').sum()}")
    print(f"  BELOW count: {(storm_period['status'] == 'BELOW').sum()}")
    print(f"  PRECURSOR_MODE count: {(storm_period['status'] == 'PRECURSOR_MODE').sum()}")
    
    # Generate report for the storm period
    print("\nStorm Period Report:")
    generate_storm_report(storm_period)
    print()


def example_with_precursor_mode():
    """Example with precursor mode (chi > 0.15)."""
    print("=" * 60)
    print("EXAMPLE 3: Precursor Mode - 20% Perturbation")
    print("=" * 60)
    
    # Create data with precursor mode
    timestamps = pd.date_range('2025-01-01', periods=60, freq='h')
    
    # Stable baseline, then large perturbation
    b_values = [50000.0] * 30
    b_values += [60000.0] * 30  # 20% increase (chi = 0.20, precursor mode)
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    # Apply the Cline Transform
    df = compute_luft_metrics(df)
    
    # Display precursor period
    print("\nData around precursor onset (rows 28-35):")
    print(df[['B', 'B_baseline', 'delta_B', 'chi', 'status']].iloc[28:36])
    
    # Generate report
    print("\n")
    generate_storm_report(df)
    print()


def example_with_csv_file():
    """Example of how to use with a CSV file."""
    print("=" * 60)
    print("EXAMPLE 4: Loading from CSV (Template)")
    print("=" * 60)
    
    print("""
To use with your own data:

1. Load your CSV file:
   df = pd.read_csv('your_live_data.csv')
   
2. Ensure your DataFrame has:
   - A datetime index (or convert a column to datetime index)
   - A column named 'B' containing magnetic field measurements
   
3. Example conversion:
   df['timestamp'] = pd.to_datetime(df['timestamp'])
   df = df.set_index('timestamp')
   
4. Apply the Cline Transform:
   df = compute_luft_metrics(df)
   
5. Generate the report:
   generate_storm_report(df)

--- SAMPLE CODE ---

import pandas as pd
from imperial_math import compute_luft_metrics, generate_storm_report

# Load your data
df = pd.read_csv('your_live_data.csv')

# Convert timestamp to datetime and set as index
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')

# Apply the Logic
df = compute_luft_metrics(df)

# Get the Report
generate_storm_report(df)

# Optionally, save the results
df.to_csv('analyzed_data.csv')
""")


if __name__ == '__main__':
    # Run all examples
    example_with_synthetic_data()
    example_with_storm_event()
    example_with_precursor_mode()
    example_with_csv_file()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
