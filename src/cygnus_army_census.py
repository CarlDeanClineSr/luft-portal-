import requests
import pandas as pd
import io
import math
import time
import os
import sys

# --- CONFIGURATION ---
RA_CENTER = "301.5644"  # Tabby's Star RA
DEC_CENTER = "44.4568"  # Tabby's Star DEC
RADIUS = "0.2"          # Small, real radius (Avoids timeouts)
OUTPUT_FILE = "reports/CYGNUS_ARMY_CENSUS.txt"

# RESONANCE TARGETS (The "Natural Order")
TARGETS = [1.3526, 4.0143]
TOLERANCE = 0.15

# TEST MODE - set to True to use mock data for testing
TEST_MODE = "--test" in sys.argv

def get_phase(hjd):
    # Standard Cline Phase Calculation
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
            2459000.2152,  # Should produce phase ~1.35 (close to target 1)
            2459000.9000,  # Random phase
        ]
    }
    return pd.DataFrame(mock_data)

def run_census():
    print(f"--- STARTING {'TEST' if TEST_MODE else 'REAL'} CENSUS SCAN (Radius: {RADIUS} deg) ---")
    
    if TEST_MODE:
        print(">> Using MOCK DATA for testing...")
        df = get_mock_data()
    else:
        # 1. FETCH THE LIST (Real ASAS-SN Query)
        # We use the 'variables' endpoint to get the list of stars first
        list_url = f"https://asas-sn.osu.edu/variables.csv?ra={RA_CENTER}&dec={DEC_CENTER}&radius={RADIUS}"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; ClineObservatory/1.0; +http://luft.local)'}
        
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
                    continue
            
            # Summary
            f.write("-" * 60 + "\n")
            f.write(f"TOTAL SCANNED: {len(df)}\n")
            f.write(f"LOCKED NODES:  {locked_count}\n")
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
