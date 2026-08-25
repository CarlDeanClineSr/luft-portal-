from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cline_l1_chain_v1 import (
    PROTOCOL_ID,
    ProtocolConfig,
    compute_frozen_baseline,
    load_magnetic,
    merge_plasma_and_classify,
)


def magnetic_frame(start: str, periods: int, value: float = 10.0) -> pd.DataFrame:
    t = pd.date_range(start, periods=periods, freq="min", tz="UTC")
    return pd.DataFrame(
        {
            "time_tag": t,
            "bx_gsm": np.full(periods, value),
            "by_gsm": np.zeros(periods),
            "bz_gsm": np.zeros(periods),
            "lon_gsm": np.full(periods, 300.0),
            "lat_gsm": np.zeros(periods),
            "bt": np.full(periods, value),
            "B_vector_nT": np.full(periods, value),
            "B_provider_nT": np.full(periods, value),
            "bt_abs_error_nT": np.zeros(periods),
            "bt_qc_pass": np.ones(periods, dtype=bool),
        }
    )


def test_protocol_name_is_frozen():
    assert PROTOCOL_ID == "CLINE-L1-B24M-TRAIL-v1"


def test_field_mapping_uses_names_not_position(tmp_path: Path):
    rows = [
        ["time_tag", "bx_gsm", "by_gsm", "bz_gsm", "lon_gsm", "lat_gsm", "bt"],
        ["2026-01-01 00:00:00.000", "3", "4", "0", "299", "10", "5"],
    ]
    source = tmp_path / "mag.json"
    source.write_text(json.dumps(rows), encoding="utf-8")

    frame, metadata = load_magnetic(source, ProtocolConfig())
    assert metadata["source_header"][4] == "lon_gsm"
    assert metadata["source_header"][6] == "bt"
    assert frame.loc[0, "B_provider_nT"] == 5.0
    assert frame.loc[0, "B_vector_nT"] == 5.0
    assert frame.loc[0, "lon_gsm"] == 299.0


def test_warmup_rows_have_no_chi():
    frame = magnetic_frame("2026-01-01", periods=24 * 60)
    out = compute_frozen_baseline(frame, ProtocolConfig())
    assert out["baseline_valid"].sum() == 0
    assert out["chi_B24M"].isna().all()
    assert set(out["baseline_status"]) == {"WARMUP_LT_24H"}


def test_baseline_is_trailing_and_excludes_current_sample():
    frame = magnetic_frame("2026-01-01", periods=24 * 60 + 2)
    # The first post-warmup point jumps from 10 to 20 nT.
    jump_index = 24 * 60
    frame.loc[jump_index, ["bx_gsm", "B_vector_nT", "B_provider_nT", "bt"]] = 20.0

    out = compute_frozen_baseline(frame, ProtocolConfig())
    row = out.iloc[jump_index]
    assert bool(row["baseline_valid"])
    assert row["B0_trailing_24h_median_nT"] == 10.0
    assert row["chi_B24M"] == 1.0


def test_no_chi_clipping():
    frame = magnetic_frame("2026-01-01", periods=24 * 60 + 2)
    jump_index = 24 * 60
    frame.loc[jump_index, ["bx_gsm", "B_vector_nT", "B_provider_nT", "bt"]] = 30.0

    out = compute_frozen_baseline(frame, ProtocolConfig())
    assert out.iloc[jump_index]["chi_B24M"] == 2.0
    assert out.iloc[jump_index]["chi_status"] == "ABOVE_BAND"


def test_coverage_gate_rejects_incomplete_prior_window():
    frame = magnetic_frame("2026-01-01", periods=26 * 60)
    # Remove two hours from the prior 24-hour window. A 95% gate requires
    # at least 1,368 of 1,440 expected samples, so this must fail.
    frame = frame.drop(index=range(6 * 60, 8 * 60)).reset_index(drop=True)
    out = compute_frozen_baseline(frame, ProtocolConfig())
    final = out.iloc[-1]
    assert not bool(final["baseline_valid"])
    assert final["baseline_status"] == "INSUFFICIENT_COVERAGE"


def test_bt_vector_qc_accepts_rounded_noaa_components(tmp_path: Path):
    rows = [
        ["time_tag", "bx_gsm", "by_gsm", "bz_gsm", "lon_gsm", "lat_gsm", "bt"],
        ["2026-01-01 00:00:00.000", "5.08", "-2.03", "3.40", "338.26", "31.90", "6.44"],
    ]
    source = tmp_path / "mag.json"
    source.write_text(json.dumps(rows), encoding="utf-8")
    frame, _ = load_magnetic(source, ProtocolConfig())
    assert bool(frame.loc[0, "bt_qc_pass"])
    assert frame.loc[0, "bt_abs_error_nT"] < 0.02


def test_kinetic_split_is_independent_of_chi():
    config = ProtocolConfig()
    magnetic = magnetic_frame("2026-01-01", periods=181)
    magnetic["baseline_valid"] = False
    magnetic["chi_B24M"] = np.nan
    magnetic["baseline_status"] = "WARMUP_LT_24H"
    magnetic["chi_status"] = "WARMUP_OR_GAP"
    magnetic["above_theoretical_0p15"] = False
    magnetic["baseline_sample_count"] = 0
    magnetic["baseline_coverage_fraction"] = 0.0
    magnetic["B0_trailing_24h_median_nT"] = np.nan
    magnetic["history_age_seconds"] = np.arange(181) * 60

    plasma = pd.DataFrame(
        {
            "time_tag": magnetic["time_tag"],
            "density": np.full(181, 5.0),
            "speed": np.full(181, 400.0),
            "temperature": np.full(181, 100000.0),
        }
    )
    # At minute 120, speed is 100 km/s above the value one hour earlier.
    plasma.loc[120, "speed"] = 500.0

    joined = merge_plasma_and_classify(magnetic, plasma, config)
    assert joined.loc[120, "speed_jump_1h_km_s"] == 100.0
    assert joined.loc[120, "kinetic_regime"] == "TRANSIENT_KINETIC"
    assert pd.isna(joined.loc[120, "chi_B24M"])


def test_boundary_band_is_not_a_cap():
    frame = magnetic_frame("2026-01-01", periods=24 * 60 + 4)
    start = 24 * 60
    for offset, value in enumerate([11.49, 11.50, 11.55, 12.00]):
        idx = start + offset
        frame.loc[idx, ["bx_gsm", "B_vector_nT", "B_provider_nT", "bt"]] = value

    out = compute_frozen_baseline(frame, ProtocolConfig())
    assert out.iloc[start]["chi_status"] == "AT_BOUNDARY"
    assert out.iloc[start + 1]["chi_status"] == "AT_BOUNDARY"
    assert out.iloc[start + 2]["chi_status"] == "AT_BOUNDARY"
    assert out.iloc[start + 3]["chi_status"] == "ABOVE_BAND"
    assert out.iloc[start + 3]["chi_B24M"] == 0.2


def test_historical_gse_columns_are_accepted_without_relabeling(tmp_path: Path):
    rows = [
        ["time_tag", "bx_gse", "by_gse", "bz_gse"],
        ["2024-05-10 00:00:00.000", "3", "4", "0"],
    ]
    source = tmp_path / "mag_gse.json"
    source.write_text(json.dumps(rows), encoding="utf-8")

    frame, metadata = load_magnetic(source, ProtocolConfig())
    assert metadata["coordinate_frame"] == "GSE"
    assert metadata["field_mapping"]["bx"] == "bx_gse"
    assert frame.loc[0, "coordinate_frame"] == "GSE"
    assert frame.loc[0, "B_vector_nT"] == 5.0
    assert "bx_gsm" not in frame.columns


def test_multiple_coordinate_frames_are_rejected(tmp_path: Path):
    rows = [
        ["time_tag", "bx_gsm", "by_gsm", "bz_gsm", "bx_gse", "by_gse", "bz_gse"],
        ["2024-05-10 00:00:00.000", "3", "4", "0", "3", "4", "0"],
    ]
    source = tmp_path / "ambiguous_mag.json"
    source.write_text(json.dumps(rows), encoding="utf-8")

    import pytest
    from cline_l1_chain_v1 import DataContractError

    with pytest.raises(DataContractError, match="multiple complete magnetic coordinate frames"):
        load_magnetic(source, ProtocolConfig())
