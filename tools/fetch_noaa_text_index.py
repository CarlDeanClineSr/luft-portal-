import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

URL = "https://services.swpc.noaa.gov/text/"
OUTPUT_DIR = Path("data/noaa_text")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL)
soup = BeautifulSoup(response.text, 'html.parser')

for link in soup.find_all('a'):
    href = link.get('href')
    if href and href.endswith('.txt'):
        filename = OUTPUT_DIR / href
        file_url = URL + href
        file_response = requests.get(file_url)
        if file_response.status_code == 200:
            with open(filename, 'w') as f:
                f.write(file_response.text)
            print(f"Fetched: {href}")
