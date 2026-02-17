from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

F107_URL = "https://services.swpc.noaa.gov/json/f107_cm_flux.json"
PARSED_DIR = Path("data/noaa_parsed")
REPORT_PATH = Path("reports/latest_f107.md")


def main() -> None:
    response = requests.get(F107_URL, timeout=30)
    response.raise_for_status()
    values = response.json()

    if not isinstance(values, list) or not values:
        raise ValueError("Unexpected F10.7 response format")

    latest = values[-1]
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    latest_json_path = PARSED_DIR / "f107_latest.json"
    latest_json_path.write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")

    report = (
        "# Latest NOAA F10.7\n\n"
        f"Fetched: {datetime.now(timezone.utc).isoformat()}\n\n"
        "```json\n"
        f"{json.dumps(latest, indent=2)}\n"
        "```\n"
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Wrote {latest_json_path}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
