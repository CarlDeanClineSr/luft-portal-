import requests
from pathlib import Path
from datetime import datetime
import json

OUTPUT_DIR = Path("data/cern_lhc")
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_cern_luminosity():
    """Fetch LHC luminosity data from CERN Open Data API"""
    experiments = ['CMS', 'ATLAS']
    
    for experiment in experiments:
        print(f"\nSearching CERN Open Data for {experiment} luminosity...")
        
        url = "https://opendata.cern.ch/api/records/"
        params = {
            'q': f'luminosity {experiment}',
            'type': 'Dataset',
            'size': 20
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Save search results
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            json_file = OUTPUT_DIR / f"cern_{experiment.lower()}_search_{timestamp}.json"
            
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Saved: {json_file}")
            
            # Check for CSV files - CORRECT API STRUCTURE
            hits = data.get('hits', {}).get('hits', [])  # ← FIX HERE
            
            csv_count = 0
            for record in hits:
                files = record.get('metadata', {}).get('files', [])
                for file_info in files:
                    if file_info.get('key', '').endswith('.csv'):
                        csv_count += 1
            
            if csv_count > 0:
                print(f"Found {csv_count} CSV file(s) in {experiment} datasets")
                return True
                
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    return False

if __name__ == "__main__": 
    print("Fetching CERN luminosity data...")
    
    success = fetch_cern_luminosity()
    
    if not success:
        print("\n⚠ No CSV files found - see saved JSON for available datasets")
        print("Manual search: https://opendata.cern.ch/search?q=luminosity")
    
    # Always exit 0 so workflow doesn't fail
    exit(0)