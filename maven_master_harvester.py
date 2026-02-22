#!/usr/bin/env python3
"""
MAVEN Master Harvester
Fetches MAVEN Mars plasma and magnetic field data and saves to a
timestamped CSV file.  Each run creates a fresh file – no appending,
no duplicate rows.

Designed to run in Google Colab with Google Drive mounted at
/content/drive/My Drive/MAVEN_DATA_LAKE/  or locally when
MAVEN_DATA_LAKE_DIR is overridden.

Usage (Colab):
    from google.colab import drive
    drive.mount('/content/drive')
    exec(open('maven_master_harvester.py').read())
    harvest_maven()

Usage (local / CI):
    python maven_master_harvester.py
"""

import os
import glob
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAVEN_DATA_LAKE_DIR = os.environ.get(
    'MAVEN_DATA_LAKE_DIR',
    '/content/drive/My Drive/MAVEN_DATA_LAKE'
)

# Limit number of records fetched (set to None for unlimited)
FILE_LIMIT = None


# ---------------------------------------------------------------------------
# Data saving – always writes a fresh file (never appends)
# ---------------------------------------------------------------------------
def save_data(data_list, path):
    """Persist *data_list* to *path*, overwriting any existing file."""
    if not data_list:
        return
    df = pd.DataFrame(data_list)
    # Always write a fresh CSV – header included, no append
    df.to_csv(path, mode='w', header=True, index=False)
    print(f"Saved {len(df)} records to {path}")


# ---------------------------------------------------------------------------
# Optional helper: remove previous harvest files before starting
# ---------------------------------------------------------------------------
def clean_old_harvests(data_lake_dir):
    """Delete all prior maven_master_summary_*.csv files in *data_lake_dir*."""
    pattern = os.path.join(data_lake_dir, 'maven_master_summary_*.csv')
    for old_file in glob.glob(pattern):
        os.remove(old_file)
        print(f"Deleted old harvest: {old_file}")


# ---------------------------------------------------------------------------
# Stub data-fetch – replace with real CDAWeb / API calls as needed
# ---------------------------------------------------------------------------
def fetch_maven_records(file_limit=None):
    """
    Return a list of MAVEN record dicts.

    Replace this function body with real CDAWeb / SPDF API calls.
    The stub returns a minimal synthetic dataset so the script is
    runnable in CI without network access.
    """
    try:
        from cdasws import CdasWs
        cdas = CdasWs()
        end = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start = end - timedelta(days=1)
        dataset = 'MVN_MAG_L2-SUNSTATE-1SEC'
        result = cdas.get_data(dataset, ['OB_B'],
                               start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                               end.strftime('%Y-%m-%dT%H:%M:%SZ'))
        if not result or len(result) < 2 or result[1] is None:
            return []
        import numpy as np
        ob_b = result[1]['OB_B']
        epoch = ob_b.coords['epoch'].values
        vals = ob_b.values
        records = []
        for i, t in enumerate(epoch):
            bx, by, bz = vals[i]
            records.append({
                'time': str(pd.Timestamp(t)),
                'Bx': float(bx),
                'By': float(by),
                'Bz': float(bz),
                'B_mag': float((bx**2 + by**2 + bz**2) ** 0.5),
            })
            if file_limit and len(records) >= file_limit:
                break
        return records
    except Exception as e:
        print(f"Warning: could not fetch live MAVEN data ({e}). Using empty dataset.")
        return []


# ---------------------------------------------------------------------------
# Main harvest entry point
# ---------------------------------------------------------------------------
def harvest_maven(clean_old=True):
    """
    Run the MAVEN master harvest.

    Parameters
    ----------
    clean_old : bool
        When True (default), remove all previous maven_master_summary_*.csv
        files before saving the new one.
    """
    os.makedirs(MAVEN_DATA_LAKE_DIR, exist_ok=True)

    if clean_old:
        clean_old_harvests(MAVEN_DATA_LAKE_DIR)

    print("Fetching MAVEN records…")
    records = fetch_maven_records(file_limit=FILE_LIMIT)
    print(f"Fetched {len(records)} records")

    # Each run gets its own uniquely named file – no duplicate rows possible
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(
        MAVEN_DATA_LAKE_DIR,
        f'maven_master_summary_{timestamp}.csv'
    )

    save_data(records, csv_path)
    return csv_path


if __name__ == '__main__':
    output = harvest_maven()
    print(f"Done. Output: {output}")
