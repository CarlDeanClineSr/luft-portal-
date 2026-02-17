#!/usr/bin/env python3
"""
NOAA Text Feed Parser
Parses NOAA space weather text products
"""

import requests
import os
import sys
from datetime import datetime

# NOAA text feed URLs
FEEDS = {
    'srs': 'https://services.swpc.noaa.gov/text/solar-region-summary.txt',
    'forecast': 'https://services.swpc.noaa.gov/text/3-day-forecast.txt',
    '27day': 'https://services.swpc.noaa.gov/text/27-day-outlook.txt'
}

def parse_noaa_text(output_dir='data/noaa_text'):
    """Fetch and save NOAA text feeds"""
    print("Fetching NOAA text feeds...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for feed_name, url in FEEDS.items():
        print(f"Fetching {feed_name}...")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                output_file = f"{output_dir}/{feed_name}_{timestamp}.txt"
                with open(output_file, 'w') as f:
                    f.write(response.text)
                print(f"  Saved: {output_file}")
            else:
                print(f"  Error: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Fetch NOAA text feeds')
    parser.add_argument('--output', default='data/noaa_text', help='Output directory')
    args = parser.parse_args()
    
    parse_noaa_text(args.output)
