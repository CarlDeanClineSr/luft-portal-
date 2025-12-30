#!/usr/bin/env python3
"""
Analyze storm phases and emit:
- data/storm_phase_summary.json (counts & times)
- data/storm_phase_metrics.json (per-phase avg/max/at-boundary)
- data/cme_heartbeat_log_2025_12_with_phases.csv (labeled rows)
"""

import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from storm_phase_analyzer import analyze_storm_phases

def main():
    data_dir = Path(__file__).parent.parent / 'data'
    input_csv = data_dir / 'cme_heartbeat_log_2025_12.csv'
    output_csv = data_dir / 'cme_heartbeat_log_2025_12_with_phases.csv'
    summary_json = data_dir / 'storm_phase_summary.json'
    metrics_json = data_dir / 'storm_phase_metrics.json'

    if not input_csv.exists():
        print(f"Error: Input file not found: {input_csv}")
        return 1

    try:
        df = pd.read_csv(input_csv)
    except pd.errors.ParserError:
        df = pd.read_csv(input_csv, on_bad_lines='skip')

    summary, df_with_phases = analyze_storm_phases(
        df, chi_boundary_min=0.145, chi_boundary_max=0.155, min_peak_points=3,
    )

    # Save labeled rows
    df_with_phases.to_csv(output_csv, index=False)

    # Emit summary
    summary_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    # Compute per-phase metrics for dashboard
    metrics = {}
    for phase in ['PRE', 'PEAK', 'POST']:
        sub = df_with_phases[df_with_phases['phase'] == phase]
        if len(sub) > 0:
            avg = float(sub['chi_amplitude'].mean())
            maxv = float(sub['chi_amplitude'].max())
            # At-boundary within band
            atb = int(((sub['chi_amplitude'] >= 0.145) & (sub['chi_amplitude'] <= 0.155)).sum())
            metrics[phase.lower()] = {
                'count': int(len(sub)),
                'avg': round(avg, 4),
                'max': round(maxv, 4),
                'at_boundary': atb
            }
        else:
            metrics[phase.lower()] = {
                'count': 0, 'avg': '--', 'max': '--', 'at_boundary': 0
            }

    metrics_json.write_text(json.dumps(metrics, indent=2), encoding='utf-8')

    print("Storm phase analysis complete.")
    print(json.dumps(summary, indent=2))
    print(json.dumps(metrics, indent=2))

    return 0

if __name__ == '__main__':
    sys.exit(main())
