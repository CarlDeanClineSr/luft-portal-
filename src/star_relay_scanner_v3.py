import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import io
import datetime
import math
import sys
import time

# --- IMPORT IMPERIAL TARGETS ---
try:
    from star_catalog import TARGETS
except ImportError:
    # Fallback if catalog is missing during transition
    TARGETS = {
        'KIC8462852': {'name': 'TABBY (Keystone)', 'role': 'RELAY_01', 'base_mag': 11.7},
        '2354429': {'name': 'SMOKER (Power)', 'role': 'RELAY_02', 'base_mag': 10.3}
    }

# --- IMPERIAL PHYSICS CONSTANTS ---
CHI_LIMIT = 0.15
RESONANCE_PHASES = [1.3526, 4.0143] 
PHASE_TOLERANCE = 0.1
MAG_VOID_THRESHOLD = 15.0 

def create_stealth_session():
    """
    Creates a requests session that looks like a legitimate researcher
    and handles server errors (500/502/503/504) automatically.
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    # IMPERIAL CLOAKING: Set a valid User-Agent so they don't block us
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LUFT-Observatory-Research/1.0",
        "Accept": "text/csv,application/json"
    })
    return session

def calculate_star_phase(hjd):
    frac_day = (hjd + 0.5) % 1.0
    return frac_day * 2 * math.pi

def scan_sector():
    print(f"--- IMPERIAL STEALTH SCAN: {datetime.datetime.utcnow()} UTC ---")
    session = create_stealth_session()
    
    for tid, info in TARGETS.items():
        # TACTICAL DELAY: Wait 2 seconds between targets to avoid 'Status 500'
        time.sleep(2) 
        
        print(f"--> TARGETING {info['name']}...")
        
        if 'coords' in info:
            url = f"https://asas-sn.osu.edu/variables.csv?ra={info['coords']['ra']}&dec={info['coords']['dec']}&radius=0.03"
        else:
            url = f"https://asas-sn.osu.edu/variables/{tid}.csv"

        try:
            r = session.get(url, timeout=20)
            
            if r.status_code != 200:
                print(f"    [SERVER BLOCK] Status {r.status_code}")
                continue
                
            try:
                # Force pandas to ignore bad lines if server sends garbage
                df = pd.read_csv(io.StringIO(r.text), on_bad_lines='skip')
            except pd.errors.EmptyDataError:
                print(f"    [EMPTY FEED] No data returned.")
                continue
            
            if not df.empty:
                latest = df.iloc[0]
                # Robust Magnitude Parsing
                mag_str = str(latest.get('mag', '99')).replace('>','')
                mag = float(mag_str) if mag_str and mag_str != 'nan' else 99.0
                hjd = float(latest['HJD'])
                
                # PHYSICS CALC
                base = info.get('base_mag', 12.0)
                flux_ratio = 10**(-0.4 * (mag - base))
                chi = abs(flux_ratio - 1.0)
                star_phase = calculate_star_phase(hjd)
                
                # RESONANCE CHECK
                lock_msg = ""
                for target in RESONANCE_PHASES:
                    if abs(star_phase - target) < PHASE_TOLERANCE:
                        lock_msg = f"⚡ LOCK [{target}]"

                # STATUS
                state = "NOMINAL"
                if mag > MAG_VOID_THRESHOLD: state = "VOID_STATE"
                if chi >= CHI_LIMIT: state += " [CHI_BREACH]"
                
                print(f"    >> MAG: {mag} | CHI: {chi:.4f} | PHASE: {star_phase:.3f} {lock_msg}")
                
            else:
                print(f"    [NO OBSERVATIONS]")
                
        except Exception as e:
            print(f"    [CONNECTION ERROR] {e}")

if __name__ == "__main__":
    scan_sector()
