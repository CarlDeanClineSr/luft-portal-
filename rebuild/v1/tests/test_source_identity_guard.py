from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cline_l1_chain_v1 import ProtocolConfig, compute_frozen_baseline
from historical.source_identity_guard import (
    SourceIdentityError,
    validate_dscovr_l1_magnetic_frame,
)


def canonical_dscovr_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_tag": pd.date_range("2024-05-09", periods=4, freq="min", tz="UTC"),
            "bx_gse": [3.0, 3.1, 3.2, 3.3],
            "by_gse": [4.0, 4.0, 4.1, 4.2],
            "bz_gse": [0.0, -0.2, -0.3, -0.4],
            "source_dataset": ["DSCOVR_H0_MAG"] * 4,
            "coordinate_frame": ["GSE"] * 4,
            "ingest_protocol": ["CDAWEB-DSCOVR-RESTCSV-1M-v1"] * 4,
        }
    )


def test_source_identity_accepts_canonical_dscovr_l1_vector():
    report = validate_dscovr_l1_magnetic_frame(canonical_dscovr_frame())
    assert report["verdict"] == "PASS"
    assert report["coordinate_frame"] == "GSE"
    assert report["B_vector_max_nT"] < 10.0
    assert report["chi_used_for_identity"] is False
    assert report["data_clipped"] is False


def test_source_identity_rejects_terrestrial_total_field_layout():
    ground = pd.DataFrame(
        {
            "time": ["2024-05-10T00:00:00Z", "2024-05-10T00:01:00Z"],
            "F": [51312.699, 51312.644],
            "B": [51312.699, 51312.644],
            "baseline": [51315.388, 51315.382],
            "chi": [5.24e-5, 5.34e-5],
        }
    )
    with pytest.raises(SourceIdentityError, match="terrestrial total-field"):
        validate_dscovr_l1_magnetic_frame(ground)


def test_source_identity_quarantines_implausibly_large_l1_vector_without_clipping():
    wrong_scale = canonical_dscovr_frame()
    wrong_scale[["bx_gse", "by_gse", "bz_gse"]] *= 10000.0
    original_max = np.sqrt(
        wrong_scale["bx_gse"] ** 2
        + wrong_scale["by_gse"] ** 2
        + wrong_scale["bz_gse"] ** 2
    ).max()
    with pytest.raises(SourceIdentityError, match="source-review ceiling"):
        validate_dscovr_l1_magnetic_frame(wrong_scale)
    after_max = np.sqrt(
        wrong_scale["bx_gse"] ** 2
        + wrong_scale["by_gse"] ** 2
        + wrong_scale["bz_gse"] ** 2
    ).max()
    assert after_max == original_max


def test_source_identity_rejects_wrong_dataset_even_at_solar_wind_scale():
    wrong_source = canonical_dscovr_frame()
    wrong_source["source_dataset"] = "GROUND_MAGNETOMETER"
    with pytest.raises(SourceIdentityError, match="source_dataset"):
        validate_dscovr_l1_magnetic_frame(wrong_source)


def test_frozen_chain_names_output_chi_b24m_not_generic_chi():
    config = ProtocolConfig(minimum_coverage_fraction=0.95)
    times = pd.date_range("2024-05-01", periods=1500, freq="min", tz="UTC")
    magnetic = pd.DataFrame(
        {
            "time_tag": times,
            "B_vector_nT": np.full(len(times), 5.0),
        }
    )
    result = compute_frozen_baseline(magnetic, config)
    assert "chi_B24M" in result.columns
    assert "chi" not in result.columns


def test_epoch_manifest_exposes_canonical_gannon_run_name():
    config_path = Path(__file__).resolve().parents[1] / "historical" / "epochs.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert "gannon_may_2024_dscovr_mag_only" in config["runs"]
    assert config["runs"]["gannon_may_2024_dscovr_mag_only"]["kind"] == "magnetic_only"
