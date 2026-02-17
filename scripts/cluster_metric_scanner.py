import requests
import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

def fetch_light_curve(coordinates):
    # Parse coords
    coord = SkyCoord(coordinates, frame='icrs')
    ra = coord.ra.to_string(unit=u.hourangle, sep=':', pad=True)
    dec = coord.dec.to_string(unit=u.degree, sep=':', pad=True, alwayssign=True)

    # Example pull from ASAS-SN API (replace with real endpoint or VizieR query)
    url = f"https://asas-sn.osu.edu/api/v2/light_curves?ra={ra}&dec={dec}&radius=5&limit=1000"  # Placeholder ASAS-SN query
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()['data']
        df = pd.DataFrame(data)
        df['mjd'] = pd.to_datetime(df['mjd'], unit='d', origin='julian')
        return df
    return pd.DataFrame()

def compute_chi(df):
    # Imperial χ on flux perturbations (replace 'flux' with real column)
    baseline = df['flux'].rolling(window=24*60).median()  # 24-hour rolling baseline (min resolution)
    df['chi'] = np.abs(df['flux'] - baseline) / baseline
    max_chi = df['chi'].max()
    mean_chi = df['chi'].mean()
    violations = (df['chi'] > 0.15).sum()
    attractor_pct = ((df['chi'] > 0.145) & (df['chi'] < 0.155)).mean() * 100
    harmonic_mode = int(np.log2(max_chi / 0.15)) if max_chi > 0.15 else 0
    is_transition = harmonic_mode > 0

    snapshot = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "source": "ASAS-SN/FAST",
        "data_points": len(df),
        "max_chi": max_chi,
        "mean_chi": mean_chi,
        "violations": violations,
        "attractor_percentage": attractor_pct,
        "compliance": violations == 0,
        "harmonic_mode": harmonic_mode,
        "is_harmonic_transition": is_transition
    }
    with open(f"measurements/cluster_events/{pd.Timestamp.now().strftime('%Y-%m-%dT%H:%M:%S')}.json", 'w') as f:
        import json
        json.dump(snapshot, f)
    print("Snapshot saved.")

if __name__ == "__main__":
    df = fetch_light_curve("RA:20h06m15.457s Dec:+44d27m24.75s")
    if not df.empty:
        compute_chi(df)
    else:
        print("No data fetched.")
