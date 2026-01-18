import requests
import pandas as pd
import io
import datetime
import sys

# --- THE TARGET LIST (EXPANDABLE) ---
# We look for "Ship-to-Ship" chains here.
TARGET_NODES = {
    '2354429': {'name': 'ALPHA (Master)', 'role': 'COMMAND'},
    '2913753': {'name': 'BETA (Slave)',   'role': 'ARRAY'},
    '3037513': {'name': 'GAMMA (Relay)',  'role': 'RELAY'},
    '6804071': {'name': 'DELTA (Slave)',  'role': 'ARRAY'},
    '6814519': {'name': 'EPSILON (Slave)','role': 'ARRAY'},
    '7255468': {'name': 'ZETA (Slave)',   'role': 'ARRAY'},
    '7575062': {'name': 'ETA (Control)',  'role': 'CONTROL'}
}

# --- THE PHYSICS LIMITS ---
# Chi = 0.15 translates to specific Magnitude flux limits
MAG_VOID = 15.0   # The Lattice is saturated (Dark)
MAG_PULSE = 11.0  # High Energy Discharge

def scan_sector():
    print(f"--- INITIATING LATTICE COMM SCAN: {datetime.datetime.now()} ---")
    active_nodes = 0
    void_nodes = 0
    
    for nid, info in TARGET_NODES.items():
        url = f"https://asas-sn.osu.edu/variables/{nid}.csv"
        try:
            # 1. Ping the Star
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
                
            # 2. Read the Signal
            df = pd.read_csv(io.StringIO(response.text))
            if df.empty: continue
            
            # 3. Check Last Known State (Top Row)
            latest = df.iloc[0] 
            mag_str = str(latest['mag'])
            
            # 4. Decode State
            status = "QUIET"
            if ">" in mag_str or (float(mag_str) > MAG_VOID):
                status = "VOID (ACTIVE)"
                void_nodes += 1
            elif float(mag_str) < MAG_PULSE:
                status = "PULSE (COMMAND)"
                active_nodes += 1
            
            print(f"NODE {info['name']}: {status} | Mag: {mag_str}")
            
        except Exception as e:
            print(f"NODE {nid}: LINK FAILURE")

    print(f"--- SECTOR SCAN COMPLETE: {void_nodes} VOID / {active_nodes} PULSE ---")

if __name__ == "__main__":
    scan_sector()
