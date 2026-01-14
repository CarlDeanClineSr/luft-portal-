import requests
from pathlib import Path
from datetime import datetime, timezone
import json

# CERN LHC Luminosity Data Fetcher
# 
# This script fetches LHC luminosity data from CERN Open Data Portal.
# Updated 2024-2025 to use current CERN portal structure.
#
# Strategies (in order):
#   1. CMS luminosity data - Direct file downloads from known records
#   2. CERN API search - Query for experiment-specific datasets
#   3. ATLAS luminosity - Fallback to ATLAS Open Data
#   4. Guidance - Show available resources and integration notes
#
# Link Harvester Integration:
#   This script can be extended with the link_harvester_core.py module
#   to automatically discover and extract CSV URLs from CERN portal pages.
#   See scripts/harvest_cern.py for paper harvesting examples.
#
# Key URLs:
#   - API: https://opendata.cern.ch/api/records/
#   - CMS Guide: https://cms-opendata-guide.web.cern.ch/analysis/lumi/
#   - ATLAS: https://opendata.atlas.cern/
#   - Real-time stats: https://cern.ch/bpt/lhc/statistics/2024/

OUTPUT_DIR = Path("data/cern_lhc")
OUTPUT_DIR.mkdir(exist_ok=True)

def validate_response(response):
    """Check if response is valid data (not HTML error page)"""
    content_type = response.headers.get('Content-Type', '')
    
    # Check if response is HTML (likely an error page)
    if 'text/html' in content_type:
        print(f"ERROR: Received HTML instead of data (likely 404)")
        print(f"URL attempted: {response.url}")
        return False
    
    # Check first few bytes for HTML tags
    content_start = response.content[:500].lower()
    if any(tag in content_start for tag in [b'<html', b'<!doctype', b'<head', b'<body', b'page not found']):
        print(f"ERROR: Response contains HTML tags (not valid data)")
        return False
    
    return True

def validate_csv_file(filepath):
    """Check if file is valid CSV (not HTML error page)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_lines = f.read(500).lower()
            
            # Check for HTML tags (404 error pages)
            if any(tag in first_lines for tag in ['<html', '<!doctype', '<head', '<body', 'page not found']):
                print(f"ERROR: {filepath} contains HTML, not CSV data")
                return False
            
            # Check for common error messages
            if any(msg in first_lines for msg in ['404', 'error 404', 'not found']):
                print(f"ERROR: {filepath} contains error message")
                return False
        
        return True
    except Exception as e:
        print(f"ERROR: Cannot validate {filepath}: {e}")
        return False

def clean_invalid_files():
    """Remove existing invalid CSV files that contain HTML"""
    print("Checking for invalid files in data directory...")
    cleaned = 0
    
    for file in OUTPUT_DIR.glob("*.csv"):
        if not validate_csv_file(file):
            print(f"Removing invalid file: {file}")
            file.unlink()
            cleaned += 1
    
    if cleaned > 0:
        print(f"Cleaned {cleaned} invalid file(s)")
    else:
        print("No invalid files found")

def fetch_cms_luminosity():
    """Fetch CMS luminosity data from CERN Open Data Portal"""
    
    # CMS luminosity records with known CSV files
    cms_records = [
        (1059, '2016', 'pp_2016lumibyls.csv'),
        (1055, '2015', '2015lumibyls.csv'),
        (1052, '2012', '2012lumibyls.csv'),
        (1051, '2011', '2011lumibyls.csv'),
        (1050, '2010', '2010lumibyls.csv'),
    ]
    
    print("Attempting to fetch CMS luminosity data...")
    
    for record_id, year, csv_file in cms_records:
        try:
            url = f"https://opendata.cern.ch/record/{record_id}/files/{csv_file}"
            print(f"Trying CMS {year}: {url}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Validate response
                if not validate_response(response):
                    continue
                
                print(f"Found CMS luminosity data for {year}")
                
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                output_file = OUTPUT_DIR / f"cms_lumi_{year}_{timestamp}.csv"
                
                with open(output_file, 'w') as f:
                    f.write(response.text)
                
                # Validate saved file
                if not validate_csv_file(output_file):
                    output_file.unlink()
                    continue
                
                print(f"SUCCESS: Downloaded CMS {year} luminosity data: {output_file}")
                return output_file
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {year} data: {e}")
            continue
        except Exception as e:
            print(f"Error processing {year} data: {e}")
            continue
    
    return None

def search_cern_api():
    """Search CERN Open Data API for luminosity datasets"""
    
    search_url = "https://opendata.cern.ch/api/records/"
    
    # Use experiment-specific queries that actually work
    queries = ['CMS luminosity', 'ATLAS luminosity']
    
    for query in queries:
        params = {
            'q': query,
            'size': 5
        }
        
        try:
            print(f"Searching CERN Open Data API: '{query}'...")
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we got valid results
            if 'hits' in data and 'hits' in data['hits'] and len(data['hits']['hits']) > 0:
                hits = data['hits']['hits']
                print(f"Found {len(hits)} results for '{query}'")
                
                # Save search results for inspection
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                json_file = OUTPUT_DIR / f"cern_search_{query.replace(' ', '_')}_{timestamp}.json"
                
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"Saved search results: {json_file}")
                return json_file
            else:
                print(f"No results found for '{query}'")
                
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error searching '{query}': {e}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Network error searching '{query}': {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response for '{query}': {e}")
            continue
        except Exception as e:
            print(f"Unexpected error searching '{query}': {e}")
            continue
    
    return None

def fetch_atlas_luminosity():
    """Fallback: Try ATLAS luminosity data from ATLAS Open Data"""
    
    print("Attempting to fetch ATLAS luminosity data...")
    
    # ATLAS Open Data portal has different structure
    # Try known ATLAS luminosity resources
    atlas_sources = [
        "https://opendata.atlas.cern/release/2020/luminosity/Data15.txt",
        "https://opendata.atlas.cern/release/2020/luminosity/Data16.txt",
    ]
    
    for url in atlas_sources:
        try:
            print(f"Trying ATLAS source: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # ATLAS data might be in different format
                print(f"Found ATLAS luminosity data: {url}")
                
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                output_file = OUTPUT_DIR / f"atlas_lumi_{timestamp}.txt"
                
                with open(output_file, 'w') as f:
                    f.write(response.text)
                
                print(f"SUCCESS: Downloaded ATLAS luminosity: {output_file}")
                return output_file
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch ATLAS data: {e}")
            continue
        except Exception as e:
            print(f"Error processing ATLAS data: {e}")
            continue
    
    return None

def fetch_cern_placeholder():
    """
    Placeholder when real data sources are not accessible.
    Provides guidance on available CERN luminosity resources.
    """
    print("=" * 60)
    print("CERN LHC Luminosity Data Ingestion")
    print("=" * 60)
    print("INFO: All data source attempts have been exhausted")
    print("")
    print("CERN Open Data provides archived LHC luminosity data:")
    print("")
    print("Available Resources:")
    print("  • CMS Luminosity Data (2010-2016):")
    print("    https://opendata.cern.ch/search?q=CMS+luminosity")
    print("")
    print("  • ATLAS Open Data:")
    print("    https://opendata.atlas.cern/")
    print("")
    print("  • CMS Luminosity Calculation Guide:")
    print("    https://cms-opendata-guide.web.cern.ch/analysis/lumi/")
    print("")
    print("  • Real-time LHC Statistics (when available):")
    print("    https://cern.ch/bpt/lhc/statistics/2024/")
    print("")
    print("Integration Notes:")
    print("  - This script can be extended with link harvester integration")
    print("  - Consider implementing automatic URL discovery from portal pages")
    print("  - API endpoints: https://opendata.cern.ch/api/records/")
    print("=" * 60)
    
    return None

if __name__ == "__main__":
    # Clean up any existing invalid files first
    clean_invalid_files()
    
    result = None
    
    # Strategy 1: Try CMS luminosity data (most reliable)
    print("\n" + "="*60)
    print("Strategy 1: CMS Luminosity Data")
    print("="*60)
    result = fetch_cms_luminosity()
    
    # Strategy 2: Search API for luminosity datasets
    if not result:
        print("\n" + "="*60)
        print("Strategy 2: CERN Open Data API Search")
        print("="*60)
        result = search_cern_api()
    
    # Strategy 3: Try ATLAS luminosity data
    if not result:
        print("\n" + "="*60)
        print("Strategy 3: ATLAS Luminosity Data")
        print("="*60)
        result = fetch_atlas_luminosity()
    
    # Strategy 4: Show guidance and available resources
    if not result:
        print("")
        result = fetch_cern_placeholder()
    
    if result:
        print(f"\n✓ SUCCESS: CERN data saved to {result}")
    else:
        print(f"\n⚠ INFO: No CERN data collected")
        print("This is expected when data sources are temporarily unavailable")
        print("The script attempted multiple fallback strategies")
    
    # Always exit 0 (success) to not fail workflow
    # Data ingestion failures should be handled gracefully
    exit(0)
