#!/usr/bin/env python3
"""Orchestrate fixed-storm and data-selected quiet DSCOVR runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(ROOT))

from cline_l1_chain_v1 import run_chain
from historical.download_dscovr_cdaweb import (
    download_interval,
    download_magnetic_interval,
    download_plasma_interval,
    iso_utc,
    parse_utc,
)
from historical.select_quiet_window import select_quiet_window
from historical.source_identity_guard import validate_dscovr_l1_magnetic_file


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _write_augmented_download_manifest(
    download_root: Path,
    manifest: dict[str, Any],
    source_identity: dict[str, Any],
) -> Path:
    """Persist the identity-gate result next to the download provenance."""
    manifest["source_identity_guard"] = source_identity
    manifest_path = download_root / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def run_fixed(name: str, spec: dict[str, Any], root: Path, warmup: int) -> dict:
    run_root = root / name
    download_root = run_root / "download"
    manifest = download_interval(
        spec["analysis_start"],
        spec["analysis_end"],
        download_root,
        baseline_warmup_hours=warmup,
    )
    magnetic_path = manifest["canonical_files"]["magnetic"]
    source_identity = validate_dscovr_l1_magnetic_file(magnetic_path)
    manifest_path = _write_augmented_download_manifest(
        download_root, manifest, source_identity
    )

    analysis_root = run_root / "analysis"
    _, summary = run_chain(
        magnetic_path=magnetic_path,
        plasma_path=manifest["canonical_files"]["plasma"],
        output_dir=analysis_root,
        label=name,
    )
    return {
        "name": name,
        "kind": "fixed",
        "download_manifest": str(manifest_path),
        "source_identity_guard": source_identity,
        "analysis_summary": str(analysis_root / "cline_l1_summary.json"),
        "result": summary["results"]["all_baseline_valid"],
    }


def run_magnetic_only(name: str, spec: dict[str, Any], root: Path, warmup: int) -> dict:
    """Run canonical magnetic chi without pretending a kinetic split exists."""
    run_root = root / name
    download_root = run_root / "download"
    analysis_start = parse_utc(spec["analysis_start"])
    analysis_end = parse_utc(spec["analysis_end"])
    retrieval_start = analysis_start - pd.Timedelta(hours=warmup)
    mag_path, mag_summary = download_magnetic_interval(
        retrieval_start, analysis_end, download_root
    )
    source_identity = validate_dscovr_l1_magnetic_file(mag_path)
    download_manifest = {
        "analysis_start": iso_utc(analysis_start),
        "analysis_end": iso_utc(analysis_end),
        "retrieval_start": iso_utc(retrieval_start),
        "baseline_warmup_hours": warmup,
        "paired_plasma": False,
        "reason": spec.get("limitation"),
        "magnetic": mag_summary,
        "canonical_files": {"magnetic": str(mag_path), "plasma": None},
        "source_identity_guard": source_identity,
    }
    download_manifest_path = download_root / "download_manifest.json"
    download_manifest_path.write_text(
        json.dumps(download_manifest, indent=2), encoding="utf-8"
    )
    analysis_root = run_root / "analysis"
    _, summary = run_chain(
        magnetic_path=mag_path,
        plasma_path=None,
        output_dir=analysis_root,
        label=name,
    )
    return {
        "name": name,
        "kind": "magnetic_only",
        "download_manifest": str(download_manifest_path),
        "source_identity_guard": source_identity,
        "analysis_summary": str(analysis_root / "cline_l1_summary.json"),
        "kinetic_interpretation": "UNAVAILABLE_NO_PAIRED_DEFINITIVE_DSCOVR_PLASMA",
        "result": summary["results"]["all_baseline_valid"],
    }


def run_quiet_scan(name: str, spec: dict[str, Any], root: Path, warmup: int) -> dict:
    run_root = root / name
    scan_download = run_root / "candidate_plasma"
    plasma_path, plasma_manifest = download_plasma_interval(
        spec["candidate_start"],
        spec["candidate_end"],
        scan_download,
    )
    selection = select_quiet_window(
        plasma_path,
        run_root / "selection",
        window_days=int(spec.get("window_days", 30)),
        stride_days=int(spec.get("stride_days", 1)),
        minimum_coverage_fraction=float(
            spec.get("minimum_coverage_fraction", 0.95)
        ),
    )
    selected = selection["selected"]
    download_root = run_root / "selected_download"
    manifest = download_interval(
        selected["start_utc"],
        selected["end_utc"],
        download_root,
        baseline_warmup_hours=warmup,
    )
    magnetic_path = manifest["canonical_files"]["magnetic"]
    source_identity = validate_dscovr_l1_magnetic_file(magnetic_path)
    manifest_path = _write_augmented_download_manifest(
        download_root, manifest, source_identity
    )

    analysis_root = run_root / "analysis"
    _, summary = run_chain(
        magnetic_path=magnetic_path,
        plasma_path=manifest["canonical_files"]["plasma"],
        output_dir=analysis_root,
        label=name,
    )
    return {
        "name": name,
        "kind": "quiet_scan",
        "selection": selection,
        "candidate_plasma_manifest": plasma_manifest,
        "download_manifest": str(manifest_path),
        "source_identity_guard": source_identity,
        "analysis_summary": str(analysis_root / "cline_l1_summary.json"),
        "result": summary["results"]["all_baseline_valid"],
    }


def run_named(config_path: str | Path, name: str, output_root: str | Path) -> dict:
    config = load_config(config_path)
    spec = config.get("runs", {}).get(name)
    if not spec:
        available = sorted((config.get("runs") or {}).keys())
        raise KeyError(f"run {name!r} is not defined; available runs: {available}")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    warmup = int(config.get("baseline_warmup_hours", 24))
    if spec.get("kind") == "fixed":
        result = run_fixed(name, spec, root, warmup)
    elif spec.get("kind") == "magnetic_only":
        result = run_magnetic_only(name, spec, root, warmup)
    elif spec.get("kind") == "quiet_scan":
        result = run_quiet_scan(name, spec, root, warmup)
    else:
        raise ValueError(f"unsupported run kind: {spec.get('kind')!r}")
    result_path = root / name / "batch_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).with_name("epochs.yaml")))
    parser.add_argument("--run", required=True)
    parser.add_argument("--outdir", default="runs/historical")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_named(args.config, args.run, args.outdir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
