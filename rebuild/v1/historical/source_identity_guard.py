#!/usr/bin/env python3
"""Fail-closed source identity checks for canonical DSCOVR L1 magnetic files.

This guard is deliberately independent of chi.  It verifies that a historical
magnetic input has the expected DSCOVR/CDAWeb provenance, one truthful vector
coordinate frame, and field magnitudes compatible with an L1 solar-wind
analysis.  Terrestrial total-field layouts such as ``time,F,B,baseline,chi``
are rejected before the CLINE baseline or any plasma physics is calculated.

The 1000 nT ceiling is an engineering quarantine threshold, not a proposed
physical boundary.  Crossing it stops automation and requires manual source
review; it never clips or alters data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXPECTED_MAGNETIC_DATASET = "DSCOVR_H0_MAG"
EXPECTED_INGEST_PROTOCOL = "CDAWEB-DSCOVR-RESTCSV-1M-v1"
EXPECTED_FRAMES = {"GSE"}
L1_REVIEW_CEILING_NT = 1000.0


class SourceIdentityError(ValueError):
    """Raised when a file cannot be identified as the frozen DSCOVR L1 source."""


def _unique_nonempty(frame: pd.DataFrame, column: str) -> set[str]:
    if column not in frame.columns:
        return set()
    return {
        str(value).strip()
        for value in frame[column].dropna().unique().tolist()
        if str(value).strip()
    }


def validate_dscovr_l1_magnetic_frame(
    frame: pd.DataFrame,
    *,
    expected_dataset: str = EXPECTED_MAGNETIC_DATASET,
    expected_ingest_protocol: str = EXPECTED_INGEST_PROTOCOL,
    review_ceiling_nT: float = L1_REVIEW_CEILING_NT,
) -> dict[str, Any]:
    """Validate canonical DSCOVR magnetic provenance and return an audit record."""
    if frame.empty:
        raise SourceIdentityError("magnetic source is empty")

    columns = {str(column) for column in frame.columns}

    # A total-field F column is a terrestrial-magnetometer signature in this
    # project.  Generic B/baseline/chi output is likewise not a canonical L1
    # magnetic source and must not enter the rebuilt chain.
    if "F" in columns or {"F", "B"}.issubset(columns):
        raise SourceIdentityError(
            "terrestrial total-field layout detected (column F); refusing DSCOVR L1 analysis"
        )
    if {"B", "baseline", "chi"}.issubset(columns):
        raise SourceIdentityError(
            "generic derived magnetic layout detected; canonical vector telemetry is required"
        )
    if "chi" in columns and "chi_B24M" not in columns:
        raise SourceIdentityError(
            "generic chi column detected; it cannot establish CLINE-L1-B24M-TRAIL-v1 provenance"
        )

    vector_contracts = {
        "GSE": ("bx_gse", "by_gse", "bz_gse"),
        "GSM": ("bx_gsm", "by_gsm", "bz_gsm"),
    }
    complete = [
        (coordinate_frame, component_columns)
        for coordinate_frame, component_columns in vector_contracts.items()
        if all(column in frame.columns for column in component_columns)
    ]
    if len(complete) != 1:
        raise SourceIdentityError(
            "expected exactly one complete GSE or GSM vector set; "
            f"found {len(complete)} in columns {list(frame.columns)}"
        )

    coordinate_frame, component_columns = complete[0]
    bx, by, bz = (
        pd.to_numeric(frame[column], errors="coerce")
        for column in component_columns
    )
    magnitude = np.sqrt(bx**2 + by**2 + bz**2)
    finite = pd.Series(magnitude).replace([np.inf, -np.inf], np.nan).dropna()
    finite = finite.loc[finite >= 0]
    if finite.empty:
        raise SourceIdentityError("no finite magnetic vector magnitudes remain")

    maximum = float(finite.max())
    median = float(finite.median())
    p99 = float(finite.quantile(0.99))
    if maximum > review_ceiling_nT:
        raise SourceIdentityError(
            "magnetic magnitude exceeds the L1 source-review ceiling: "
            f"max={maximum:.6g} nT > {review_ceiling_nT:.6g} nT. "
            "Possible terrestrial or wrong-instrument input; no values were altered."
        )

    datasets = _unique_nonempty(frame, "source_dataset")
    if datasets != {expected_dataset}:
        raise SourceIdentityError(
            f"source_dataset must be exactly {expected_dataset!r}; found {sorted(datasets)!r}"
        )

    protocols = _unique_nonempty(frame, "ingest_protocol")
    if protocols != {expected_ingest_protocol}:
        raise SourceIdentityError(
            "ingest_protocol mismatch: "
            f"expected {expected_ingest_protocol!r}, found {sorted(protocols)!r}"
        )

    declared_frames = _unique_nonempty(frame, "coordinate_frame")
    if declared_frames != {coordinate_frame}:
        raise SourceIdentityError(
            f"coordinate frame declaration mismatch: vectors={coordinate_frame}, "
            f"declared={sorted(declared_frames)!r}"
        )
    if coordinate_frame not in EXPECTED_FRAMES:
        raise SourceIdentityError(
            f"historical V1 expects frame in {sorted(EXPECTED_FRAMES)!r}; found {coordinate_frame!r}"
        )

    return {
        "verdict": "PASS",
        "expected_dataset": expected_dataset,
        "source_dataset_values": sorted(datasets),
        "expected_ingest_protocol": expected_ingest_protocol,
        "ingest_protocol_values": sorted(protocols),
        "coordinate_frame": coordinate_frame,
        "component_columns": list(component_columns),
        "rows": int(len(frame)),
        "finite_magnitude_rows": int(len(finite)),
        "B_vector_median_nT": median,
        "B_vector_p99_nT": p99,
        "B_vector_max_nT": maximum,
        "review_ceiling_nT": float(review_ceiling_nT),
        "chi_used_for_identity": False,
        "data_clipped": False,
    }


def validate_dscovr_l1_magnetic_file(
    path: str | Path,
    *,
    review_ceiling_nT: float = L1_REVIEW_CEILING_NT,
) -> dict[str, Any]:
    source_path = Path(path)
    frame = pd.read_csv(source_path, low_memory=False)
    report = validate_dscovr_l1_magnetic_frame(
        frame,
        review_ceiling_nT=review_ceiling_nT,
    )
    report["path"] = str(source_path)
    return report
