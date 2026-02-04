#!/usr/bin/env python3
"""
Imperial Physics Observatory: Scan for Chi Violations
Identifies all chi boundary events and violations
"""

import pandas as pd
import json
import argparse
from pathlib import Path

def scan_violations(filepath):
    """Scan chi data for violations and boundary events"""
    df = pd.read_csv(filepath)
    
    # Find violations
    violations = df[df['chi_status'] == 'VIOLATION'].copy()
    boundary = df[df['chi_status'] == 'AT_BOUNDARY'].copy()
    
    report = {
        'total_measurements': len(df),
        'violations': {
            'count': len(violations),
            'max_chi': float(violations['chi'].max()) if len(violations) > 0 else 0.0,
            'missions': violations['mission'].value_counts().to_dict() if len(violations) > 0 else {},
            'events': violations[['timestamp', 'mission', 'chi']].to_dict('records')
        },
        'boundary_events': {
            'count': len(boundary),
            'missions': boundary['mission'].value_counts().to_dict() if len(boundary) > 0 else {}
        },
        'by_mission': {}
    }
    
    # Per-mission statistics
    for mission in df['mission'].unique():
        mission_data = df[df['mission'] == mission]
        report['by_mission'][mission] = {
            'measurements': len(mission_data),
            'mean_chi': float(mission_data['chi'].mean()),
            'max_chi': float(mission_data['chi'].max()),
            'violations': int((mission_data['chi_status'] == 'VIOLATION').sum()),
            'at_boundary': int((mission_data['chi_status'] == 'AT_BOUNDARY').sum())
        }
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Scan for chi violations')
    parser.add_argument('--input', required=True, help='Input chi CSV file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    
    args = parser.parse_args()
    
    print(f"Scanning chi violations in: {args.input}")
    
    report = scan_violations(args.input)
    
    # Save report
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nViolation report saved: {args.output}")
    print(f"  Total measurements: {report['total_measurements']:,}")
    print(f"  Violations: {report['violations']['count']:,}")
    print(f"  Boundary events: {report['boundary_events']['count']:,}")
    
    if report['violations']['count'] > 0:
        print(f"  Max chi: {report['violations']['max_chi']:.4f}")

if __name__ == '__main__':
    main()
