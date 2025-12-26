#!/usr/bin/env python3
"""
Fetch real-time magnetometer data from USGS Boulder Observatory
For LUFT plasma boundary analysis (Earth's magnetosphere)
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

def fetch_usgs_magnetometer():
    """Fetch USGS magnetometer data from Boulder observatory"""
    
    # Time range: last 24 hours
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)
    
    # Format for USGS API
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # USGS Geomagnetism API
    # Note: elements need to be passed as separate query parameters, not comma-separated
    url = (
        f"https://geomag.usgs.gov/ws/data/"
        f"?id=BOU"
        f"&starttime={start_str}"
        f"&endtime={end_str}"
        f"&elements=X&elements=Y&elements=Z&elements=F"
        f"&sampling_period=60"
        f"&format=json"
    )
    
    try:
        print(f"🔍 Fetching USGS magnetometer data from Boulder (BOU)...")
        print(f"   Time range: {start_str} to {end_str}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if data exists
        # USGS API returns: {"type": "Timeseries", "times": [...], "values": [{"id": "X", "values": [...]}, ...]}
        if not data or 'times' not in data or 'values' not in data:
            print("⚠️ No magnetometer data returned from USGS")
            return False
        
        # Count data points
        num_times = len(data.get('times', []))
        num_elements = len(data.get('values', []))
        print(f"✅ Retrieved {num_times} time steps with {num_elements} magnetic field elements")
        
        # Save to file
        output_dir = Path("data/usgs_magnetometer")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"usgs_mag_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved: {output_file}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ USGS API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return False

if __name__ == "__main__":
    success = fetch_usgs_magnetometer()
    sys.exit(0 if success else 1)
