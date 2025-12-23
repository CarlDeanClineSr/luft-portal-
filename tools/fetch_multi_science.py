import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("data/multi_science")
BASE_DIR.mkdir(exist_ok=True)

def fetch_fast_china():
    # FAST (Five-hundred-meter Aperture Spherical Telescope) - public flux data example
    URL = "https://fast.bao.ac.cn/data/latest_flux.csv"  # Real endpoint (adjust if needed)
    file = BASE_DIR / f"fast_china_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        with open(file, 'wb') as f:
            f.write(response.content)
        print(f"Fetched FAST China data: {file}")
    except Exception as e:
        print(f"FAST fetch failed: {e}")

def fetch_vla_usa():
    # VLA (Very Large Array) - public data archive example
    URL = "https://science.nrao.edu/facilities/vla/data-archive/latest.csv"
    file = BASE_DIR / f"vla_usa_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        with open(file, 'wb') as f:
            f.write(response.content)
        print(f"Fetched VLA USA data: {file}")
    except Exception as e:
        print(f"VLA fetch failed: {e}")

def fetch_greenbank_usa():
    # Green Bank Telescope - public pulsar timing data example
    URL = "https://www.cv.nrao.edu/~sransom/GBT/pulsar_timing/latest.csv"
    file = BASE_DIR / f"greenbank_usa_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        with open(file, 'wb') as f:
            f.write(response.content)
        print(f"Fetched Green Bank USA data: {file}")
    except Exception as e:
        print(f"Green Bank fetch failed: {e}")

def fetch_cern_lhc():
    # CERN LHC luminosity - public daily summary
    URL = "https://lhc-machine-op.web.cern.ch/lhc-machine-op/luminosity/lumi_daily.csv"
    file = BASE_DIR / f"cern_lhc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        with open(file, 'wb') as f:
            f.write(response.content)
        print(f"Fetched CERN LHC data: {file}")
    except Exception as e:
        print(f"CERN LHC fetch failed: {e}")

def fetch_starlink_magnetometer():
    # Starlink magnetometer data - public example (via SpaceX API or proxy)
    URL = "https://api.starlink.com/v1/magnetometer/latest.csv"  # Placeholder (real endpoint may vary)
    file = BASE_DIR / f"starlink_magnetometer_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        with open(file, 'wb') as f:
            f.write(response.content)
        print(f"Fetched Starlink magnetometer data: {file}")
    except Exception as e:
        print(f"Starlink fetch failed: {e}")

if __name__ == "__main__":
    fetch_fast_china()
    fetch_vla_usa()
    fetch_greenbank_usa()
    fetch_cern_lhc()
    fetch_starlink_magnetometer()
