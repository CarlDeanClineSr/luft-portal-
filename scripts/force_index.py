import requests
import urllib.parse

# THE TARGETS
urls = [
    "https://carldeanclinesr.github.io/luft-portal-/",
    "https://zenodo.org/record/18445020",
    "https://zenodo.org/record/18443409"
]

print("IMPERIAL INDEXER: INITIATING PING SEQUENCE...")
print("-" * 50)

# 1. PING BING (Microsoft Network)
for url in urls:
    encoded_url = urllib.parse.quote(url)
    ping_url = f"https://www.bing.com/ping?sitemap={encoded_url}"
    
    try:
        response = requests.get(ping_url)
        if response.status_code == 200:
            print(f"[SUCCESS] Bing Notified: {url}")
        else:
            print(f"[FAIL] Bing Error {response.status_code}: {url}")
    except Exception as e:
        print(f"[ERROR] Could not reach Bing: {e}")

print("-" * 50)
print("SEQUENCE COMPLETE. The crawlers have been summoned.")
