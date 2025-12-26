#!/usr/bin/env python3
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
import urllib3

# Disable SSL warnings (Oulu has cert issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def fetch_oulu_data():
    """Fetch Oulu cosmic ray neutron monitor data with SSL bypass"""
    
    url = "https://cosmicrays.oulu.fi/phi/Phi_mon.txt"
    output_dir = Path("data/oulu_cr")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Bypass SSL verification (Oulu site has expired cert)
        response = requests. get(url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Save raw data
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"oulu_cr_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write(response.text)
        
        print(f"✅ Oulu data saved:  {output_file}")
        
        # Parse to CSV
        lines = response.text.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        
        if len(data_lines) > 0:
            csv_file = output_dir / f"oulu_cr_{timestamp}. csv"
            with open(csv_file, 'w') as f:
                f.write("year,month,neutron_count\n")
                for line in data_lines: 
                    parts = line.split()
                    if len(parts) >= 3:
                        f.write(f"{parts[0]},{parts[1]},{parts[2]}\n")
            print(f"✅ CSV saved: {csv_file}")
        
        return True
        
    except requests.exceptions.SSLError as e:
        print(f"⚠️ SSL error (bypassed): {e}")
        return False
    except Exception as e: 
        print(f"❌ Oulu fetch failed: {e}")
        return False

if __name__ == "__main__": 
    success = fetch_oulu_data()
    exit(0 if success else 1)
