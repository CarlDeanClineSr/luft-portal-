from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from physical_transition_analysis import (
    add_derived_metrics,
    compute_alfven_speed_kms,
    compute_dynamic_pressure_npa,
    compute_proton_beta,
    estimate_spectral_slope,
    rank_correlation,
    resolve_columns,
    run_analysis,
)


def test_derived_plasma_metrics_are_finite_and_positive():
    b = pd.Series([5.0, 10.0])
    density = pd.Series([5.0, 5.0])
    temperature = pd.Series([1.0e5, 1.0e5])
    speed = pd.Series([400.0, 500.0])

    beta = compute_proton_beta(b, density, temperature)
    pdyn = compute_dynamic_pressure_npa(density, speed)
    va = compute_alfven_speed_kms(b, density)

    assert np.isfinite(beta).all()
    assert np.isfinite(pdyn).all()
    assert np.isfinite(va).all()
    assert (beta > 0).all()
    assert (pdyn > 0).all()
    assert (va > 0).all()
    assert beta.iloc[0] > beta.iloc[1]  # beta scales as 1/B^2
    assert pdyn.iloc[1] > pdyn.iloc[0]


def test_rank_correlation_detects_monotonic_relation():
    x = pd.Series([5.0, 1.0, 3.0, 2.0, 4.0])
    y = 7.0 * x + 2.0
    rho, n = rank_correlation(x, y)
    assert n == 5
    assert np.isclose(rho, 1.0)


def test_column_resolver_requires_canonical_chi_not_generic_chi():
    df = pd.DataFrame(
        {
            "chi": [0.1],
            "B_vector_nT": [5.0],
            "density_p_cm3": [4.0],
            "speed_km_s": [400.0],
            "temperature_K": [1.0e5],
        }
    )
    try:
        resolve_columns(df)
    except KeyError as exc:
        assert "chi" in str(exc)
    else:
        raise AssertionError("Generic legacy chi column must not be accepted")


def test_add_derived_metrics_preserves_unclipped_chi():
    df = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2026-01-01", periods=3, freq="min", tz="UTC"),
            "chi_B24M": [0.05, 1.25, 2.75],
            "B_vector_nT": [5.0, 6.0, 7.0],
            "density_p_cm3": [4.0, 5.0, 6.0],
            "speed_km_s": [390.0, 450.0, 620.0],
            "temperature_K": [8.0e4, 1.0e5, 2.0e5],
        }
    )
    columns = resolve_columns(df)
    out = add_derived_metrics(df, columns)
    assert out["chi_B24M"].tolist() == [0.05, 1.25, 2.75]
    assert out["chi_B24M"].max() == 2.75
    assert np.isfinite(out["proton_beta"]).all()
    assert np.isfinite(out["alfven_mach"]).all()


def test_spectral_slope_returns_finite_value_for_regular_signal():
    rng = np.random.default_rng(7)
    n = 4096
    t = np.arange(n) * 60.0
    signal = np.sin(2.0 * np.pi * t / 1800.0) + 0.15 * rng.normal(size=n)
    result = estimate_spectral_slope(signal, cadence_seconds=60.0)
    assert result["n"] == n
    assert result["finite_fraction"] == 1.0
    assert np.isfinite(result["slope"])


def test_full_analysis_writes_provenance_and_does_not_clip(tmp_path: Path):
    n = 240
    ts = pd.date_range("2026-01-01", periods=n, freq="min", tz="UTC")
    chi = np.linspace(0.01, 2.0, n)
    frame = pd.DataFrame(
        {
            "timestamp_utc": ts,
            "chi_B24M": chi,
            "B_vector_nT": 6.0 + 0.4 * np.sin(np.arange(n) / 11.0),
            "density_p_cm3": 5.0 + 0.5 * np.cos(np.arange(n) / 13.0),
            "speed_km_s": 410.0 + 20.0 * np.sin(np.arange(n) / 17.0),
            "temperature_K": 1.2e5 + 1.0e4 * np.cos(np.arange(n) / 19.0),
            "kinetic_regime": ["STEADY"] * 180 + ["TRANSIENT"] * 60,
        }
    )
    input_path = tmp_path / "canonical.csv"
    output_dir = tmp_path / "out"
    frame.to_csv(input_path, index=False)

    manifest = run_analysis(input_path, output_dir)
    assert manifest["analysis_protocol"] == "CLINE-L1-B24M-TRAIL-v1"
    assert manifest["transition_analysis_version"] == "CLINE-L1-TRANSITIONS-v1"
    assert manifest["chi_clipped"] is False
    assert np.isclose(manifest["chi_input_max"], 2.0)
    assert np.isclose(manifest["chi_output_max"], 2.0)

    derived = pd.read_csv(output_dir / "derived_transition_metrics.csv")
    assert np.isclose(derived["chi_B24M"].max(), 2.0)
    assert (output_dir / "chi_by_beta_band.csv").exists()
    assert (output_dir / "chi_rank_correlations.csv").exists()
    assert (output_dir / "chi_by_kinetic_regime.csv").exists()
    spectral = json.loads((output_dir / "spectral_slopes.json").read_text())
    assert spectral["cadence_seconds"] == 60.0
