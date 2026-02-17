from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://services.swpc.noaa.gov/products/solar-wind"
OUTPUT_DIR = Path("data/noaa_solarwind")


def fetch_json_table(name: str) -> list[list[str]]:
    url = f"{BASE}/{name}.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError(f"Unexpected data shape from {url}")
    return data


def write_csv(table: list[list[str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(table)


def main() -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    mag = fetch_json_table("mag-1-day")
    plasma = fetch_json_table("plasma-1-day")

    mag_path = OUTPUT_DIR / f"noaa_mag_{ts}.csv"
    plasma_path = OUTPUT_DIR / f"noaa_plasma_{ts}.csv"

    write_csv(mag, mag_path)
    write_csv(plasma, plasma_path)

    print(f"Wrote {mag_path}")
    print(f"Wrote {plasma_path}")


if __name__ == "__main__":
    main()
