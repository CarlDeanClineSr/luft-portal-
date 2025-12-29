"""
NOAA /text/ Crawler – Ingest and Archive All SWPC Bulletins Daily

Fetches all products from NOAA SWPC /text/ directory,
saves each as data/noaa_text/<product>/<YYYYMMDD>.txt
Ready for downstream parsing and analysis.

Usage: python tools/noaa_text_ingest.py
Dependencies: requests, beautifulsoup4
"""

import os, re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TEXT_URL = "https://services.swpc.noaa.gov/text/"
ARCHIVE_DIR = "data/noaa_text"

# Helper: extract file list from /text/ index
def get_file_list():
    res = requests.get(TEXT_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    files = [a.get('href') for a in soup.find_all('a') if re.match(r'^[\w\-\_\.]+\.txt$', a.get('href'))]
    return files

def fetch_and_save(file_name):
    today = datetime.utcnow().strftime("%Y%m%d")
    product = file_name.split('.')[0].replace("-", "_")
    prod_dir = os.path.join(ARCHIVE_DIR, product)
    os.makedirs(prod_dir, exist_ok=True)
    url = TEXT_URL + file_name
    try:
        resp = requests.get(url)
        if resp.ok and resp.text.strip() != "":
            file_path = os.path.join(prod_dir, f"{today}.txt")
            with open(file_path, "w") as f:
                f.write(resp.text)
            print(f"Saved: {file_path}")
        else:
            print(f"Skipped: {url} (no content or fetch error)")
    except Exception as e:
        print(f"Error for {url}: {e}")

def main():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    file_list = get_file_list()
    print(f"Found {len(file_list)} products in /text/")
    for file_name in file_list:
        fetch_and_save(file_name)

if __name__ == "__main__":
    main()
