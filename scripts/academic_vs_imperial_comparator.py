import requests
import csv
import os
from datetime import datetime, timezone

# NOAA SWPC Real-time JSON endpoints
PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
LOG_FILE = "data/academic_vs_imperial_storm_log.csv"

# Imperial Constants
CHI_CEILING = 0.15

FIELDNAMES = [
    "timestamp_utc",
    "speed_km_s",
    "density_p_cm3",
    "bz_nT",
    "bt_nT",
    "academic_unbounded_stress",
    "imperial_chi_regulated",
    "boundary_status",
]


def fetch_latest(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # First row is the header; return the last data row
        return data[-1] if len(data) > 1 else None
    except Exception as e:
        print(f"Feed error: {e}")
        return None


def run_comparator():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Initiating Academic vs Imperial Dual-Read...")

    plasma = fetch_latest(PLASMA_URL)
    mag = fetch_latest(MAG_URL)

    if not plasma or not mag:
        print("Data dropout detected. Lattice sensors may be blinded.")
        return

    timestamp = mag[0]
    try:
        density = float(plasma[1])
        speed = float(plasma[2])
        bz = float(mag[3])
        bt = float(mag[6])
    except (TypeError, ValueError) as exc:
        print(f"[{timestamp}] Sensor noise/NaN detected. Skipping calculation. ({exc})")
        return

    # --- THE ACADEMIC STANDARD (Unbounded) ---
    # Standard dynamic pressure proxy scales infinitely with density and velocity squared
    academic_kinetic_stress = (density * (speed ** 2)) / 1e6

    # --- THE IMPERIAL MEASUREMENT (Regulated) ---
    # Maps the raw kinetic stress to the vacuum chi scale
    raw_chi_proxy = academic_kinetic_stress * 0.05  # Baseline scaling factor

    # Apply the physical vacuum limit
    if raw_chi_proxy > CHI_CEILING:
        imperial_chi = CHI_CEILING
        status = "AT_BOUNDARY"
    else:
        imperial_chi = round(raw_chi_proxy, 4)
        status = "BELOW"

    row = {
        "timestamp_utc": timestamp,
        "speed_km_s": speed,
        "density_p_cm3": density,
        "bz_nT": bz,
        "bt_nT": bt,
        "academic_unbounded_stress": round(academic_kinetic_stress, 4),
        "imperial_chi_regulated": imperial_chi,
        "boundary_status": status,
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(
        f"Logged: Speed {speed} km/s | Density {density} p/cm³ | "
        f"Bz {bz} nT | Bt {bt} nT | "
        f"Academic Stress: {row['academic_unbounded_stress']} | "
        f"Imperial Chi: {row['imperial_chi_regulated']} [{status}]"
    )


if __name__ == "__main__":
    run_comparator()
