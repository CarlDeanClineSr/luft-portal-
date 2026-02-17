import requests
import pandas as pd
import io
import datetime

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
            if df.empty:
                continue
            
            # Sort by HJD (date) to get the most recent observation first
            if 'HJD' in df.columns:
                df = df.sort_values(by='HJD', ascending=False)
            elif 'hjd' in df.columns:
                df = df.sort_values(by='hjd', ascending=False)
            # If no date column found, we'll use the data as-is (typically already sorted)
            
            # 3. Check Last Known State (Top Row)
            latest = df.iloc[0] 
            mag_str = str(latest['mag'])
            
            # 4. Decode State
            status = "QUIET"
            try:
                # Extract numeric value, handling '>' prefix
                mag_numeric = float(mag_str.replace('>', ''))
                
                if ">" in mag_str or mag_numeric > MAG_VOID:
                    status = "VOID (ACTIVE)"
                    void_nodes += 1
                elif mag_numeric < MAG_PULSE:
                    status = "PULSE (COMMAND)"
                    active_nodes += 1
            except (ValueError, AttributeError):
                status = "QUIET (PARSE ERROR)"
            
            print(f"NODE {info['name']}: {status} | Mag: {mag_str}")
            
        except Exception as e:
            print(f"NODE {nid}: LINK FAILURE - {e}")

    print(f"--- SECTOR SCAN COMPLETE: {void_nodes} VOID / {active_nodes} PULSE ---")

if __name__ == "__main__":
    scan_sector()
