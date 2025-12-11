#!/usr/bin/env python3
"""
data_ingest_goes.py

Minimal GOES proton flux ingestion for LUFT flare foam pipeline.

This matches the plan described in the LUFT relay (e.g., New Text Document (149).txt):
- Read GOES >10 MeV proton flux
- Produce a time-indexed series Φ(t) in pfu
"""

from __future__ import annotations

import pandas as pd


def load_goes_proton_csv(path: str, time_col: str = "time", flux_col: str = "flux_pfu") -> pd.Series:
    """
    Load a GOES proton CSV and return a time-indexed Series Φ(t) in pfu.

    Expected columns (can be adapted by caller):
      - `time_col`: ISO8601 or similar timestamp
      - `flux_col`: proton flux in pfu at >10 MeV (or another selected channel)
    """
    df = pd.read_csv(path)
    df[time_col] = pd.to_datetime(df[time_col], utc=True)
    df = df.set_index(time_col).sort_index()
    phi = df[flux_col].astype(float)
    phi.name = "phi_pfu"
    return phi
