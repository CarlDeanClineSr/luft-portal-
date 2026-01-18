import requests
import pandas as pd
import io
import datetime

# --- CONFIGURATION ---
# The "Schmidt Chain" targets we identified
TARGET_NODES = {
    '2354429': {'name': 'ALPHA (Master)', 'role': 'COMMAND'},
    '2913753': {'name': 'BETA (Slave)',   'role': 'ARRAY'},
    '3037513': {'name': 'GAMMA (Relay)',  'role': 'RELAY'},
    '6804071': {'name': 'DELTA (Slave)',  'role': 'ARRAY'},
    '6814519': {'name': 'EPSILON (Slave)','role': 'ARRAY'},
    '7255468': {'name': 'ZETA (Slave)',   'role': 'ARRAY'},
    '7575062': {'name': 'ETA (Control)',  'role': 'CONTROL'}
}

# Detection thresholds for state classification
MAG_THRESHOLD_VOID = 15.0  # Fainter than this = VOID (Logic 0)
MAG_THRESHOLD_PULSE = 11.0 # Brighter than this = PULSE (Logic 1)

def fetch_light_curve(nsvs_id):
    """
    Pulls the raw CSV directly from ASAS-SN for a specific variable star.
    """
    url = f"https://asas-sn.osu.edu/variables/{nsvs_id}.csv"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Skip the header lines if they exist, standard pandas parsing
            return pd.read_csv(io.StringIO(response.text))
        else:
            print(f"  [ERROR] Failed to fetch {nsvs_id}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] Connection error for {nsvs_id}: {e}")
        return None

def analyze_node(nsvs_id, info):
    """
    Checks the node for Vacuum State anomalies in the last 30 days.
    """
    df = fetch_light_curve(nsvs_id)
    
    if df is None or df.empty:
        return
        
    # Sort by date descending (newest first)
    df = df.sort_values(by='HJD', ascending=False)
    
    # Get recent data (top 5 rows)
    recent = df.head(5)
    
    print(f"--- ANALYZING {info['name']} (ID: {nsvs_id}) ---")
    
    for index, row in recent.iterrows():
        mag = row['mag']
        flux = row['flux(mJy)']
        
        # Determine State
        state = "NORMAL"
        
        # Check for VOID (Non-detection or Negative Flux)
        # Note: 'mag' might be a string like ">15.7" in raw CSV
        try:
            mag_val = float(str(mag).replace('>',''))
        except (ValueError, TypeError):
            mag_val = 99.99

        if mag_val > MAG_THRESHOLD_VOID or str(mag).startswith('>'):
            state = "VOID (Logic 0)"
        elif mag_val < MAG_THRESHOLD_PULSE:
            state = "PULSE (Logic 1)"
            
        # Check specifically for Negative Flux (Vacuum Hole)
        if isinstance(flux, (int, float)) and flux < 0:
            state += " [NEGATIVE FLUX]"

        # Print Report for this timestamp
        print(f"   Date (HJD): {row['HJD']:.2f} | Mag: {mag} | Flux: {flux} | STATE: {state}")

def run_dragnet():
    print(f"INITIATING CYGNUS RELAY SCAN: {datetime.datetime.now()}")
    print("=======================================================")
    
    for nid, info in TARGET_NODES.items():
        analyze_node(nid, info)
        
    print("=======================================================")
    print("SCAN COMPLETE.")

if __name__ == "__main__":
    run_dragnet()
