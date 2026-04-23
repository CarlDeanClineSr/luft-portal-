#!/usr/bin/env python3
import urllib.request
import json
import os
import datetime
import sys

def main():
    os.makedirs("data/psp", exist_ok=True)
    output_path = "data/psp/psp_daily.json"
    
    today = datetime.date.today()
    max_days_back = 60  # PSP data latency is usually < 30 days
    
    print(f"🛰️  PSP Batch Ingest — starting from {today}")
    
    for days_ago in range(0, max_days_back + 1):
        target_date = today - datetime.timedelta(days=days_ago)
        date_str = target_date.strftime("%Y%m%d")
        api_url = f"https://sscweb.gsfc.nasa.gov/WS/sscr/2/locations/psp/{date_str},{date_str}/json"
        
        print(f"  Trying {date_str} → {api_url}")
        
        try:
            with urllib.request.urlopen(api_url, timeout=15) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read())
                    with open(output_path, "w") as f:
                        json.dump(data, f, indent=2)
                    print(f"✅ SUCCESS: PSP data for {date_str} saved")
                    return 0
        except Exception as e:
            print(f"  ⚠️  No data yet ({e})")
            continue
    
    # Fallback if nothing found (should never happen after 60 days)
    print("⚠️  No recent PSP data found — writing placeholder")
    with open(output_path, "w") as f:
        json.dump({"status": "unavailable", "date": today.strftime("%Y-%m-%d"), "note": "PSP still in cooldown orbit"}, f, indent=2)
    return 1

if __name__ == "__main__":
    sys.exit(main())
