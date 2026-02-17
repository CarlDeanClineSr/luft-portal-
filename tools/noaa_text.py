"""
NOAA Text Pipeline – Ingest + Parse SWPC /text/ Bulletins

1. Ingest:
   - Fetches all products from NOAA SWPC /text/ directory
   - Saves each as data/noaa_text/<product>/<YYYYMMDD>.txt

2. Parse:
   - Reads all saved text files
   - Extracts basic metadata (product, filename, timestamp, alert level, region)
   - Writes:
       data/noaa_parsed/noaa_bulletins.jsonl
       data/noaa_parsed/noaa_summary.csv

Usage:
    python tools/noaa_text.py

Dependencies:
    - requests
    - beautifulsoup4
    - pandas
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

TEXT_URL = "https://services.swpc.noaa.gov/text/"
ARCHIVE_DIR = Path("data/noaa_text")
PARSED_DIR = Path("data/noaa_parsed")

JSONL_PATH = PARSED_DIR / "noaa_bulletins.jsonl"
SUMMARY_PATH = PARSED_DIR / "noaa_summary.csv"

# ---------------------------------------------------------------------
# INGEST LAYER
# ---------------------------------------------------------------------

def get_file_list():
    """
    Fetch the NOAA /text/ index and return a list of .txt filenames.
    """
    print(f"[INGEST] Fetching index from {TEXT_URL} ...")
    res = requests.get(TEXT_URL, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    files = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and re.match(r"^[\w\-\_\.]+\.txt$", href):
            files.append(href)

    print(f"[INGEST] Found {len(files)} .txt products in /text/")
    return files


def fetch_and_save(file_name, today_str=None):
    """
    Download a single NOAA text file and save to data/noaa_text/<product>/<YYYYMMDD>.txt
    """
    if today_str is None:
        today_str = datetime.utcnow().strftime("%Y%m%d")

    product = file_name.split(".")[0].replace("-", "_")
    prod_dir = ARCHIVE_DIR / product
    prod_dir.mkdir(parents=True, exist_ok=True)

    url = TEXT_URL + file_name
    try:
        resp = requests.get(url, timeout=30)
        if resp.ok and resp.text.strip():
            file_path = prod_dir / f"{today_str}.txt"
            file_path.write_text(resp.text, encoding="utf-8")
            print(f"[INGEST] Saved: {file_path}")
        else:
            print(f"[INGEST] Skipped: {url} (no content or fetch error)")
    except Exception as e:
        print(f"[INGEST] Error for {url}: {e}")


def run_ingest():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    file_list = get_file_list()
    today_str = datetime.utcnow().strftime("%Y%m%d")

    for file_name in file_list:
        fetch_and_save(file_name, today_str=today_str)

    print("[INGEST] NOAA text ingest complete.")


# ---------------------------------------------------------------------
# PARSE LAYER
# ---------------------------------------------------------------------

# NOAA timestamp patterns
TS_PATTERNS = [
    r"(\d{4} \w{3} \d{1,2} \d{2}:\d{2} UTC)",   # 2025 Dec 28 12:34 UTC
    r"(\w{3} \d{1,2} \d{4} \d{2}:\d{2} UTC)",   # Dec 28 2025 12:34 UTC
    r"(\d{2}:\d{2} UTC)",                       # 12:34 UTC
]


def extract_timestamp(text: str):
    """
    Try to find and normalize a timestamp in the NOAA bulletin text.
    Returns ISO-8601 string or None.
    """
    for pat in TS_PATTERNS:
        m = re.search(pat, text)
        if m:
            ts = m.group(1)
            # Try several possible datetime formats
            for fmt in (
                "%Y %b %d %H:%M UTC",
                "%b %d %Y %H:%M UTC",
                "%H:%M UTC",
            ):
                try:
                    dt = datetime.strptime(ts, fmt)
                    # If date is partial (only time), leave date as None
                    if fmt == "%H:%M UTC":
                        # Time only; return time string, no date context
                        return dt.time().isoformat()
                    return dt.isoformat()
                except Exception:
                    continue
    return None


def extract_alert_level(text: str) -> str:
    """
    Detect NOAA alert levels like:
      - WARNING
      - WATCH
      - ALERT
      - SUMMARY
      - FORECAST
    Fallback: INFO
    """
    levels = ["WARNING", "WATCH", "ALERT", "SUMMARY", "FORECAST"]
    upper = text.upper()
    for lvl in levels:
        if lvl in upper:
            return lvl
    return "INFO"


def extract_region(text: str):
    """
    Extract region codes like:
      - R1, R2, R3 (Radio Blackout)
      - S1, S2, S3 (Solar Radiation)
      - G1, G2, G3 (Geomagnetic Storm)
    """
    m = re.search(r"\b([RSG]\d)\b", text)
    return m.group(1) if m else None


def parse_bulletin(product: str, txt_path: Path) -> dict:
    """
    Parse a single NOAA bulletin file into a structured record.
    """
    raw_text = txt_path.read_text(errors="ignore")
    return {
        "product": product,
        "filename": txt_path.name,
        "filepath": str(txt_path),
        "timestamp": extract_timestamp(raw_text),
        "alert_level": extract_alert_level(raw_text),
        "region": extract_region(raw_text),
        "body": raw_text.strip(),
    }


def run_parse():
    """
    Parse all ingested NOAA text files and write JSONL + CSV.
    """
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    records = []

    if not ARCHIVE_DIR.exists():
        print("[PARSE] No archive directory found, skipping parse.")
        return

    for product_dir in ARCHIVE_DIR.iterdir():
        if not product_dir.is_dir():
            continue

        product = product_dir.name

        for txt_file in product_dir.glob("*.txt"):
            rec = parse_bulletin(product, txt_file)
            records.append(rec)

    if not records:
        print("[PARSE] No NOAA bulletins found to parse.")
        return

    # Write JSONL
    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    print(f"[PARSE] Saved parsed bulletins → {JSONL_PATH}")

    # Write summary CSV
    df = pd.DataFrame(records)
    df.to_csv(SUMMARY_PATH, index=False)
    print(f"[PARSE] Saved summary table → {SUMMARY_PATH}")

    print(f"[PARSE] Parsed {len(records)} NOAA bulletins.")


# ---------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------

def main():
    print("=== NOAA TEXT PIPELINE START ===")
    run_ingest()
    run_parse()
    print("=== NOAA TEXT PIPELINE COMPLETE ===")


if __name__ == "__main__":
    main()
