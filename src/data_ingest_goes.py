#!/usr/bin/env python3
"""
Ingest GOES proton flux data and produce a cleaned time series for LUFT flare pipeline.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse

def mock_goes(start, end, cadence='5min'):
    # Placeholder: replace with real GOES API or file ingest
    times = pd.date_range(start, end, freq=cadence)
    # Synthetic flare: baseline 5 pfu rising to 120 pfu peak then decay
    peak_time = start + (end - start)/3
    flux = 5 + 115 * np.exp(-((times - peak_time).total_seconds()/3600)**2 / 6)
    return pd.DataFrame({'time': times, 'flux_pfu_gt10MeV': flux})

def load_goes(path=None, start=None, end=None):
    if path and os.path.isfile(path):
        df = pd.read_csv(path, parse_dates=['time'])
        return df
    return mock_goes(start, end)

def preprocess(df):
    df = df.sort_values('time').drop_duplicates('time')
    df['flux_smoothed'] = df['flux_pfu_gt10MeV'].rolling(3, center=True, min_periods=1).mean()
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2025-11-10T00:00:00Z')
    ap.add_argument('--end', default='2025-11-14T00:00:00Z')
    ap.add_argument('--out', default='data/processed/goes_flux.csv')
    ap.add_argument('--source', default=None, help='Optional CSV path')
    args = ap.parse_args()
    df = load_goes(args.source, pd.Timestamp(args.start), pd.Timestamp(args.end))
    df = preprocess(df)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)
    print("Wrote", args.out, "rows:", len(df))

if __name__ == '__main__':
    main()
