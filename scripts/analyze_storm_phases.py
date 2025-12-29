#!/usr/bin/env python3
"""
Example usage of the storm phase analyzer with CME heartbeat log data.

This script demonstrates how to:
1. Load χ timeseries from CSV
2. Analyze storm phases
3. Save results (JSON summary and CSV with phases)
4. Display summary statistics
"""

import pandas as pd
import json
from pathlib import Path
import sys

# Add parent directory to path to import storm_phase_analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))

from storm_phase_analyzer import analyze_storm_phases


def main():
    """Main function to analyze storm phases."""
    
    # Define paths
    data_dir = Path(__file__).parent.parent / 'data'
    input_csv = data_dir / 'cme_heartbeat_log_2025_12.csv'
    output_csv = data_dir / 'cme_heartbeat_log_2025_12_with_phases.csv'
    output_json = data_dir / 'storm_phase_summary.json'
    
    # Check if input file exists
    if not input_csv.exists():
        print(f"Error: Input file not found: {input_csv}")
        print("Please ensure the CME heartbeat log exists.")
        return 1
    
    print(f"Loading χ timeseries from: {input_csv}")
    # Handle CSV files with malformed rows
    try:
        df = pd.read_csv(input_csv)
    except pd.errors.ParserError:
        # Skip bad lines if the CSV has formatting issues
        df = pd.read_csv(input_csv, on_bad_lines='skip')
    print(f"Loaded {len(df)} observations")
    print()
    
    # Analyze storm phases
    print("Analyzing storm phases...")
    summary, df_with_phases = analyze_storm_phases(
        df,
        chi_boundary_min=0.145,
        chi_boundary_max=0.155,
        min_peak_points=3,
    )
    print("Analysis complete!")
    print()
    
    # Save updated CSV with phase column
    print(f"Saving CSV with phases to: {output_csv}")
    df_with_phases.to_csv(output_csv, index=False)
    print("CSV saved!")
    print()
    
    # Save summary for dashboard (JSON)
    print(f"Saving summary to: {output_json}")
    output_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("Summary saved!")
    print()
    
    # Display summary
    print("=" * 60)
    print("STORM PHASE ANALYSIS SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2))
    print("=" * 60)
    print()
    
    # Display phase distribution
    phase_counts = df_with_phases['phase'].value_counts()
    print("Phase Distribution:")
    for phase, count in phase_counts.items():
        pct = (count / len(df_with_phases)) * 100
        print(f"  {phase:8s}: {count:4d} ({pct:5.2f}%)")
    print()
    
    if summary['has_storm']:
        print(f"✓ Storm detected!")
        print(f"  First peak: {summary['first_peak_time']}")
        print(f"  Last peak:  {summary['last_peak_time']}")
    else:
        print("○ No storm detected (quiet period)")
    
    print()
    print("Analysis complete!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
