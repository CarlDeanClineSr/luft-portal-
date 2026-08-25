from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from historical.download_dscovr_cdaweb import (
    IngestConfig,
    aggregate_magnetic_to_one_minute,
    magnetic_frame_from_arrays,
    plasma_frame_from_arrays,
)
from historical.select_quiet_window import score_windows


def test_magnetic_ingest_keeps_gse_label_and_qc():
    epochs = pd.date_range("2024-05-10", periods=60, freq="s", tz="UTC")
    vector = np.column_stack(
        [np.full(60, 3.0), np.full(60, 4.0), np.zeros(60)]
    )
    frame = magnetic_frame_from_arrays(
        epochs,
        vector,
        provider_magnitude=np.full(60, 5.0),
        quality_flag=np.zeros(60),
    )
    assert "bx_gse" in frame.columns
    assert "bx_gsm" not in frame.columns
    assert frame["bt_qc_pass"].all()

    minute = aggregate_magnetic_to_one_minute(frame)
    assert len(minute) == 1
    assert minute.loc[0, "coordinate_frame"] == "GSE"
    assert minute.loc[0, "valid_seconds"] == 60
    assert minute.loc[0, "bx_gse"] == 3.0


def test_magnetic_minute_rejects_low_coverage():
    epochs = pd.date_range("2024-05-10", periods=44, freq="s", tz="UTC")
    vector = np.column_stack(
        [np.full(44, 3.0), np.full(44, 4.0), np.zeros(44)]
    )
    frame = magnetic_frame_from_arrays(
        epochs,
        vector,
        provider_magnitude=np.full(44, 5.0),
        quality_flag=np.zeros(44),
    )
    minute = aggregate_magnetic_to_one_minute(frame, config=IngestConfig())
    assert minute.empty


def test_plasma_ingest_filters_by_explicit_quality_later():
    epochs = pd.date_range("2024-05-10", periods=2, freq="min", tz="UTC")
    velocity = np.array([[-400.0, 0.0, 0.0], [-500.0, 0.0, 0.0]])
    frame = plasma_frame_from_arrays(
        epochs,
        velocity,
        density=np.array([5.0, 6.0]),
        temperature=np.array([100000.0, 120000.0]),
        quality_flag=np.array([0, 1]),
    )
    assert frame.loc[0, "quality_pass"]
    assert not frame.loc[1, "quality_pass"]
    assert frame.loc[0, "speed"] == 400.0


def test_quiet_selector_uses_kinetics_and_picks_quiet_window():
    # Two 30-day blocks. The first is quiet; the second has high speed.
    times = pd.date_range("2020-04-01", periods=60 * 24 * 60, freq="min", tz="UTC")
    speed = np.full(len(times), 400.0)
    density = np.full(len(times), 5.0)
    speed[30 * 24 * 60 :] = 700.0
    frame = pd.DataFrame({"time_tag": times, "speed": speed, "density": density})

    result = score_windows(
        frame,
        window_days=30,
        stride_days=30,
        minimum_coverage_fraction=0.99,
    )
    assert len(result) == 2
    assert result.iloc[0]["start_utc"].startswith("2020-04-01")
    assert result.iloc[0]["transient_fraction"] == 0.0
    assert result.iloc[1]["transient_fraction"] > 0.99
