#!/usr/bin/env python3
"""
Imperial Physics Observatory: USGS Historical Magnetometer Data Download
Downloads historical magnetometer data from USGS (1945-1992)
"""

import requests
import pandas as pd
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import time

USGS_BASE_URL = "https://geomag.usgs.gov/ws/data/"

def download_usgs_data(station, start_date, end_date):
    """
    Download USGS magnetometer data for given station and date range
    
    Args:
        station: USGS station code (e.g., 'BOU', 'FRD', 'CMO')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with magnetometer measurements
    """
    results = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current <= end:
        year = current.year
        month = current.month
        day = current.day
        
        # USGS API format: /data/?id=BOU&starttime=2020-01-01T00:00:00Z&endtime=2020-01-02T00:00:00Z&format=json
        url = f"{USGS_BASE_URL}?id={station}&starttime={year:04d}-{month:02d}-{day:02d}T00:00:00Z&endtime={year:04d}-{month:02d}-{day:02d}T23:59:59Z&format=json&elements=X,Y,Z,F"
        
        try:
            print(f"  Downloading {station} data for {year}-{month:02d}-{day:02d}...", end='')
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    for record in data['values']:
                        results.append({
                            'timestamp': record.get('time'),
                            'station': station,
                            'X': record.get('X'),
                            'Y': record.get('Y'),
                            'Z': record.get('Z'),
                            'F': record.get('F')
                        })
                    print(f" OK ({len(data['values'])} records)")
                else:
                    print(" No data")
            else:
                print(f" ERROR (HTTP {response.status_code})")
                
        except Exception as e:
            print(f" ERROR ({str(e)})")
        
        # Rate limiting (be nice to USGS servers)
        time.sleep(0.5)
        
        # Move to next day
        current += timedelta(days=1)
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Download USGS historical magnetometer data')
    parser.add_argument('--station', required=True, help='USGS station code (e.g., BOU, FRD, CMO)')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', required=True, help='Output CSV path')
    
    args = parser.parse_args()
    
    print(f"Downloading USGS magnetometer data:")
    print(f"  Station: {args.station}")
    print(f"  Date range: {args.start} to {args.end}")
    
    df = download_usgs_data(args.station, args.start, args.end)
    
    if len(df) > 0:
        # Ensure output directory exists
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(args.output, index=False)
        print(f"\nDownload complete:")
        print(f"  Total records: {len(df)}")
        print(f"  Saved to: {args.output}")
    else:
        print("\nNo data downloaded (check station code and date range)")

if __name__ == '__main__':
    main()
