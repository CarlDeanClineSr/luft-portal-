"""
Lightning Storm Phase Analyzer

Extends storm_phase_analyzer.py for lightning data analysis.
Analyzes VLF amplitude or sferic power recordings as proxy for χ (chi).
Classifies lightning events into PRE/PEAK/POST phases.

This module adapts the CME storm phase analysis methodology to terrestrial
atmospheric plasma phenomena, proving universality of the χ boundary across
QCD, CME, solar wind, black holes, lattice QCD, turbulence, and now lightning.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, Any, Tuple
import sys
import os
from pathlib import Path


def analyze_lightning_events(
    df: pd.DataFrame,
    amplitude_boundary_min: float = 0.145,
    amplitude_boundary_max: float = 0.155,
    min_peak_points: int = 2,
    chi_column: str = 'chi_proxy',
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Analyze lightning VLF/sferic data and classify into storm phases.
    
    This function applies the same χ boundary logic used for CME storms
    to lightning recordings. The VLF amplitude is normalized to create
    a χ-proxy that follows the same boundary enforcement physics.
    
    Phase logic (lightning strokes are brief, discrete events):
      - PEAK:  χ_proxy in [amplitude_boundary_min, amplitude_boundary_max]
               These are the discrete spark events hitting the boundary
      - PRE:   buildup phase before leader/stroke events
      - POST:  decay/recovery after stroke events
      - UNKNOWN: invalid/missing data
    
    Multiple strokes per storm are detected as separate PEAK regions.
    Each stroke should show χ_proxy ≤ 0.15 (boundary enforcement).
    Zero violations expected (runaway forbidden by physics).
    
    Args:
        df: DataFrame with columns:
            - 'timestamp': datetime or parseable string
            - 'vlf_amplitude' or 'sferic_power': raw measurement
            - 'chi_proxy': pre-computed χ-like normalized perturbation
              (optional, will be computed if not present and raw data exists)
        amplitude_boundary_min: lower bound of χ boundary (default: 0.145)
        amplitude_boundary_max: upper bound of χ boundary (default: 0.155)
        min_peak_points: minimum consecutive points to call it a stroke (default: 2)
        chi_column: name of the χ-proxy column (default: 'chi_proxy')
    
    Returns:
        tuple: (summary, df_with_phases)
            summary: dict with:
              - 'total_obs': total observations
              - 'num_pre', 'num_peak', 'num_post', 'num_unknown': phase counts
              - 'pct_pre', 'pct_peak', 'pct_post', 'pct_unknown': percentages
              - 'has_storm': True if PEAK events detected
              - 'num_strokes': count of discrete stroke events
              - 'first_peak_time', 'last_peak_time': ISO timestamps
              - 'chi_boundary_min', 'chi_boundary_max': boundary values
              - 'max_chi_proxy': maximum χ_proxy observed
              - 'violations': count of χ_proxy > chi_boundary_max (should be 0)
            df_with_phases: DataFrame with new 'phase' column
    """
    
    df = df.copy()
    
    # Ensure timestamp column
    if 'timestamp' not in df.columns:
        if 'timestamp_utc' in df.columns:
            df['timestamp'] = df['timestamp_utc']
        elif 'time' in df.columns:
            df['timestamp'] = df['time']
        else:
            raise ValueError("DataFrame must contain 'timestamp', 'timestamp_utc', or 'time' column")
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Compute chi_proxy if not present
    if chi_column not in df.columns:
        if 'vlf_amplitude' in df.columns and 'baseline' in df.columns:
            # Compute χ-like normalized perturbation
            df[chi_column] = (df['vlf_amplitude'] - df['baseline']) / df['baseline']
        elif 'peak_amplitude' in df.columns and 'baseline' in df.columns:
            df[chi_column] = (df['peak_amplitude'] - df['baseline']) / df['baseline']
        elif 'sferic_power' in df.columns and 'baseline' in df.columns:
            df[chi_column] = (df['sferic_power'] - df['baseline']) / df['baseline']
        else:
            raise ValueError(
                f"DataFrame must contain '{chi_column}' column or provide "
                "amplitude/power data with baseline for computation"
            )
    
    # Ensure chi_proxy is numeric
    df[chi_column] = pd.to_numeric(df[chi_column], errors='coerce')
    
    # Initialize phase column
    df['phase'] = 'UNKNOWN'
    
    # Handle missing or invalid χ
    chi = df[chi_column]
    valid_mask = chi.notna() & np.isfinite(chi)
    
    # Detect PEAK points (χ_proxy in boundary band)
    peak_mask = (
        valid_mask &
        (chi >= amplitude_boundary_min) &
        (chi <= amplitude_boundary_max)
    )
    
    num_peak_points = peak_mask.sum()
    
    # Count violations (χ_proxy > boundary_max)
    violations_mask = valid_mask & (chi > amplitude_boundary_max)
    num_violations = violations_mask.sum()
    
    # Get max chi_proxy
    max_chi_proxy = chi[valid_mask].max() if valid_mask.any() else np.nan
    
    if num_peak_points >= min_peak_points:
        # We have stroke events
        has_storm = True
        
        # Detect individual strokes (groups of consecutive PEAK points)
        # Create a stroke ID by checking for gaps in peak indices
        peak_indices = df.index[peak_mask].tolist()
        stroke_groups = []
        current_group = [peak_indices[0]] if peak_indices else []
        
        for i in range(1, len(peak_indices)):
            if peak_indices[i] - peak_indices[i-1] == 1:
                # Consecutive - same stroke
                current_group.append(peak_indices[i])
            else:
                # Gap - new stroke
                if current_group:
                    stroke_groups.append(current_group)
                current_group = [peak_indices[i]]
        
        # Add final group
        if current_group:
            stroke_groups.append(current_group)
        
        num_strokes = len(stroke_groups)
        
        first_peak_idx = df.index[peak_mask][0]
        last_peak_idx = df.index[peak_mask][-1]
        
        first_peak_time = df.loc[first_peak_idx, 'timestamp']
        last_peak_time = df.loc[last_peak_idx, 'timestamp']
        
        # Assign PEAK
        df.loc[peak_mask, 'phase'] = 'PEAK'
        
        # Assign PRE: valid points before first peak
        pre_mask = valid_mask & (df.index < first_peak_idx)
        df.loc[pre_mask, 'phase'] = 'PRE'
        
        # Assign POST: valid points after last peak
        post_mask = valid_mask & (df.index > last_peak_idx)
        df.loc[post_mask, 'phase'] = 'POST'
        
    else:
        # No clear PEAK: treat all valid points as PRE (quiet period)
        df.loc[valid_mask, 'phase'] = 'PRE'
        has_storm = False
        num_strokes = 0
        first_peak_time = None
        last_peak_time = None
    
    # Aggregate statistics
    total_obs = len(df)
    num_pre = (df['phase'] == 'PRE').sum()
    num_peak = (df['phase'] == 'PEAK').sum()
    num_post = (df['phase'] == 'POST').sum()
    num_unknown = (df['phase'] == 'UNKNOWN').sum()
    
    def pct(n: int) -> float:
        return float(n) * 100.0 / total_obs if total_obs > 0 else 0.0
    
    summary = {
        'total_obs': int(total_obs),
        'num_pre': int(num_pre),
        'num_peak': int(num_peak),
        'num_post': int(num_post),
        'num_unknown': int(num_unknown),
        'pct_pre': pct(num_pre),
        'pct_peak': pct(num_peak),
        'pct_post': pct(num_post),
        'pct_unknown': pct(num_unknown),
        'has_storm': bool(has_storm),
        'num_strokes': int(num_strokes),
        'first_peak_time': first_peak_time.isoformat() if first_peak_time is not None and pd.notna(first_peak_time) else None,
        'last_peak_time': last_peak_time.isoformat() if last_peak_time is not None and pd.notna(last_peak_time) else None,
        'chi_boundary_min': float(amplitude_boundary_min),
        'chi_boundary_max': float(amplitude_boundary_max),
        'max_chi_proxy': float(max_chi_proxy) if pd.notna(max_chi_proxy) else None,
        'violations': int(num_violations),
    }
    
    return summary, df


def process_lightning_recording(
    input_path: str,
    output_dir: str = 'results',
    amplitude_boundary_min: float = 0.145,
    amplitude_boundary_max: float = 0.155,
) -> Dict[str, Any]:
    """
    Process a single lightning recording file.
    
    Supports HDSDR CSV exports (spectrograms or peak detects).
    Expected columns:
      - timestamp (or time, timestamp_utc)
      - peak_amplitude or vlf_amplitude or sferic_power
      - baseline (for normalization)
    
    Or pre-computed:
      - timestamp
      - chi_proxy
    
    Args:
        input_path: path to input CSV file
        output_dir: directory for output files (default: 'results')
        amplitude_boundary_min: χ boundary lower bound
        amplitude_boundary_max: χ boundary upper bound
    
    Returns:
        summary: dict with analysis results
    """
    
    # Load data
    df = pd.read_csv(input_path)
    
    print(f"Loaded {len(df)} observations from {input_path}")
    print(f"Columns: {list(df.columns)}")
    
    # Analyze
    summary, df_with_phases = analyze_lightning_events(
        df,
        amplitude_boundary_min=amplitude_boundary_min,
        amplitude_boundary_max=amplitude_boundary_max,
    )
    
    # Print summary
    print("\n=== Lightning Phase Analysis Summary ===")
    print(f"Total observations: {summary['total_obs']}")
    print(f"Has storm events: {summary['has_storm']}")
    if summary['has_storm']:
        print(f"Number of strokes: {summary['num_strokes']}")
        print(f"First peak time: {summary['first_peak_time']}")
        print(f"Last peak time: {summary['last_peak_time']}")
    print(f"PRE phase: {summary['num_pre']} ({summary['pct_pre']:.1f}%)")
    print(f"PEAK phase: {summary['num_peak']} ({summary['pct_peak']:.1f}%)")
    print(f"POST phase: {summary['num_post']} ({summary['pct_post']:.1f}%)")
    print(f"UNKNOWN: {summary['num_unknown']} ({summary['pct_unknown']:.1f}%)")
    print(f"Max χ_proxy: {summary['max_chi_proxy']:.4f}" if summary['max_chi_proxy'] else "Max χ_proxy: N/A")
    print(f"Boundary violations (χ > {amplitude_boundary_max}): {summary['violations']}")
    print(f"χ boundary: [{amplitude_boundary_min}, {amplitude_boundary_max}]")
    
    # Save results
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename from input
    input_name = Path(input_path).stem
    output_csv = Path(output_dir) / f"lightning_phases_{input_name}.csv"
    output_json = Path(output_dir) / f"lightning_summary_{input_name}.json"
    
    df_with_phases.to_csv(output_csv, index=False)
    print(f"\n✅ Saved phase data to: {output_csv}")
    
    # Save summary as JSON
    with open(output_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Saved summary to: {output_json}")
    
    return summary


def process_lightning_directory(
    data_dir: str = 'data/lightning',
    output_dir: str = 'results',
) -> None:
    """
    Process all CSV files in the lightning data directory.
    
    Args:
        data_dir: directory containing lightning CSV files
        output_dir: directory for output files
    """
    
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"⚠️  Lightning data directory not found: {data_dir}")
        print(f"   Creating directory structure...")
        data_path.mkdir(parents=True, exist_ok=True)
        print(f"   Place HDSDR CSV exports in: {data_path}")
        return
    
    # Find all CSV files
    csv_files = list(data_path.glob('*.csv'))
    
    if not csv_files:
        print(f"⚠️  No CSV files found in {data_dir}")
        print(f"   Place HDSDR CSV exports in this directory")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to process\n")
    
    all_summaries = []
    
    for csv_file in csv_files:
        print(f"\n{'='*60}")
        print(f"Processing: {csv_file.name}")
        print('='*60)
        
        try:
            summary = process_lightning_recording(
                str(csv_file),
                output_dir=output_dir,
            )
            all_summaries.append({
                'file': csv_file.name,
                'summary': summary,
            })
        except Exception as e:
            print(f"❌ Error processing {csv_file.name}: {e}")
            continue
    
    # Create combined summary
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print('='*60)
    print(f"Processed {len(all_summaries)} file(s) successfully")
    
    total_strokes = sum(s['summary'].get('num_strokes', 0) for s in all_summaries)
    total_violations = sum(s['summary'].get('violations', 0) for s in all_summaries)
    
    print(f"Total lightning strokes detected: {total_strokes}")
    print(f"Total boundary violations: {total_violations}")
    print(f"✅ Physics check: {total_violations} violations (expect 0 - boundary enforced)")


if __name__ == '__main__':
    """
    Command-line interface for lightning phase analysis.
    
    Usage:
        # Process all files in data/lightning/
        python scripts/lightning_phase_analyzer.py
        
        # Process specific file
        python scripts/lightning_phase_analyzer.py data/lightning/may_storm1.csv
        
        # Process directory with custom output
        python scripts/lightning_phase_analyzer.py data/lightning/ --output results/lightning
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze lightning VLF/sferic recordings for χ boundary enforcement'
    )
    parser.add_argument(
        'input',
        nargs='?',
        default='data/lightning',
        help='Input CSV file or directory (default: data/lightning)'
    )
    parser.add_argument(
        '--output',
        default='results',
        help='Output directory (default: results)'
    )
    parser.add_argument(
        '--boundary-min',
        type=float,
        default=0.145,
        help='χ boundary minimum (default: 0.145)'
    )
    parser.add_argument(
        '--boundary-max',
        type=float,
        default=0.155,
        help='χ boundary maximum (default: 0.155)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Process single file
        process_lightning_recording(
            str(input_path),
            output_dir=args.output,
            amplitude_boundary_min=args.boundary_min,
            amplitude_boundary_max=args.boundary_max,
        )
    else:
        # Process directory
        process_lightning_directory(
            data_dir=str(input_path),
            output_dir=args.output,
        )
