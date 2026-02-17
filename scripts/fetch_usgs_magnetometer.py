#!/usr/bin/env python3
"""
Fetch 1-minute magnetometer data from ALL USGS observatories.
Stores data per-station in data/usgs_magnetometer/{STATION}/
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# All 13 USGS geomagnetic observatories
STATIONS = ['BOU', 'FRD', 'HON', 'TUC', 'SIT', 'CMO', 'BRW', 'DED', 'SHU', 'NEW', 'SJG', 'GUA', 'BSL']

def fetch_station_data(station_code, hours=24):
    """Fetch last N hours of 1-minute data for given station."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    # Format for USGS API
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # USGS Geomagnetism API
    # Note: elements need to be passed as separate query parameters
    url = (
        f"https://geomag.usgs.gov/ws/data/"
        f"?id={station_code}"
        f"&starttime={start_str}"
        f"&endtime={end_str}"
        f"&elements=X&elements=Y&elements=Z&elements=F"
        f"&sampling_period=60"
        f"&format=json"
    )
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if data exists
        if not data or 'times' not in data or 'values' not in data:
            print(f"⚠️  {station_code}: No data returned")
            return False
        
        # Count data points
        num_times = len(data.get('times', []))
        num_elements = len(data.get('values', []))
        
        # Save to station-specific directory
        station_dir = Path(f'data/usgs_magnetometer/{station_code}')
        station_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = station_dir / f'usgs_{station_code}_{timestamp}.json'
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ {station_code}: {num_times} records saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ {station_code}: {str(e)}")
        return False

def main():
    print(f"Fetching USGS magnetometer data from {len(STATIONS)} observatories...")
    print(f"Time range: Last 24 hours")
    
    success_count = 0
    for station in STATIONS:
        if fetch_station_data(station):
            success_count += 1
    
    print(f"\n✅ Successfully fetched {success_count}/{len(STATIONS)} stations")
    
    # Return success if at least one station was fetched
    return success_count > 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
