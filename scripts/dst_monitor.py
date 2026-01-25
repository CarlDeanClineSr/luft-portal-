import requests
import datetime
import sys

def fetch_dst_imperial():
    # IMPERIAL ALIGNMENT: Truncate to whole minutes/seconds
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    start_time = (now - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')
    end_time = now.strftime('%Y-%m-%dT%H:%M:%S')

    # USGS Endpoint for Dst
    url = "https://geomag.usgs.gov/ws/data/"
    params = {
        "id": "USGS",
        "type": "dst",
        "starttime": start_time,
        "endtime": end_time,
        "format": "json"
    }

    print(f"🔍 Interrogating Lattice Tension (Dst): {start_time} to {end_time}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            print("✅ Handshake successful. Dst tension recorded.")
            # Here we would save the data, but for now we just verify connection
        else:
            print(f"❌ Handshake failed: {response.status_code} - {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_dst_imperial()
