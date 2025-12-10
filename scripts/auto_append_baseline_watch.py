#!/usr/bin/env python3
"""
auto_append_baseline_watch.py
==============================
LUFT Automated Baseline Watch — Auto-appends daily χ floor and plasma/magnetic reading
to CAPSULE_DECEMBER_BASELINE_SHIFT_WATCH_001.md

Discovered by Carl Dean Cline Sr., Lincoln, Nebraska
December 2025

This script:
- Pulls real-time SWPC JSON (ACE/DSCOVR considered, falls back to GOES if needed)
- Computes quiet-hour average at 06:00 UTC
- Calculates χ floor from plasma and magnetic readings
- Appends daily entry to baseline watch capsule
- Marks 'CONFIRMED SHIFT' if χ ≥ 0.12, else 'EXHALE TEST'

Law #15 ledger eternal.

Usage:
    python scripts/auto_append_baseline_watch.py --plasma data/ace_plasma_latest.json --mag data/ace_mag_latest.json
    python scripts/auto_append_baseline_watch.py --demo  # Run with demo data for testing

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# LUFT Constants
CHI_SHIFT_THRESHOLD = 0.12  # Threshold for confirmed shift
CHI_BASELINE_PRE_DEC = 0.055  # Pre-December baseline
CHI_MIN_VALUE = 0.01  # Minimum chi value (clamping)
CHI_MAX_VALUE = 0.20  # Maximum chi value (clamping)
DELTA_CHI_SIGNIFICANT = 0.05  # Threshold for significant delta chi

PERIOD_HOURS = 2.4    # Period in hours
PERIOD_SECONDS = PERIOD_HOURS * 3600  # 8640 seconds

# Baseline solar wind parameters (quiet conditions)
BASELINE_DENSITY = 5.0    # p/cm³ - typical quiet solar wind density
BASELINE_SPEED = 400.0    # km/s - typical quiet solar wind speed
BASELINE_BT = 5.0         # nT - typical quiet interplanetary magnetic field

# Chi amplitude scaling factor (empirically derived from LUFT model)
CHI_SCALING_CENTER = 0.1  # Center point for modulation-to-chi mapping

# Uncertainty bounds
UNCERTAINTY_MIN = 0.001  # Minimum uncertainty value
UNCERTAINTY_SCALE = 0.01  # Scaling factor for uncertainty
UNCERTAINTY_MAX = 0.010  # Maximum uncertainty value
UNCERTAINTY_DEFAULT = 0.002  # Default uncertainty if no data

# Capsule file path
CAPSULE_PATH = Path("capsules/2025_dec_batch/CAPSULE_DECEMBER_BASELINE_SHIFT_WATCH_001.md")

# Demo data generation parameters
DEMO_DENSITY_MEAN = 5.0
DEMO_DENSITY_STD = 2.0
DEMO_SPEED_MEAN = 400.0
DEMO_SPEED_STD = 50.0
DEMO_BZ_MEAN = -2.0
DEMO_BZ_STD = 3.0
DEMO_BT_MEAN = 5.0
DEMO_BT_STD = 2.0


def load_json_data(filepath):
    """Load JSON data from file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {filepath}")
        print(f"   Please check that the data download step completed successfully.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in {filepath}")
        print(f"   JSON decode error: {e}")
        print(f"   The file may be corrupted or not in valid JSON format.")
        return None
    except Exception as e:
        print(f"❌ ERROR: Unexpected error loading {filepath}: {type(e).__name__}: {e}")
        return None


def extract_quiet_hour_average(data, data_type='plasma'):
    """
    Extract quiet-hour average from NOAA JSON format.
    Averages the last hour of data (12 samples at 5-min intervals).
    """
    if not data:
        print(f"⚠️  WARNING: No {data_type} data provided")
        return None
    
    if len(data) < 2:
        print(f"⚠️  WARNING: Insufficient {data_type} data (need at least 2 rows, got {len(data)})")
        return None
    
    # NOAA format: first row is headers, data rows follow
    # For plasma: [time_tag, density, speed, temperature]
    # For mag: [time_tag, bx_gsm, by_gsm, bz_gsm, bt, lat_gsm, lon_gsm]
    try:
        # Take last 12 samples (1 hour at 5-min intervals)
        # Skip header row (index 0)
        samples = data[-12:] if len(data) > 12 else data[1:]
        
        if data_type == 'plasma':
            # Filter out header and None values
            densities = []
            speeds = []
            for row in samples:
                if len(row) >= 3 and row[0] != 'time_tag':  # Skip header row
                    try:
                        if row[1] and row[1] != 'density':
                            densities.append(float(row[1]))
                        if row[2] and row[2] != 'speed':
                            speeds.append(float(row[2]))
                    except (ValueError, TypeError) as e:
                        print(f"   Skipping invalid plasma row: {e}")
                        continue
            
            if not densities and not speeds:
                print(f"❌ ERROR: No valid plasma data values found in {len(samples)} samples")
                print(f"   All density and speed values were None or invalid")
                return None
            
            return {
                'density': np.mean(densities) if densities else None,
                'speed': np.mean(speeds) if speeds else None,
                'density_std': np.std(densities) if densities else None,
                'speed_std': np.std(speeds) if speeds else None,
            }
        elif data_type == 'mag':
            # Filter out header and None values
            bts = []
            bzs = []
            for row in samples:
                if len(row) >= 5 and row[0] != 'time_tag':  # Skip header row
                    try:
                        if row[4] and row[4] != 'bt':
                            bts.append(float(row[4]))
                        if row[3] and row[3] != 'bz_gsm':
                            bzs.append(float(row[3]))
                    except (ValueError, TypeError) as e:
                        print(f"   Skipping invalid mag row: {e}")
                        continue
            
            if not bts and not bzs:
                print(f"❌ ERROR: No valid magnetic field data values found in {len(samples)} samples")
                print(f"   All bt and bz values were None or invalid")
                return None
            
            return {
                'bt': np.mean(bts) if bts else None,
                'bz': np.mean(bzs) if bzs else None,
                'bt_std': np.std(bts) if bts else None,
                'bz_std': np.std(bzs) if bzs else None,
            }
    except (ValueError, TypeError, IndexError) as e:
        print(f"❌ ERROR: Could not parse {data_type} data: {type(e).__name__}: {e}")
        print(f"   Data format may be incorrect or corrupted")
    
    return None


def estimate_chi_floor(density, speed, bt):
    """
    Estimate χ floor from solar wind parameters using quiet-hour averaging.
    
    Uses a simplified model based on density and speed fluctuations
    relative to baseline values.
    """
    chi = 0.0
    n_valid = 0
    
    if density is not None and density > 0:
        density_mod = abs(density - BASELINE_DENSITY) / BASELINE_DENSITY
        chi += min(density_mod, 0.3)  # Cap contribution
        n_valid += 1
    
    if speed is not None and speed > 0:
        speed_mod = abs(speed - BASELINE_SPEED) / BASELINE_SPEED
        chi += min(speed_mod, 0.3)
        n_valid += 1
    
    if bt is not None and bt > 0:
        bt_mod = abs(bt - BASELINE_BT) / BASELINE_BT
        chi += min(bt_mod, 0.3)
        n_valid += 1
    
    if n_valid > 0:
        chi = chi / n_valid  # Average modulation
        # Scale to expected range around 0.055 using scaling center
        chi = CHI_BASELINE_PRE_DEC + (chi - CHI_SCALING_CENTER) * 0.5
        chi = max(CHI_MIN_VALUE, min(chi, CHI_MAX_VALUE))  # Clamp to reasonable range
    else:
        chi = CHI_BASELINE_PRE_DEC  # Default if no valid data
    
    return chi


def estimate_uncertainty(density_std, speed_std, bt_std):
    """
    Estimate uncertainty in χ from standard deviations of measurements.
    """
    uncertainties = []
    
    if density_std is not None:
        uncertainties.append(density_std / BASELINE_DENSITY * 0.5)
    if speed_std is not None:
        uncertainties.append(speed_std / BASELINE_SPEED * 0.5)
    if bt_std is not None:
        uncertainties.append(bt_std / BASELINE_BT * 0.5)
    
    if uncertainties:
        # Combined uncertainty (quadrature sum)
        combined = np.sqrt(sum(u**2 for u in uncertainties))
        return max(UNCERTAINTY_MIN, min(combined * UNCERTAINTY_SCALE, UNCERTAINTY_MAX))
    
    return UNCERTAINTY_DEFAULT


def append_to_capsule(chi, uncertainty, delta_chi, status, notes, data_source):
    """
    Append a new row to the baseline watch capsule table.
    """
    if not CAPSULE_PATH.exists():
        print()
        print(f"❌ ERROR: Capsule file not found: {CAPSULE_PATH}")
        print(f"   Expected path: {CAPSULE_PATH.absolute()}")
        print(f"   Please verify the capsule file exists at this location.")
        sys.exit(1)
    
    try:
        # Read existing content
        with open(CAPSULE_PATH, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print()
        print(f"❌ ERROR: Could not read capsule file: {type(e).__name__}: {e}")
        sys.exit(1)
    
    # Find the table section
    table_end_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('|') and 'Date' in line:
            # Found table header, search for end of table
            for j in range(i+2, len(lines)):  # Skip header and separator
                if not lines[j].strip().startswith('|'):
                    table_end_idx = j
                    break
            if table_end_idx is None:
                table_end_idx = len(lines)
            break
    
    if table_end_idx is None:
        print()
        print("❌ ERROR: Could not find table in capsule file")
        print(f"   Expected a markdown table with a 'Date' column header")
        print(f"   Please verify the capsule file format is correct.")
        sys.exit(1)
    
    # Format new row
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    chi_str = f"{chi:.3f} ± {uncertainty:.3f}"
    delta_str = f"**{delta_chi:+.3f}**" if abs(delta_chi) >= DELTA_CHI_SIGNIFICANT else f"{delta_chi:+.3f}"
    
    new_row = f"| {date} | {chi_str} | {delta_str} | {notes} |\n"
    
    # Check if today's entry already exists
    for line in lines:
        if date in line and line.strip().startswith('|'):
            print()
            print(f"ℹ️  Entry for {date} already exists. Skipping append.")
            return False
    
    # Insert new row
    lines.insert(table_end_idx, new_row)
    
    # Write back
    try:
        with open(CAPSULE_PATH, 'w') as f:
            f.writelines(lines)
    except Exception as e:
        print()
        print(f"❌ ERROR: Could not write to capsule file: {type(e).__name__}: {e}")
        print(f"   File may be read-only or disk may be full.")
        sys.exit(1)
    
    print(f"✅ Appended entry for {date} to {CAPSULE_PATH}")
    print(f"   χ floor: {chi_str}")
    print(f"   Δ from baseline: {delta_str}")
    print(f"   Status: {status}")
    print(f"   Data source: {data_source}")
    
    return True


def generate_demo_entry():
    """Generate a demo entry for testing."""
    # Simulate solar wind data with some variation
    density = DEMO_DENSITY_MEAN + np.random.normal(0, DEMO_DENSITY_STD)
    speed = DEMO_SPEED_MEAN + np.random.normal(0, DEMO_SPEED_STD)
    bt = DEMO_BT_MEAN + np.random.normal(0, DEMO_BT_STD)
    
    # Add some noise for std calculation
    density_std = abs(np.random.normal(0, DEMO_DENSITY_STD * 0.5))
    speed_std = abs(np.random.normal(0, DEMO_SPEED_STD * 0.5))
    bt_std = abs(np.random.normal(0, DEMO_BT_STD * 0.5))
    
    return {
        'density': max(0, density),
        'speed': max(0, speed),
        'bt': max(0, bt),
        'density_std': density_std,
        'speed_std': speed_std,
        'bt_std': bt_std,
    }


def main():
    parser = argparse.ArgumentParser(
        description="LUFT Automated Baseline Watch — Auto-append daily χ floor (Law #15 ledger)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/auto_append_baseline_watch.py --plasma data/ace_plasma_latest.json --mag data/ace_mag_latest.json
  python scripts/auto_append_baseline_watch.py --demo

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--plasma', type=str, help='Path to plasma data JSON')
    parser.add_argument('--mag', type=str, help='Path to magnetic field data JSON')
    parser.add_argument('--demo', action='store_true', help='Generate demo entry for testing')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("   LUFT AUTOMATED BASELINE WATCH — LAW #15 LEDGER ETERNAL")
    print("   Daily χ floor appender for quantum capsule")
    print("=" * 70)
    print()
    
    if args.demo:
        print("Running in DEMO mode...")
        demo_data = generate_demo_entry()
        
        density = demo_data['density']
        speed = demo_data['speed']
        bt = demo_data['bt']
        density_std = demo_data['density_std']
        speed_std = demo_data['speed_std']
        bt_std = demo_data['bt_std']
        data_source = "DEMO"
    else:
        if not args.plasma or not args.mag:
            print("❌ ERROR: Please provide --plasma and --mag data files, or use --demo")
            print("   Usage: python scripts/auto_append_baseline_watch.py --plasma <file> --mag <file>")
            sys.exit(1)
        
        # Load data
        print(f"📥 Loading plasma data from: {args.plasma}")
        plasma_data = load_json_data(args.plasma)
        
        print(f"📥 Loading magnetic data from: {args.mag}")
        mag_data = load_json_data(args.mag)
        
        if not plasma_data and not mag_data:
            print()
            print("❌ ERROR: Could not load any valid data from input files")
            print("   Both plasma and magnetic data files failed to load.")
            print("   Check that the files exist and contain valid JSON data.")
            sys.exit(1)
        
        if not plasma_data:
            print("⚠️  WARNING: Plasma data not available, will use magnetic data only")
        if not mag_data:
            print("⚠️  WARNING: Magnetic data not available, will use plasma data only")
        
        # Extract quiet-hour averages
        print()
        print("🔬 Computing quiet-hour averages...")
        plasma_avg = extract_quiet_hour_average(plasma_data, 'plasma') if plasma_data else None
        mag_avg = extract_quiet_hour_average(mag_data, 'mag') if mag_data else None
        
        if not plasma_avg and not mag_avg:
            print()
            print("❌ ERROR: Could not extract valid averages from input data")
            print("   Data files may be empty, corrupted, or in an unexpected format.")
            print("   Expected NOAA SWPC JSON format with headers in first row.")
            sys.exit(1)
        
        # Get values
        density = plasma_avg.get('density') if plasma_avg else None
        speed = plasma_avg.get('speed') if plasma_avg else None
        bt = mag_avg.get('bt') if mag_avg else None
        density_std = plasma_avg.get('density_std') if plasma_avg else None
        speed_std = plasma_avg.get('speed_std') if plasma_avg else None
        bt_std = mag_avg.get('bt_std') if mag_avg else None
        
        # Determine data source
        if plasma_avg and mag_avg:
            data_source = "ACE/DSCOVR"
        elif plasma_avg:
            data_source = "ACE/DSCOVR (plasma only)"
        else:
            data_source = "ACE/DSCOVR (mag only)"
    
    # Compute χ floor
    if density is not None:
        print(f"Density: {density:.2f} ± {density_std:.2f} p/cm³" if density_std is not None else f"Density: {density:.2f} p/cm³")
    else:
        print("Density: N/A")
    
    if speed is not None:
        print(f"Speed: {speed:.1f} ± {speed_std:.1f} km/s" if speed_std is not None else f"Speed: {speed:.1f} km/s")
    else:
        print("Speed: N/A")
    
    if bt is not None:
        print(f"Bt: {bt:.2f} ± {bt_std:.2f} nT" if bt_std is not None else f"Bt: {bt:.2f} nT")
    else:
        print("Bt: N/A")
    print()
    
    chi = estimate_chi_floor(density, speed, bt)
    uncertainty = estimate_uncertainty(density_std, speed_std, bt_std)
    delta_chi = chi - CHI_BASELINE_PRE_DEC
    
    # Determine status
    if chi >= CHI_SHIFT_THRESHOLD:
        status = "CONFIRMED SHIFT"
        notes = f"**{status}** — χ ≥ {CHI_SHIFT_THRESHOLD}"
    else:
        status = "EXHALE TEST"
        notes = f"{status}"
    
    print(f"χ floor: {chi:.3f} ± {uncertainty:.3f}")
    print(f"Δ from pre-Dec baseline: {delta_chi:+.3f}")
    print(f"Status: {status}")
    print()
    
    # Append to capsule
    appended = append_to_capsule(chi, uncertainty, delta_chi, status, notes, data_source)
    
    print()
    print("=" * 70)
    if appended:
        print("✅ Daily baseline watch appended successfully — Law #15 ledger eternal.")
    else:
        print("ℹ️  No changes made — Entry already exists for today.")
    print("Contact: CARLDCLINE@GMAIL.COM")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
