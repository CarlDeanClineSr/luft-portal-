import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# Real public INTERMAGNET data portal (example - adjust if needed)
BASE_URL = "https://intermagnet.org/data-donnee/download-telecharge-eng.php"
OUTPUT_DIR = Path("data/intermagnet")
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_latest_intermagnet():
    try:
        # Step 1: Get the main download page
        response = requests.get(BASE_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 2: Find the latest CSV link (example: look for href ending in .csv)
        csv_link = None
        for a in soup.find_all('a', href=True):
            if a['href'].endswith('.csv'):
                csv_link = a['href']
                break  # Take the first (usually latest)

        if not csv_link:
            print("No CSV link found on page.")
            return

        # Step 3: Download the CSV
        full_url = csv_link if csv_link.startswith('http') else BASE_URL.rsplit('/', 1)[0] + '/' + csv_link
        csv_response = requests.get(full_url, timeout=30)
        csv_response.raise_for_status()

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file = OUTPUT_DIR / f"intermagnet_{timestamp}.csv"
        with open(file, 'wb') as f:
            f.write(csv_response.content)
        print(f"Fetched INTERMAGNET data: {file}")

    except Exception as e:
        print(f"INTERMAGNET fetch failed: {e}")

if __name__ == "__main__":
    fetch_latest_intermagnet()
