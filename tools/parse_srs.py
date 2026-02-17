from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests

SRS_URL = "https://services.swpc.noaa.gov/text/srs.txt"
PARSED_DIR = Path("data/noaa_parsed")
REPORT_PATH = Path("reports/latest_srs.md")


def main() -> None:
    response = requests.get(SRS_URL, timeout=30)
    response.raise_for_status()
    body = response.text.strip()
    fetched_at = datetime.now(timezone.utc)

    ts = fetched_at.strftime("%Y%m%d_%H%M%S")
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw_path = PARSED_DIR / f"srs_{ts}.txt"
    raw_path.write_text(body + "\n", encoding="utf-8")

    REPORT_PATH.write_text(
        "# Latest NOAA SRS\n\n"
        f"Fetched: {fetched_at.isoformat()}\n\n"
        "```text\n"
        f"{body}\n"
        "```\n",
        encoding="utf-8",
    )

    print(f"Wrote {raw_path}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
