#!/usr/bin/env python3
"""
Fetch Dst (Disturbance Storm Time) index from USGS.
Hourly values, global geomagnetic storm indicator.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

DST_URL = 'https://geomag.usgs.gov/ws/data/'

def fetch_dst(days=7):
    """Fetch last N days of Dst index (hourly)."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    # Format for USGS API
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # USGS API for Dst index
    url = (
        f"{DST_URL}"
        f"?id=dst"
        f"&starttime={start_str}"
        f"&endtime={end_str}"
        f"&format=json"
    )
    
    try:
        print(f"🔍 Fetching Dst index from USGS...")
        print(f"   Time range: {start_str} to {end_str}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Parse USGS format
        if not data or 'times' not in data or 'values' not in data:
            print("⚠️ No Dst data returned from USGS")
            return False
        
        times = data.get('times', [])
        # Extract Dst values from the first element in values array
        dst_values = []
        if len(data.get('values', [])) > 0:
            dst_values = data['values'][0].get('values', [])
        
        if not times or not dst_values:
            print("⚠️ No Dst data points found")
            return False
        
        # Create DataFrame
        df = pd.DataFrame({
            'time': times,
            'dst': dst_values
        })
        
        # Save
        output_dir = Path('data/dst_index')
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f'dst_{timestamp}.csv'
        df.to_csv(output_path, index=False)
        
        print(f"✅ Dst index: {len(df)} hourly values saved to {output_path}")
        
        # Print latest value
        if len(df) > 0:
            latest_dst = df.iloc[-1]['dst']
            latest_time = df.iloc[-1]['time']
            print(f"   Latest Dst: {latest_dst} nT at {latest_time}")
            
            # Interpret storm level
            if latest_dst > -30:
                level = "Quiet"
            elif latest_dst > -50:
                level = "Minor storm (G1)"
            elif latest_dst > -100:
                level = "Moderate storm (G2-G3)"
            elif latest_dst > -200:
                level = "Strong storm (G4)"
            else:
                level = "Extreme storm (G5)"
            print(f"   Storm level: {level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dst fetch failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = fetch_dst()
    sys.exit(0 if success else 1)
