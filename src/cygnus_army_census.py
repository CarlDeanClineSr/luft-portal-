"""
Cygnus Army Census Scanner

Queries the ASAS-SN variable star catalog for stars near Tabby's Star (KIC8462852),
calculates their phase angles using the Cline Phase Calculation, and identifies
stars exhibiting phase-locked resonances at specific target phases.

Usage:
    python src/cygnus_army_census.py          # Production mode (queries ASAS-SN)
    python src/cygnus_army_census.py --test   # Test mode (uses mock data)

The scanner outputs a formatted census report to reports/CYGNUS_ARMY_CENSUS.txt
with lock statistics and phase information for each star.
"""

import requests
import pandas as pd
import io
import math
import time
import os
import sys

# --- CONFIGURATION ---

# Sky position configuration:
# - RA_CENTER and DEC_CENTER are the J2000 coordinates (in degrees) of
#   KIC 8462852 ("Tabby's Star"), which defines the center of the search
#   field for the ASAS-SN query.
RA_CENTER = "301.5644"  # Tabby's Star RA (J2000, degrees)
DEC_CENTER = "44.4568"  # Tabby's Star DEC (J2000, degrees)

# Search radius (in degrees) around the field center. This small radius
# keeps the catalog query tractable and helps avoid ASAS-SN API timeouts
# while still covering the immediate neighborhood of Tabby's Star.
RADIUS = "0.2"

OUTPUT_FILE = "reports/CYGNUS_ARMY_CENSUS.txt"

# RESONANCE TARGETS (The "Natural Order"):
# The census looks for stars whose variability phase aligns with specific
# target phase angles, expressed in radians on [0, 2π). These values are
# derived from prior analysis of the hypothesized "natural order" of
# resonances in the system:
#   - 1.3526 rad (~77.5°)
#   - 4.0143 rad (~230.1°)
# Stars are considered to "match" a resonance if their phase (see get_phase)
# lies within TOLERANCE radians of any target angle.
TARGETS = [1.3526, 4.0143]

# Allowed deviation (in radians) from each resonance target. A phase is
# counted as resonant if |phase - target| <= TOLERANCE for at least one
# target in TARGETS. Adjust with care: larger values increase counts but
# reduce selectivity of the resonance criterion.
TOLERANCE = 0.15

# TEST MODE - set to True to use mock data for testing
TEST_MODE = "--test" in sys.argv

def get_phase(hjd):
    """
    Compute the phase (in radians) of a Heliocentric Julian Date (HJD) within a
    single solar day using the "Standard Cline Phase Calculation".
    
    The calculation proceeds in two steps:
    1. Phase in days:
       We take the HJD, add 0.5 days, and then take the fractional part:
           phase_day = (HJD + 0.5) % 1.0
       This is equivalent to folding the time on a 1-day period. The +0.5 is a
       conventional choice of zero-point (epoch) that shifts the reference
       phase by half a day; it does not change the periodic content, only the
       origin of phase.
    
    2. Phase in radians:
       We then map the day-fraction to an angular phase on [0, 2π):
           phase_rad = phase_day * 2π
       This is a standard transformation in time-series/astronomical analysis
       when expressing the phase of periodic phenomena (e.g., variable stars)
       as an angle.
    
    This function therefore returns an angular phase in radians that can be
    compared directly to target resonance phases defined on [0, 2π).
    
    Args:
        hjd: Heliocentric Julian Date
        
    Returns:
        Phase angle in radians [0, 2π)
    """
    val = (float(hjd) + 0.5) % 1.0
    return val * 2 * math.pi

def get_mock_data():
    """Generate mock data for testing when ASAS-SN is unavailable"""
    # Create test data with some stars at resonance phases
    mock_data = {
        'id': [
            'ASAS-SN-V J200135.45+442721.3',
            'ASAS-SN-V J200142.12+442815.8',
            'ASAS-SN-V J200158.31+442456.2',
            'ASAS-SN-V J200201.89+442632.7',
            'ASAS-SN-V J200215.43+442801.5',
        ],
        'mag_v': [12.3, 13.1, 11.8, 14.2, 12.9],
        # HJD values calculated to produce phases near our targets
        # Target 1: 1.3526 rad -> day_frac = 1.3526/(2*pi) = 0.2152
        # Target 2: 4.0143 rad -> day_frac = 4.0143/(2*pi) = 0.6388
        'HJD': [
            2459000.7152,  # Should produce phase ~1.35 (close to target 1)
            2459000.1388,  # Should produce phase ~4.01 (close to target 2)
            2459000.4500,  # Random phase
            2458999.7152,  # Should produce phase ~1.35 (close to target 1)
            2459000.9000,  # Random phase
        ]
    }
    return pd.DataFrame(mock_data)

def run_census():
    """
    Run the Cygnus Army census scan against ASAS-SN data.
    
    In production mode (default), this function queries the ASAS-SN
    variables endpoint around ``RA_CENTER``/``DEC_CENTER`` within
    ``RADIUS`` degrees, then processes the returned catalog to search
    for stars whose phases resonate with the ``TARGETS`` values within
    ``TOLERANCE``.
    
    When ``TEST_MODE`` is enabled (via the ``--test`` command-line
    flag), the remote ASAS-SN query is skipped and mock data from
    :func:`get_mock_data` is used instead, allowing offline or faster
    testing.
    
    The function writes a human-readable report to ``OUTPUT_FILE`` and
    prints progress messages, warnings, and any errors to standard
    output. It does not return a value.
    """
    print(f"--- STARTING {'TEST' if TEST_MODE else 'REAL'} CENSUS SCAN (Radius: {RADIUS} deg) ---")
    
    if TEST_MODE:
        print(">> Using MOCK DATA for testing...")
        df = get_mock_data()
    else:
        # 1. FETCH THE LIST (Real ASAS-SN Query)
        # We use the 'variables' endpoint to get the list of stars first
        list_url = f"https://asas-sn.osu.edu/variables.csv?ra={RA_CENTER}&dec={DEC_CENTER}&radius={RADIUS}"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; ClineObservatory/1.0; +https://github.com/CarlDeanClineSr/luft-portal-)'}
        
        try:
            print(">> Querying ASAS-SN Database...")
            r = requests.get(list_url, headers=headers, timeout=30)
            
            if r.status_code != 200:
                print(f"ERROR: Server returned {r.status_code}")
                print(f"Response: {r.text[:200]}")
                return

            # Check if we got any data
            if not r.text or len(r.text.strip()) == 0:
                print("WARNING: Empty response from ASAS-SN server")
                print("This may indicate the region has no known variable stars,")
                print("or the ASAS-SN service is temporarily unavailable.")
                return

            # Load the list of stars
            df = pd.read_csv(io.StringIO(r.text))
            
            if df.empty:
                print("No stars found in this radius. Try widening it.")
                return
        except Exception as e:
            print(f"FETCH ERROR: {e}")
            return

    try:
        print(f">> FOUND {len(df)} CANDIDATE STARS. ANALYZING PHASES...")
        
        # 2. ANALYZE AND WRITE TO FILE
        # We ensure the directory exists
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        locked_count = 0
        skipped_count = 0
        
        with open(OUTPUT_FILE, "w") as f:
            f.write(f"GALACTIC PLATE CENSUS REPORT\n")
            f.write(f"Center: {RA_CENTER}, {DEC_CENTER} | Radius: {RADIUS}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'STAR ID':<30} | {'MAG':<6} | {'PHASE (rad)':<12} | {'STATUS'}\n")
            f.write("-" * 60 + "\n")
            
            for index, star in df.iterrows():
                try:
                    # Some ASAS-SN CSVs have 'HJD' in the top row, others require a separate fetch.
                    # This endpoint usually gives the latest HJD in the 'epoch' or similar column if flattened.
                    # If HJD is missing, we skip (to avoid breaking).
                    if 'HJD' not in star and 'hjd' not in star:
                        # Attempt to fetch individual light curve if needed (slower, but accurate)
                        # For this batch, we assume the bulk CSV provides the necessary data column 
                        # or we skip to keep it fast.
                        continue
                         
                    hjd = float(star.get('HJD', star.get('hjd', 0)))
                    if hjd == 0: continue

                    phase = get_phase(hjd)
                    
                    # Check Lock
                    status = "DRIFT"
                    for t in TARGETS:
                        if abs(phase - t) < TOLERANCE:
                            status = f"LOCKED [{t}]"
                            locked_count += 1
                            break  # Only count once per star
                    
                    # Write to file
                    line = f"{star['id']:<30} | {star.get('mag_v', 'N/A'):<6} | {phase:.4f}       | {status}\n"
                    f.write(line)
                    print(line.strip())
                    
                except Exception as e:
                    skipped_count += 1
                    print(f"WARNING: Skipped star due to error: {e}")
                    continue
            
            # Summary
            f.write("-" * 60 + "\n")
            f.write(f"TOTAL SCANNED: {len(df)}\n")
            f.write(f"LOCKED NODES:  {locked_count}\n")
            if skipped_count > 0:
                f.write(f"SKIPPED:       {skipped_count}\n")
            if len(df) > 0:
                percentage = (locked_count / len(df)) * 100
                f.write(f"LOCK RATE:     {percentage:.2f}%\n")
            else:
                f.write(f"LOCK RATE:     N/A\n")
            
        print(f"\n>> SUCCESS. REPORT SAVED TO: {OUTPUT_FILE}")
        if len(df) > 0:
            percentage = (locked_count / len(df)) * 100
            print(f">> LOCK RATE: {percentage:.2f}%")
        else:
            print(f">> LOCK RATE: N/A")

    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_census()
