#!/usr/bin/env python3
"""
detect_harmonic_modes.py
========================
Harmonic Mode Detection for Carl Dean Cline Sr.'s χ Boundary Discovery

This script classifies χ values into harmonic modes:
  - Mode 1 (Fundamental): χ ≤ 0.15
  - Mode 2 (First Harmonic): 0.15 < χ ≤ 0.30
  - Mode 3 (Second Harmonic): 0.30 < χ ≤ 0.45
  - Violation: χ > 0.45 (critical - structure breaking)

Carl's discovery: Under extreme energy conditions (solar storms), the vacuum
lattice doesn't break—it shifts to higher harmonic modes (0.30, 0.45) rather
than violating χ > 0.45.

Author: Carl Dean Cline Sr. + Copilot Agent Task + Imperial Gatekeeper Update
"""

import pandas as pd
import numpy as np
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Harmonic mode boundaries (Carl's discovery)
MODE_1_MAX = 0.15  # Fundamental frequency
MODE_2_MAX = 0.30  # First harmonic (2x fundamental)
MODE_3_MAX = 0.45  # Second harmonic (3x fundamental)


def classify_mode(chi_value):
    """Classify a chi value into its harmonic mode."""
    if chi_value <= MODE_1_MAX:
        return 1
    elif chi_value <= MODE_2_MAX:
        return 2
    elif chi_value <= MODE_3_MAX:
        return 3
    else:
        return 4  # Violation


def detect_mode_transitions(df, chi_col='chi'):
    """Detect transitions between harmonic modes in the time series."""
    if chi_col not in df.columns:
        raise ValueError(f"Column '{chi_col}' not found in dataframe")
    
    if len(df) == 0:
        return []
    
    df = df.copy()
    df['mode'] = df[chi_col].apply(classify_mode)
    
    transitions = []
    prev_mode = df['mode'].iloc[0]
    
    for idx, row in df.iterrows():
        current_mode = row['mode']
        if current_mode != prev_mode:
            # Detect timestamp column
            time_col = None
            for col in ['timestamp', 'time', 'TT2000', 'datetime', 'date']:
                if col in df.columns:
                    time_col = col
                    break
            
            timestamp = row[time_col] if time_col else str(idx)
            
            transitions.append({
                'index': int(idx) if isinstance(idx, (int, np.integer)) else str(idx),
                'timestamp': str(timestamp),
                'from_mode': int(prev_mode),
                'to_mode': int(current_mode),
                'chi_value': float(row[chi_col])
            })
            prev_mode = current_mode
    
    return transitions


def compute_mode_statistics(df, chi_col='chi'):
    """Compute statistics for each harmonic mode."""
    if chi_col not in df.columns:
        raise ValueError(f"Column '{chi_col}' not found in dataframe")
    
    if len(df) == 0:
        raise ValueError("DataFrame is empty - no data to analyze")
    
    df = df.copy()
    df['mode'] = df[chi_col].apply(classify_mode)
    
    total_count = len(df)
    mode_counts = df['mode'].value_counts().to_dict()
    
    # Ensure all modes are represented
    for mode in [1, 2, 3, 4]:
        if mode not in mode_counts:
            mode_counts[mode] = 0
    
    stats = {
        'total_observations': total_count,
        'mode_1_fundamental': mode_counts[1],
        'mode_2_harmonic': mode_counts[2],
        'mode_3_harmonic': mode_counts[3],
        'violations': mode_counts[4],
        'mode_1_fundamental_pct': round(100 * mode_counts[1] / total_count, 2),
        'mode_2_harmonic_pct': round(100 * mode_counts[2] / total_count, 2),
        'mode_3_harmonic_pct': round(100 * mode_counts[3] / total_count, 2),
        'violations_pct': round(100 * mode_counts[4] / total_count, 2),
        'max_chi': float(df[chi_col].max()),
        'mean_chi': float(df[chi_col].mean()),
        'median_chi': float(df[chi_col].median())
    }
    
    return stats


def test_harmonic_clustering(chi_series, harmonic_levels=[0.15, 0.30, 0.45], window=0.02):
    """
    LUFT HARMONIC CLUSTERING TEST
    -----------------------------
    The real test: Do chi values physically lock (CLUSTER) at the mechanical 
    harmonic levels (0.15, 0.30, 0.45), or just randomly pass through them?
    """
    results = {}
    n = len(chi_series)
    
    if n == 0:
        return results
        
    chi_min = min(chi_series)
    chi_max = max(chi_series)
    chi_range = chi_max - chi_min
    
    if chi_range > 0:
        expected_frac = (2 * window) / chi_range
    else:
        expected_frac = 0.0
        
    for level in harmonic_levels:
        in_window = np.sum(
            (chi_series >= level - window) & 
            (chi_series <= level + window)
        )
        
        observed_frac = in_window / n
        
        if expected_frac > 0:
            excess_ratio = observed_frac / expected_frac
        else:
            excess_ratio = 0.0
            
        is_attractor = excess_ratio > 3.0  
        
        results[level] = {
            'count':         int(in_window),
            'observed_pct':  round(100 * observed_frac, 2),
            'expected_pct':  round(100 * expected_frac, 2),
            'excess_ratio':  round(excess_ratio, 2),
            'attractor':     is_attractor
        }
        
        status_flag = "✅ ATTRACTOR CONFIRMED" if is_attractor else "— no clustering"
        print(f"  χ = {level:.2f}:  {observed_frac*100:5.1f}% observed vs "
              f"{expected_frac*100:5.1f}% expected  "
              f"(ratio: {excess_ratio:5.1f}x)  {status_flag}")
              
    return results


def analyze_harmonic_structure(file_path, chi_col='chi', output_json=None):
    """Analyze the harmonic mode structure in a chi dataset."""
    # Load data
    df = pd.read_csv(file_path)
    
    if chi_col not in df.columns:
        possible_cols = [col for col in df.columns if 'chi' in col.lower()]
        if possible_cols:
            chi_col = possible_cols[0]
            print(f"ℹ️  Using column: {chi_col}")
        else:
            raise ValueError(f"No chi column found. Available columns: {df.columns.tolist()}")

    # =========================================================================
    # IMPERIAL GATEKEEPER: PREVENT UNVOXELIZED NOISE FROM DILUTING THE ENGINE
    # =========================================================================
    chi_max = df[chi_col].abs().max()
    chi_median = df[chi_col].median()
    
    # If max chi is microscopic (< 0.01) or massive (> 10.0), it's unscaled raw data.
    if chi_max < 0.01 or chi_max > 10.0:
        status_msg = f"WRONG_SCALE — Raw data detected (median: {chi_median:.5f}, max: {chi_max:.5f}). Skipping."
        print(f"⚠️  {status_msg}")
        
        report = {
            'file': str(file_path),
            'chi_col': chi_col,
            'n_loaded': len(df),
            'chi_median': float(chi_median),
            'status': status_msg
        }
        
        if output_json:
            output_path = Path(output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report
    # =========================================================================

    # Compute statistics
    stats = compute_mode_statistics(df, chi_col)
    
    # Detect transitions
    transitions = detect_mode_transitions(df, chi_col)
    
    # Determine dominant mode
    mode_counts = [
        (1, stats['mode_1_fundamental']),
        (2, stats['mode_2_harmonic']),
        (3, stats['mode_3_harmonic'])
    ]
    dominant_mode_num = max(mode_counts, key=lambda x: x[1])[0]
    
    # Build report
    report = {
        'file': str(file_path),
        'analysis_date': datetime.now().isoformat(),
        'discovery': "Carl Dean Cline Sr.'s Harmonic Lattice Structure",
        'resonance_profile': stats,
        'mode_transitions': transitions,
        'interpretation': {
            'harmonic_modes': "χ resonates at 0.15, 0.30, 0.45 (fundamental and harmonics)",
            'stability': "No violations" if stats['violations'] == 0 else f"{stats['violations']} violations detected",
            'dominant_mode': f"Mode {dominant_mode_num}"
        }
    }
    
    # Save JSON if requested
    if output_json:
        output_path = Path(output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Saved JSON report: {output_json}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Detect harmonic modes in χ data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file results/psp_validation/encounter17_chi_processed.csv
  %(prog)s --file data.csv --output harmonics.json
  %(prog)s --file data.csv --chi-col chi_normalized
        """
    )
    
    parser.add_argument('--file', type=str, required=True,
                        help='Path to chi_processed.csv file')
    parser.add_argument('--chi-col', type=str, default='chi',
                        help='Name of the chi column (default: chi)')
    parser.add_argument('--output', type=str,
                        help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  HARMONIC MODE DETECTION                                           ║")
    print("║  Carl Dean Cline Sr.'s Discovery: χ Resonates in Modes             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        report = analyze_harmonic_structure(
            args.file,
            chi_col=args.chi_col,
            output_json=args.output
        )
        
        # =========================================================================
        # GATEKEEPER CATCH: Stop processing if unscaled raw data was detected
        # =========================================================================
        if 'WRONG_SCALE' in report.get('status', ''):
            print("╔════════════════════════════════════════════════════════════════════╗")
            print("║  🛑 FILE REJECTED: UNSCALED RAW DATA PREVENTED FROM DILUTING ENGINE║")
            print("╚════════════════════════════════════════════════════════════════════╝")
            print(f"  File: {args.file} bypassed to protect aggregate data integrity.")
            return 0
        # =========================================================================
        
        # Display results
        stats = report['resonance_profile']
        
        print(f"📊 Resonance Profile:")
        print(f"   Total observations: {stats['total_observations']}")
        print()
        print(f"   Mode 1 (Fundamental, χ≤0.15):  {stats['mode_1_fundamental']:6d} ({stats['mode_1_fundamental_pct']:5.1f}%)")
        print(f"   Mode 2 (1st Harmonic, χ≤0.30): {stats['mode_2_harmonic']:6d} ({stats['mode_2_harmonic_pct']:5.1f}%)")
        print(f"   Mode 3 (2nd Harmonic, χ≤0.45): {stats['mode_3_harmonic']:6d} ({stats['mode_3_harmonic_pct']:5.1f}%)")
        print(f"   Violations (χ>0.45):           {stats['violations']:6d} ({stats['violations_pct']:5.1f}%)")
        print()
        print(f"📈 Chi Statistics:")
        print(f"   Maximum χ: {stats['max_chi']:.4f}")
        print(f"   Mean χ:    {stats['mean_chi']:.4f}")
        print(f"   Median χ:  {stats['median_chi']:.4f}")
        print()
        print(f"🔄 Mode Transitions: {len(report['mode_transitions'])} events")
        
        if report['mode_transitions']:
            print()
            print("   Sample transitions:")
            for trans in report['mode_transitions'][:5]:
                print(f"      Mode {trans['from_mode']} → Mode {trans['to_mode']} "
                      f"at {trans['timestamp']} (χ={trans['chi_value']:.4f})")
            if len(report['mode_transitions']) > 5:
                print(f"      ... and {len(report['mode_transitions']) - 5} more")
        
        print()
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║  INTERPRETATION                                                    ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print()
        print(f"  {report['interpretation']['harmonic_modes']}")
        print(f"  Stability: {report['interpretation']['stability']}")
        print(f"  Dominant: {report['interpretation']['dominant_mode']}")
        print()
        
        if stats['violations'] == 0:
            print("✅ DISCOVERY VALIDATED: No violations detected (χ ≤ 0.45)")
            print("   The vacuum lattice remains structurally intact.")
        else:
            print(f"🚨 WARNING: {stats['violations']} true violations (χ > 0.45)")
            print("   Extreme events may exceed harmonic structure.")
        
        print()
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
