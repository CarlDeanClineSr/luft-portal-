#!/usr/bin/env python3
"""
LIGO Gravitational Wave Strain Data Fetcher
Fetches strain h(t) data from LIGO Open Science Center
"""

import requests
import os
import json
from datetime import datetime

# GWOSC API endpoint
BASE_URL = "https://gwosc.org/eventapi/json/allevents/"

def fetch_ligo_strain():
    """Fetch recent LIGO strain data"""
    print("Fetching LIGO strain data...")
    
    # Create output directory
    os.makedirs('data/ligo_gw', exist_ok=True)
    
    try:
        # Fetch event catalog
        response = requests.get(BASE_URL, timeout=30)
        
        if response.status_code == 200:
            events = response.json()
            print(f"Fetched {len(events)} LIGO events")
            
            # Save to file
            output_file = f"data/ligo_gw/events_{datetime.now().strftime('%Y%m%d')}.json"
            with open(output_file, 'w') as f:
                json.dump(events, f, indent=2)
            
            print(f"Saved to {output_file}")
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching LIGO data: {e}")

if __name__ == "__main__":
    fetch_ligo_strain()
