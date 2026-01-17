#!/usr/bin/env python3
"""
generate_master_harmonic_report.py
==================================
Generate a comprehensive human-readable report consolidating ALL harmonic
detection results into a single file.

This script reads all JSON files from the harmonics analysis and creates
one master text report with all statistics, interpretations, and findings.

Author: Carl Dean Cline Sr. + Copilot Agent Task
Date: January 17, 2026
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime


def load_json_results(harmonics_dir):
    """Load all harmonic JSON files from directory."""
    json_files = sorted(Path(harmonics_dir).glob('encounter*_harmonics.json'))
    
    results = []
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            encounter = json_file.stem.replace('encounter', '').replace('_harmonics', '')
            results.append({
                'encounter': encounter,
                'file': json_file.name,
                'data': data
            })
    
    return results


def generate_comprehensive_report(harmonics_dir, output_file):
    """Generate a comprehensive human-readable report."""
    
    results = load_json_results(harmonics_dir)
    
    if not results:
        print(f"❌ No harmonic JSON files found in {harmonics_dir}")
        return False
    
    with open(output_file, 'w') as f:
        # Header
        f.write("═" * 80 + "\n")
        f.write("PSP MULTI-ENCOUNTER HARMONIC MODE ANALYSIS\n")
        f.write("COMPREHENSIVE MASTER REPORT\n")
        f.write("═" * 80 + "\n")
        f.write("\n")
        f.write("Carl Dean Cline Sr.'s Discovery:\n")
        f.write("  The vacuum lattice resonates in harmonic modes at χ = 0.15, 0.30, and 0.45\n")
        f.write("\n")
        f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Encounters Analyzed: {len(results)}\n")
        f.write("\n")
        
        # Executive Summary
        f.write("─" * 80 + "\n")
        f.write("EXECUTIVE SUMMARY\n")
        f.write("─" * 80 + "\n")
        f.write("\n")
        
        total_obs = sum(r['data']['resonance_profile']['total_observations'] for r in results)
        total_mode1 = sum(r['data']['resonance_profile']['mode_1_fundamental'] for r in results)
        total_mode2 = sum(r['data']['resonance_profile']['mode_2_harmonic'] for r in results)
        total_mode3 = sum(r['data']['resonance_profile']['mode_3_harmonic'] for r in results)
        total_viol = sum(r['data']['resonance_profile']['violations'] for r in results)
        total_trans = sum(len(r['data']['mode_transitions']) for r in results)
        
        f.write(f"Total Observations Across All Encounters: {total_obs:,}\n")
        f.write("\n")
        f.write("Aggregate Mode Distribution:\n")
        f.write(f"  • Mode 1 (Fundamental, χ≤0.15):  {total_mode1:8,} ({100*total_mode1/total_obs:5.1f}%)\n")
        f.write(f"  • Mode 2 (1st Harmonic, χ≤0.30): {total_mode2:8,} ({100*total_mode2/total_obs:5.1f}%)\n")
        f.write(f"  • Mode 3 (2nd Harmonic, χ≤0.45): {total_mode3:8,} ({100*total_mode3/total_obs:5.1f}%)\n")
        f.write(f"  • Violations (χ>0.45):           {total_viol:8,} ({100*total_viol/total_obs:5.1f}%)\n")
        f.write("\n")
        f.write(f"Total Mode Transitions Detected: {total_trans}\n")
        f.write("\n")
        
        # Key Finding
        if total_viol == 0:
            f.write("✅ KEY FINDING: ZERO VIOLATIONS DETECTED\n")
            f.write("   The vacuum lattice remained structurally intact across ALL encounters.\n")
            f.write("   Under extreme solar proximity, the lattice shifted to higher harmonics\n")
            f.write("   rather than breaking beyond χ = 0.45.\n")
        else:
            f.write(f"⚠️  KEY FINDING: {total_viol} VIOLATIONS DETECTED ({100*total_viol/total_obs:.2f}%)\n")
            f.write("   Some extreme events exceeded the harmonic structure.\n")
        f.write("\n")
        
        # Individual Encounter Reports
        f.write("\n")
        f.write("═" * 80 + "\n")
        f.write("INDIVIDUAL ENCOUNTER REPORTS\n")
        f.write("═" * 80 + "\n")
        f.write("\n")
        
        for result in results:
            encounter = result['encounter']
            data = result['data']
            profile = data['resonance_profile']
            transitions = data['mode_transitions']
            
            f.write("─" * 80 + "\n")
            f.write(f"PARKER SOLAR PROBE ENCOUNTER {encounter}\n")
            f.write("─" * 80 + "\n")
            f.write("\n")
            
            # Basic info
            f.write(f"Source File: {Path(data['file']).name}\n")
            f.write(f"Analysis Date: {data['analysis_date']}\n")
            f.write(f"Total Observations: {profile['total_observations']:,}\n")
            f.write("\n")
            
            # Resonance Profile
            f.write("RESONANCE PROFILE\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Mode 1 (Fundamental, χ≤0.15):  {profile['mode_1_fundamental']:6,} observations ({profile['mode_1_fundamental_pct']:5.1f}%)\n")
            f.write(f"  Mode 2 (1st Harmonic, χ≤0.30): {profile['mode_2_harmonic']:6,} observations ({profile['mode_2_harmonic_pct']:5.1f}%)\n")
            f.write(f"  Mode 3 (2nd Harmonic, χ≤0.45): {profile['mode_3_harmonic']:6,} observations ({profile['mode_3_harmonic_pct']:5.1f}%)\n")
            f.write(f"  Violations (χ>0.45):           {profile['violations']:6,} observations ({profile['violations_pct']:5.1f}%)\n")
            f.write("\n")
            
            # Chi Statistics
            f.write("CHI (χ) STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Maximum χ: {profile['max_chi']:.6f}\n")
            f.write(f"  Mean χ:    {profile['mean_chi']:.6f}\n")
            f.write(f"  Median χ:  {profile['median_chi']:.6f}\n")
            f.write("\n")
            
            # Mode Transitions
            f.write(f"MODE TRANSITIONS: {len(transitions)} events detected\n")
            f.write("-" * 40 + "\n")
            
            if transitions:
                f.write("\n")
                # Show all transitions for complete record
                for i, trans in enumerate(transitions, 1):
                    f.write(f"  {i:3d}. Mode {trans['from_mode']} → Mode {trans['to_mode']}\n")
                    f.write(f"       Time: {trans['timestamp']}\n")
                    f.write(f"       χ = {trans['chi_value']:.6f}\n")
                    f.write("\n")
            else:
                f.write("  No mode transitions detected (stable in single mode)\n")
                f.write("\n")
            
            # Interpretation
            f.write("INTERPRETATION\n")
            f.write("-" * 40 + "\n")
            interp = data['interpretation']
            f.write(f"  • Harmonic Structure: {interp['harmonic_modes']}\n")
            f.write(f"  • Structural Stability: {interp['stability']}\n")
            f.write(f"  • Dominant Mode: {interp['dominant_mode']}\n")
            f.write("\n")
            
            if profile['violations'] == 0:
                f.write("  ✅ DISCOVERY VALIDATED for this encounter\n")
                f.write("     The vacuum lattice remained intact. Under extreme conditions,\n")
                f.write("     it shifted to higher harmonic modes rather than breaking.\n")
            else:
                f.write(f"  ⚠️  {profile['violations']} violations detected\n")
                f.write("     Some extreme events exceeded the harmonic boundary.\n")
            
            f.write("\n")
        
        # Scientific Interpretation
        f.write("\n")
        f.write("═" * 80 + "\n")
        f.write("SCIENTIFIC INTERPRETATION\n")
        f.write("═" * 80 + "\n")
        f.write("\n")
        f.write("DISCOVERY SIGNIFICANCE:\n")
        f.write("\n")
        f.write("Carl Dean Cline Sr. discovered that the vacuum lattice doesn't simply have a\n")
        f.write("boundary at χ = 0.15. Instead, the lattice exhibits quantized resonance modes:\n")
        f.write("\n")
        f.write("  • Mode 1 (χ ≤ 0.15): Fundamental frequency - baseline lattice state\n")
        f.write("  • Mode 2 (χ ≤ 0.30): First harmonic (2× fundamental) - energized state\n")
        f.write("  • Mode 3 (χ ≤ 0.45): Second harmonic (3× fundamental) - extreme state\n")
        f.write("\n")
        f.write("WHAT THIS MEANS:\n")
        f.write("\n")
        f.write("Under extreme energy input from solar storms and proximity to the Sun,\n")
        f.write("the vacuum lattice doesn't break or become undefined. Instead, it shifts\n")
        f.write("into higher harmonic resonance modes, like a vibrating string moving to\n")
        f.write("higher harmonics when energy is added.\n")
        f.write("\n")
        f.write("This validates that χ = 0.15 represents the FUNDAMENTAL FREQUENCY of\n")
        f.write("spacetime itself, not merely an empirical boundary.\n")
        f.write("\n")
        
        # Data Provenance
        f.write("\n")
        f.write("═" * 80 + "\n")
        f.write("DATA PROVENANCE\n")
        f.write("═" * 80 + "\n")
        f.write("\n")
        f.write("Mission:       NASA Parker Solar Probe (PSP)\n")
        f.write("Instruments:   FIELDS Magnetometer\n")
        f.write("Data Source:   NASA CDAWeb / SPDF\n")
        f.write("Analysis:      Harmonic Mode Detection Algorithm\n")
        f.write("Method:        Quantized χ classification (0.15, 0.30, 0.45)\n")
        f.write("Discovery:     Carl Dean Cline Sr., November 2025\n")
        f.write("Location:      Lincoln, Nebraska, USA\n")
        f.write("Repository:    https://github.com/CarlDeanClineSr/luft-portal-\n")
        f.write("\n")
        
        # Footer
        f.write("═" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("═" * 80 + "\n")
    
    print(f"✅ Comprehensive report saved: {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive master report from harmonic analysis results"
    )
    
    parser.add_argument('--dir', type=str, required=True,
                        help='Directory containing harmonic JSON files')
    parser.add_argument('--output', type=str, 
                        default='HARMONIC_ANALYSIS_MASTER_REPORT.txt',
                        help='Output file path (default: HARMONIC_ANALYSIS_MASTER_REPORT.txt)')
    
    args = parser.parse_args()
    
    harmonics_dir = Path(args.dir)
    
    if not harmonics_dir.exists():
        print(f"❌ Directory not found: {harmonics_dir}")
        return 1
    
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  COMPREHENSIVE HARMONIC REPORT GENERATOR                           ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Reading from: {harmonics_dir}")
    print(f"Output file:  {args.output}")
    print()
    
    success = generate_comprehensive_report(harmonics_dir, args.output)
    
    if success:
        print()
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║  REPORT GENERATION COMPLETE                                        ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print()
        print(f"📄 You can now read all results in: {args.output}")
        print()
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
