#!/usr/bin/env python3
"""
Unit test skeleton for tools/merge_noaa_omni_heartbeat.py
Validates time alignment and derived field computation on synthetic sample.
"""

import pandas as pd
from pathlib import Path
import pytest
from tools import merge_noaa_omni_heartbeat as merge

def test_compute_derived_fields(tmp_path):
    # Synthetic sample
    df = pd.DataFrame({
        "time_tag": ["2025-12-18T00:00Z","2025-12-18T01:00Z"],
        "density": [5.0, 6.0],
        "speed": [400.0, 420.0],
        "bz_gsm": [-5.0, 3.0]
    })
    df = merge.compute_derived(df)
    assert "pressure_npa" in df.columns
    assert "E_mVpm" in df.columns
    # Pressure should be positive
    assert all(df["pressure_npa"] > 0)
    # Electric field sign check
    assert df.loc[0,"E_mVpm"] > 0  # -V * Bz with Bz negative
    assert df.loc[1,"E_mVpm"] < 0  # Bz positive

def test_merge_no_inputs(monkeypatch):
    monkeypatch.setattr(merge, "read_latest_noaa", lambda: pd.DataFrame())
    monkeypatch.setattr(merge, "load_omni", lambda: pd.DataFrame())
    monkeypatch.setattr(merge, "load_heartbeat", lambda: pd.DataFrame())
    merge.main()  # Should warn and exit gracefully
