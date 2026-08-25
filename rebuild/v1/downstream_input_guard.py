#!/usr/bin/env python3
"""Guard downstream LUFT analyses against silent legacy-χ reuse."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml

CANONICAL_COLUMN = "chi_B24M"
CANONICAL_PROTOCOL = "CLINE-L1-B24M-TRAIL-v1"
LEGACY_COLUMNS = ("legacy_composite_score_v1", "chi_amplitude", "chi_capped")


class LegacyInputError(ValueError):
    """Raised when a downstream calculation is pointed at an ambiguous input."""


def require_canonical_chi(
    frame: pd.DataFrame,
    *,
    column: str = CANONICAL_COLUMN,
    protocol_id: str | None = None,
) -> pd.Series:
    """Return a numeric canonical χ series or fail closed.

    This deliberately rejects a generic ``chi`` fallback. A caller must name the
    observable it intends to use.
    """
    if column == "chi":
        raise LegacyInputError("generic column 'chi' is forbidden; name the observable")
    if column not in frame.columns:
        present_legacy = [name for name in LEGACY_COLUMNS if name in frame.columns]
        detail = f"; legacy-like columns present: {present_legacy}" if present_legacy else ""
        raise LegacyInputError(
            f"required canonical column '{column}' is absent{detail}"
        )
    if protocol_id is not None and protocol_id != CANONICAL_PROTOCOL:
        raise LegacyInputError(
            f"protocol mismatch: expected {CANONICAL_PROTOCOL}, got {protocol_id}"
        )

    values = pd.to_numeric(frame[column], errors="coerce")
    if values.notna().sum() == 0:
        raise LegacyInputError(f"canonical column '{column}' has no numeric values")
    return values


def load_manifest(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def audit_manifest(repo_root: str | Path, manifest_path: str | Path) -> dict:
    root = Path(repo_root)
    manifest = load_manifest(manifest_path)
    records = []
    for module in manifest.get("modules", []):
        relative = Path(module["path"])
        path = root / relative
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        tokens = [token for token in ("chi_amplitude", "chi_capped", "calculate_chi") if token in text]
        records.append(
            {
                "path": str(relative),
                "exists": path.exists(),
                "status": module.get("status"),
                "legacy_tokens_found": tokens,
                "action": module.get("action"),
            }
        )
    return {
        "canonical_protocol": CANONICAL_PROTOCOL,
        "canonical_column": CANONICAL_COLUMN,
        "modules": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="Optional row CSV to validate")
    parser.add_argument("--column", default=CANONICAL_COLUMN)
    parser.add_argument("--protocol-id", default=CANONICAL_PROTOCOL)
    parser.add_argument("--manifest", default="DOWNSTREAM_RERUN_MANIFEST.yaml")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--report", help="Write a JSON manifest audit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.csv:
        frame = pd.read_csv(args.csv)
        values = require_canonical_chi(
            frame, column=args.column, protocol_id=args.protocol_id
        )
        print(f"canonical numeric rows: {values.notna().sum()}")

    report = audit_manifest(args.repo_root, args.manifest)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
