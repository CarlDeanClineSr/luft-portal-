#!/usr/bin/env python3
"""
MAVEN Master Harvester v2
Extended version of maven_master_harvester.py with additional features:
  - FILE_LIMIT parameter for limiting records (useful for testing)
  - clean_old parameter cleans old CSVs before harvest (default True)
  - Richer per-record metadata (chi parameter, B_baseline)

Each run creates a fresh timestamped CSV – no appending, no duplicates.

Designed to run in Google Colab with Google Drive mounted at
/content/drive/My Drive/MAVEN_DATA_LAKE/  or locally when
MAVEN_DATA_LAKE_DIR is overridden.

Usage (Colab):
    from google.colab import drive
    drive.mount('/content/drive')
    exec(open('maven_master_harvester2.py').read())
    harvest_maven(file_limit=10, clean_old=True)   # test with 10 rows

Usage (local / CI):
    python maven_master_harvester2.py
"""

import os
import glob
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAVEN_DATA_LAKE_DIR = os.environ.get(
    'MAVEN_DATA_LAKE_DIR',
    '/content/drive/My Drive/MAVEN_DATA_LAKE'
)

# Default record limit used when running as a script.
# Override via the file_limit parameter in harvest_maven() for production runs:
#   harvest_maven(file_limit=None)   # fetch all available records
FILE_LIMIT = 10


# ---------------------------------------------------------------------------
# Physics helpers
# ---------------------------------------------------------------------------
def calculate_chi(b_mag, baseline_percentile=10):
    """
    Calculate χ = |B - B_baseline| / B_baseline.

    Parameters
    ----------
    b_mag : array-like
        Magnetic field magnitudes.
    baseline_percentile : int
        Percentile used for the quiet-time baseline.

    Returns
    -------
    chi : ndarray
    b_baseline : float
    """
    b_mag = np.asarray(b_mag, dtype=float)
    b_baseline = np.nanpercentile(b_mag, baseline_percentile)
    if b_baseline == 0:
        b_baseline = np.nanmean(b_mag) if not np.all(np.isnan(b_mag)) else 1.0
    chi = np.abs(b_mag - b_baseline) / b_baseline
    return chi, float(b_baseline)


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
    Return a list of MAVEN record dicts including chi values.

    Replace this function body with real CDAWeb / SPDF API calls.
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
        ob_b = result[1]['OB_B']
        epoch = ob_b.coords['epoch'].values
        vals = ob_b.values

        b_mags = [(vals[i][0]**2 + vals[i][1]**2 + vals[i][2]**2) ** 0.5
                  for i in range(len(epoch))]
        chi_vals, b_baseline = calculate_chi(b_mags)

        records = []
        for i, t in enumerate(epoch):
            bx, by, bz = vals[i]
            records.append({
                'time': str(pd.Timestamp(t)),
                'Bx': float(bx),
                'By': float(by),
                'Bz': float(bz),
                'B_mag': float(b_mags[i]),
                'chi': float(chi_vals[i]),
                'B_baseline': float(b_baseline),
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
def harvest_maven(file_limit=FILE_LIMIT, clean_old=True):
    """
    Run the MAVEN master harvest (v2).

    Parameters
    ----------
    file_limit : int or None
        Cap on the number of records fetched.  Use a small value (e.g. 10)
        to verify there are no duplicates before a full production run.
    clean_old : bool
        When True (default), remove all previous maven_master_summary_*.csv
        files before saving the new one, preventing accumulation of stale
        harvest files.
    """
    os.makedirs(MAVEN_DATA_LAKE_DIR, exist_ok=True)

    if clean_old:
        clean_old_harvests(MAVEN_DATA_LAKE_DIR)

    print(f"Fetching MAVEN records (limit={file_limit})…")
    records = fetch_maven_records(file_limit=file_limit)
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
