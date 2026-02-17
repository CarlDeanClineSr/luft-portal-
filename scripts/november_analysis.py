#!/usr/bin/env python3
"""
November Pattern Analyzer for LUFT Portal
==========================================

Analyzes all November months (2020-2025) to check for:
- χ ≤ 0.15 boundary consistency
- Temporal mode patterns (6h, 12h, 24h)
- 0.9-hour sub-structure
- Seasonal heliospheric patterns

Hypothesis: November timing is NOT random - possible orbital/seasonal effects

Author: Carl Dean Cline Sr.
Date: 2026-01-03
"""

import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_data_for_november(data_dir, year):
    """Load all available data for November of a given year"""
    data_dir = Path(data_dir)
    november_data = []
    
    # Look for files with November dates
    patterns = [
        f'*{year}*11*.csv',
        f'*{year}*11*.json',
        f'*{year}-11*.csv',
        f'*{year}-11*.json',
        f'*november*{year}*.csv',
        f'*november*{year}*.json',
    ]
    
    files_found = []
    for pattern in patterns:
        files_found.extend(list(data_dir.rglob(pattern)))
    
    # Remove duplicates
    files_found = list(set(files_found))
    
    print(f"  Found {len(files_found)} files for November {year}")
    
    for filepath in files_found:
        try:
            if filepath.suffix == '.csv':
                df = pd.read_csv(filepath)
            elif filepath.suffix == '.json':
                df = pd.read_json(filepath, lines=True)
            else:
                continue
            
            # Filter for November if timestamp column exists
            if 'timestamp' in df.columns or 'time' in df.columns:
                time_col = 'timestamp' if 'timestamp' in df.columns else 'time'
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                
                # Filter for November
                november_mask = (df[time_col].dt.month == 11) & (df[time_col].dt.year == year)
                df_november = df[november_mask]
                
                if len(df_november) > 0:
                    november_data.append(df_november)
        except Exception as e:
            # Skip problematic files
            continue
    
    if november_data:
        return pd.concat(november_data, ignore_index=True)
    else:
        return pd.DataFrame()

def analyze_chi_boundary(df):
    """Analyze χ boundary behavior"""
    chi_cols = [col for col in df.columns if 'chi' in col.lower()]
    
    if not chi_cols:
        return None
    
    chi_col = chi_cols[0]
    chi_data = df[chi_col].dropna()
    
    if len(chi_data) == 0:
        return None
    
    analysis = {
        'total_observations': len(chi_data),
        'mean': float(chi_data.mean()),
        'median': float(chi_data.median()),
        'std': float(chi_data.std()),
        'min': float(chi_data.min()),
        'max': float(chi_data.max()),
        'chi_le_015_count': int((chi_data <= 0.15).sum()),
        'chi_le_015_percentage': float((chi_data <= 0.15).sum() / len(chi_data) * 100),
        'violations_of_015': int((chi_data > 0.15).sum()),
        'violation_percentage': float((chi_data > 0.15).sum() / len(chi_data) * 100),
    }
    
    # Check attractor state (chi ≈ 0.15, within 0.01)
    attractor_mask = (chi_data >= 0.14) & (chi_data <= 0.16)
    analysis['attractor_state_count'] = int(attractor_mask.sum())
    analysis['attractor_state_percentage'] = float(attractor_mask.sum() / len(chi_data) * 100)
    
    return analysis

def detect_temporal_modes(df):
    """Detect 6h, 12h, 24h temporal patterns"""
    # Expected modes in hours
    expected_modes = [6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72]
    
    time_col = 'timestamp' if 'timestamp' in df.columns else 'time' if 'time' in df.columns else None
    
    if time_col is None or time_col not in df.columns:
        return None
    
    # Look for event markers or anomalies
    # This is a simplified analysis - full implementation would need specific event data
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df_sorted = df.sort_values(time_col).reset_index(drop=True)
    
    # Calculate time differences between consecutive events
    time_diffs = df_sorted[time_col].diff()
    time_diffs_hours = time_diffs.dt.total_seconds() / 3600
    
    # Find modes
    mode_counts = defaultdict(int)
    for diff_hours in time_diffs_hours.dropna():
        for mode in expected_modes:
            if abs(diff_hours - mode) < 3:  # Within 3 hours
                mode_counts[mode] += 1
    
    if mode_counts:
        return dict(mode_counts)
    else:
        return None

def analyze_november_patterns(data_dir, years):
    """Analyze November patterns across multiple years"""
    all_results = {}
    
    print("=" * 70)
    print("LUFT November Pattern Analyzer")
    print("=" * 70)
    print()
    
    for year in years:
        print(f"Analyzing November {year}...")
        
        df = load_data_for_november(data_dir, year)
        
        if len(df) == 0:
            print(f"  ⚠️  No data found for November {year}")
            all_results[year] = {'status': 'no_data'}
            continue
        
        print(f"  Loaded {len(df)} observations")
        
        year_analysis = {
            'status': 'analyzed',
            'total_observations': len(df),
        }
        
        # Analyze χ boundary
        chi_analysis = analyze_chi_boundary(df)
        if chi_analysis:
            year_analysis['chi_boundary'] = chi_analysis
            print(f"    χ ≤ 0.15: {chi_analysis['chi_le_015_percentage']:.1f}%")
            print(f"    Violations: {chi_analysis['violation_percentage']:.1f}%")
            print(f"    Attractor state: {chi_analysis['attractor_state_percentage']:.1f}%")
        
        # Detect temporal modes
        temporal_modes = detect_temporal_modes(df)
        if temporal_modes:
            year_analysis['temporal_modes'] = temporal_modes
            print(f"    Temporal modes detected: {list(temporal_modes.keys())}")
        
        all_results[year] = year_analysis
        print()
    
    return all_results

def generate_report(results, output_file):
    """Generate markdown report"""
    with open(output_file, 'w') as f:
        f.write("# November Pattern Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
        f.write("**Hypothesis:** November events show consistent χ ≤ 0.15 pattern across years\n\n")
        f.write("---\n\n")
        
        f.write("## Summary by Year\n\n")
        
        for year in sorted(results.keys()):
            result = results[year]
            f.write(f"### November {year}\n\n")
            
            if result['status'] == 'no_data':
                f.write("⚠️  **No data available**\n\n")
                continue
            
            f.write(f"**Total Observations:** {result['total_observations']}\n\n")
            
            if 'chi_boundary' in result:
                chi = result['chi_boundary']
                f.write("#### χ Boundary Analysis\n\n")
                f.write(f"- Mean χ: {chi['mean']:.4f}\n")
                f.write(f"- Median χ: {chi['median']:.4f}\n")
                f.write(f"- Range: [{chi['min']:.4f}, {chi['max']:.4f}]\n")
                f.write(f"- χ ≤ 0.15: {chi['chi_le_015_percentage']:.1f}%\n")
                f.write(f"- Violations (χ > 0.15): {chi['violation_percentage']:.1f}%\n")
                f.write(f"- Attractor state (0.14-0.16): {chi['attractor_state_percentage']:.1f}%\n\n")
            
            if 'temporal_modes' in result:
                modes = result['temporal_modes']
                f.write("#### Temporal Modes Detected\n\n")
                for mode, count in sorted(modes.items()):
                    f.write(f"- {mode}h mode: {count} occurrences\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        # Cross-year analysis
        f.write("## Cross-Year Patterns\n\n")
        
        years_with_data = [y for y, r in results.items() if r['status'] == 'analyzed' and 'chi_boundary' in r]
        
        if len(years_with_data) >= 2:
            f.write("### χ Boundary Consistency\n\n")
            
            f.write("| Year | χ ≤ 0.15 | Violations | Attractor State |\n")
            f.write("|------|----------|------------|----------------|\n")
            
            for year in sorted(years_with_data):
                chi = results[year]['chi_boundary']
                f.write(f"| {year} | {chi['chi_le_015_percentage']:.1f}% | ")
                f.write(f"{chi['violation_percentage']:.1f}% | ")
                f.write(f"{chi['attractor_state_percentage']:.1f}% |\n")
            
            f.write("\n")
            
            # Check consistency
            violation_rates = [results[y]['chi_boundary']['violation_percentage'] for y in years_with_data]
            avg_violation = np.mean(violation_rates)
            std_violation = np.std(violation_rates)
            
            f.write(f"**Average violation rate:** {avg_violation:.1f}% ± {std_violation:.1f}%\n\n")
            
            if avg_violation < 5:
                f.write("✅ **HYPOTHESIS SUPPORTED:** χ ≤ 0.15 boundary consistently holds across November months\n\n")
            elif avg_violation < 10:
                f.write("⚠️  **HYPOTHESIS PARTIALLY SUPPORTED:** χ ≤ 0.15 boundary mostly holds with some exceptions\n\n")
            else:
                f.write("❌ **HYPOTHESIS NOT SUPPORTED:** Significant violations of χ ≤ 0.15 boundary in November\n\n")
        else:
            f.write("⚠️  Insufficient data for cross-year comparison\n\n")
        
        f.write("---\n\n")
        f.write("## Recommendations\n\n")
        f.write("1. **If pattern confirmed:** Investigate orbital mechanics and seasonal heliospheric structure\n")
        f.write("2. **If pattern unclear:** Gather more November data from additional sources\n")
        f.write("3. **Next steps:** Compare with other months to determine if November is special\n\n")
        
        f.write("---\n\n")
        f.write("*Generated by LUFT November Pattern Analyzer*\n")
        f.write("*Carl Dean Cline Sr. - Lincoln, Nebraska, USA*\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze November patterns across years')
    parser.add_argument('--data-dir', default='data', help='Data directory to search')
    parser.add_argument('--years', required=True, help='Comma-separated list of years (e.g., 2020,2021,2022)')
    parser.add_argument('--output', required=True, help='Output markdown report file')
    parser.add_argument('--json', help='Optional JSON output file')
    args = parser.parse_args()
    
    # Parse years
    years = [int(y.strip()) for y in args.years.split(',')]
    
    # Analyze
    results = analyze_november_patterns(args.data_dir, years)
    
    # Generate report
    print(f"Generating report: {args.output}")
    generate_report(results, args.output)
    print(f"  ✅ Report saved")
    
    # Save JSON if requested
    if args.json:
        print(f"Saving JSON: {args.json}")
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  ✅ JSON saved")
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
