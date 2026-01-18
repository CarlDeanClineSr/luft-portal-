import requests
import pandas as pd
import io
import datetime
import numpy as np
import sys

# --- MISSION CONFIGURATION ---
# The "Schmidt Chain" + Tabby's Star (Keystone)
TARGETS = {
    '2354429':  {'name': 'ALPHA (Master)', 'role': 'COMMAND', 'base_mag': 12.5},
    '2913753': {'name':  'BETA (Slave)',   'role': 'ARRAY',   'base_mag': 12.0},
    '3037513': {'name': 'GAMMA (Relay)',  'role': 'RELAY',   'base_mag': 14.7},
    '6804071': {'name': 'DELTA (Slave)',  'role': 'ARRAY',   'base_mag': 12.0},
    '6814519': {'name': 'EPSILON (Slave)','role': 'ARRAY',   'base_mag':  12.0},
    '7255468': {'name': 'ZETA (Slave)',   'role': 'ARRAY',   'base_mag': 12.0},
    '7575062': {'name': 'ETA (Control)',  'role': 'CONTROL', 'base_mag': 14.0},
    'KIC8462852': {
        'name':  'TABBY (Keystone)', 
        'role': 'PROTOTYPE', 
        'coords': {'ra': '301.5644', 'dec':  '44.4568'},
        'base_mag': 11.7
    }
}

# --- CLINE PHYSICS CONSTANTS ---
CHI_LIMIT = 0.15
CHI_MODES = [0.15, 0.30, 0.45]
FLUX_MULTIPLIER_ALERT = 13.0
LADDER_INTERVAL_HOURS = 6.0

def calculate_chi(observed_mag, baseline_mag):
    try:
        flux_ratio = 10**(-0.4 * (float(observed_mag) - baseline_mag))
        chi = abs(flux_ratio - 1.0)
        return chi, flux_ratio
    except (ValueError, TypeError, AttributeError): 
        return 0.0, 1.0

def check_time_ladder(hjd_date):
    day_fraction = (hjd_date + 0.5) % 1.0
    hour_utc = day_fraction * 24.0
    dist_to_ladder = min([abs(hour_utc - x) for x in [0, 6, 12, 18, 24]])
    is_aligned = dist_to_ladder < 0.5
    return is_aligned, hour_utc

def scan_target(tid, info):
    print(f"--> PINGING {info['name']}...")
    
    if 'coords' in info: 
        url = f"https://asas-sn.osu.edu/variables.csv?ra={info['coords']['ra']}&dec={info['coords']['dec']}&radius=0.03"
    else:
        url = f"https://asas-sn.osu.edu/variables/{tid}.csv"
        
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"    [LINK FAILED] Status {response.status_code}")
            return

        df = pd.read_csv(io.StringIO(response.text))
        if df.empty: return

        if 'HJD' in df.columns:
            df = df.sort_values(by='HJD', ascending=False)
            
        latest = df.iloc[0]
        obs_mag_str = str(latest.get('mag', '99.99'))
        
        if ">" in obs_mag_str: 
            obs_mag = 99.99
        else:
            obs_mag = float(obs_mag_str)

        chi, flux_ratio = calculate_chi(obs_mag, info['base_mag'])
        
        ladder_sync = False
        event_hour = 0.0
        if 'HJD' in latest:
            ladder_sync, event_hour = check_time_ladder(latest['HJD'])
        
        status = "QUIET"
        
        if obs_mag > 15.0:
            status = "VOID [VACUUM SATURATION]"
        elif flux_ratio > FLUX_MULTIPLIER_ALERT: 
            status = f"PULSE [HIGH ENERGY {flux_ratio:.1f}x]"
        else:
            for mode in CHI_MODES:
                if abs(chi - mode) < 0.02:
                    status = f"LOCKED [CHI MODE {mode}]"
                    
        sync_flag = " [TIME LADDER SYNC]" if ladder_sync else ""
        
        if status != "QUIET":
            print(f"    *** ALERT: {status} ***")
            print(f"    Chi: {chi:.3f} | Flux: {flux_ratio:.2f}x | Hour: {event_hour:.1f}{sync_flag}")
        else:
            print(f"    Status: Nominal (Chi {chi:.3f})")

    except Exception as e: 
        print(f"    [ERROR] {e}")

if __name__ == "__main__": 
    print(f"--- CLINE OBSERVATORY SCANNER V2: {datetime.datetime.now()} ---")
    for tid, info in TARGETS.items():
        scan_target(tid, info)
    print("--- SCAN COMPLETE ---")
