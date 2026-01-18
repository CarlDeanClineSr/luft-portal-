import requests
import pandas as pd
import io
import datetime
import numpy as np
import math

# --- MISSION TARGETS ---
TARGETS = {
    '2354429': {'name': 'ALPHA (Master)', 'role': 'COMMAND', 'base_mag': 12.5},
    '6804071': {'name': 'DELTA (Slave)',  'role': 'ARRAY',   'base_mag': 12.0},
    'KIC8462852': {
        'name': 'TABBY (Keystone)', 
        'role': 'PROTOTYPE', 
        'coords': {'ra': '301.5644', 'dec': '44.4568'}, 
        'base_mag': 11.7
    }
}

# --- PHYSICS CONSTANTS ---
CHI_LIMIT = 0.15
RESONANCE_PHASES = [1.3526, 4.0143] # The Solar Wind Keys
PHASE_TOLERANCE = 0.1  # Strict tolerance for phase matching
MAG_VOID_THRESHOLD = 15.0  # Magnitude threshold for void state
FLUX_PULSE_THRESHOLD = 10.0  # Flux ratio threshold for pulse state

def calculate_star_phase(hjd):
    """
    Converts Event Time (HJD) into a 0-2pi Phase Angle 
    to compare with Solar Wind Radians.
    """
    # 1. Get fractional day (0.0 - 0.99)
    # HJD starts at noon, add 0.5 to align to UTC Midnight
    frac_day = (hjd + 0.5) % 1.0
    
    # 2. Convert to Radians (0 to 6.28)
    phase_rad = frac_day * 2 * math.pi
    return phase_rad

def scan_sector():
    print(f"--- STAR RELAY V3 (PHASE HUNT): {datetime.datetime.now()} ---")
    print(f"LOOKING FOR SOLAR RESONANCE: {RESONANCE_PHASES}")
    
    for tid, info in TARGETS.items():
        # Build URL
        if 'coords' in info:
            url = f"https://asas-sn.osu.edu/variables.csv?ra={info['coords']['ra']}&dec={info['coords']['dec']}&radius=0.03"
        else:
            url = f"https://asas-sn.osu.edu/variables/{tid}.csv"

        try:
            r = requests.get(url, timeout=10)
            
            if r.status_code != 200:
                print(f"NODE {info['name']}: [HTTP ERROR {r.status_code}]")
                continue
                
            df = pd.read_csv(io.StringIO(r.text))
            
            if not df.empty:
                # Get Latest Event
                latest = df.iloc[0]
                mag_str = str(latest.get('mag', '99')).replace('>','')
                mag = float(mag_str) if mag_str else 99.0
                hjd = float(latest['HJD'])
                
                # PHYSICS CALCS
                # 1. Chi
                flux_ratio = 10**(-0.4 * (mag - info['base_mag']))
                chi = abs(flux_ratio - 1.0)
                
                # 2. Phase
                star_phase = calculate_star_phase(hjd)
                
                # 3. Check for Lock
                lock_status = ""
                for target in RESONANCE_PHASES:
                    if abs(star_phase - target) < PHASE_TOLERANCE:
                        lock_status = f" [PHASE MATCH: {target}]"

                # REPORT
                state = "NOMINAL"
                if mag > MAG_VOID_THRESHOLD: state = "VOID"
                if flux_ratio > FLUX_PULSE_THRESHOLD: state = "PULSE"
                
                print(f"NODE {info['name']}: {state}")
                print(f"   -> Chi: {chi:.3f} | Phase: {star_phase:.4f} rad {lock_status}")
            else:
                print(f"NODE {info['name']}: [NO DATA]")
                
        except requests.exceptions.RequestException as e:
            print(f"NODE {info['name']}: [NETWORK ERROR]")
        except Exception as e:
            print(f"NODE {info['name']}: [DATA ERROR: {type(e).__name__}]")

if __name__ == "__main__":
    scan_sector()
