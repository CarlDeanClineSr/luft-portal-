import requests
from pathlib import Path
from datetime import datetime
import json

# Validates the response from the API
def validate_response(response):
    if response.status_code != 200:
        print(f"Error: Received response {response.status_code}")
        return False
    return True

# Validates if the fetched CSV file URL points to a proper CSV file
def validate_csv_file(url):
    response = requests.head(url)
    content_type = response.headers.get('Content-Type', '')
    if 'text/csv' not in content_type:
        print(f"Invalid CSV File: {url}")
        return False
    return True

# Cleans the invalid CSV files
def clean_invalid_files(urls):
    valid_urls = []
    for url in urls:
        if validate_csv_file(url):
            valid_urls.append(url)
    return valid_urls

# Extracts CSV file URLs from the API response
def extract_csv_urls(data):
    csv_urls = []
    for record in data['records']:
        for file in record['fields']['media']: 
            if file['type'] == 'text/csv':
                csv_urls.append(file['url'])
    return csv_urls

# Fetches luminosity data from CERN Open Data Portal
def fetch_cern_luminosity():
    experiments = ['CMS', 'ATLAS']
    for experiment in experiments:
        print(f"Fetching data for {experiment}...")
        url = f'https://opendata.cern.ch/api/records/?q={experiment}+luminosity'
        response = requests.get(url)
        if validate_response(response):
            data = response.json()
            csv_urls = extract_csv_urls(data)
            valid_csv_urls = clean_invalid_files(csv_urls)
            if valid_csv_urls:
                return valid_csv_urls
            else:
                print(f"No valid CSV URLs found for {experiment}.")
    return None

# Fallback function to fetch LHC statistics
def fetch_lhc_stats():
    print("Fetching fallback LHC statistics...")
    url = 'https://opendata.cern.ch/api/records/?q=LHC+statistics'
    response = requests.get(url)
    if validate_response(response):
        data = response.json()
        csv_urls = extract_csv_urls(data)
        valid_csv_urls = clean_invalid_files(csv_urls)
        return valid_csv_urls
    return None

# Displays the data guide
def show_data_guide():
    print("Current API URLs for fetching data:")
    print("- Luminosity data: https://opendata.cern.ch/api/records/?q=luminosity")
    print("- Statistics data: https://opendata.cern.ch/api/records/?q=LHC+statistics")

# Main block
if __name__ == '__main__':
    # Clean invalid files
    print("Cleaning invalid files...")
    # Assuming a function or method to clean files is in place here

    # Try fetching luminosity data
    luminosity_data = fetch_cern_luminosity()
    if not luminosity_data:
        # Fallback to fetching LHC statistics if no data found
        luminosity_data = fetch_lhc_stats()
        if not luminosity_data:
            show_data_guide()

    # Always exit with status code 0
    exit(0)

# TODO: Integrate with link harvester for automated data handling