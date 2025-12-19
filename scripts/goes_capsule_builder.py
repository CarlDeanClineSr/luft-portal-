#!/usr/bin/env python3
"""
Build a GOES X-ray flux capsule from the SWPC JSON product.

Usage:
  python scripts/goes_capsule_builder.py input_json output_md

Behavior:
- Reads the SWPC GOES X-ray flux JSON (table-style: first row is header).
- Takes the latest row, renders a small markdown capsule.
- Fails soft if the file is missing or has no data.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


def load_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"WARNING: input JSON not found: {path}")
        return []
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        print(f"WARNING: failed to parse JSON {path}: {exc}")
        return []
    if not isinstance(data, list) or len(data) < 2:
        print(f"WARNING: JSON shape unexpected (need header + rows), len={len(data)}")
        return []
    header = data[0]
    rows = data[1:]
    out = []
    for row in rows:
        if not isinstance(row, list):
            continue
        rec = {header[i]: row[i] for i in range(min(len(header), len(row)))}
        out.append(rec)
    return out


def render_capsule(latest: Dict[str, Any]) -> str:
    ts = latest.get("time_tag") or latest.get("time") or "unknown"
    flux = latest.get("observed_flux") or latest.get("flux") or latest.get("x_ray_flux") or "unknown"
    sat = latest.get("satellite") or latest.get("sat") or "GOES"
    energy = latest.get("energy") or latest.get("energy_range") or latest.get("wavelength") or "0.1–0.8 nm"

    lines = [
        "# GOES X-ray Flux Capsule",
        f"Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC",
        "",
        f"- Time: {ts}",
        f"- Satellite: {sat}",
        f"- Band: {energy}",
        f"- Observed flux: {flux}",
    ]
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/goes_capsule_builder.py input_json output_md")
        sys.exit(0)

    input_json = Path(sys.argv[1])
    output_md = Path(sys.argv[2])
    output_md.parent.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_json)
    if not rows:
        print("WARNING: no rows to render; skipping capsule creation.")
        sys.exit(0)

    latest = rows[-1]
    capsule = render_capsule(latest)
    output_md.write_text(capsule)
    print(f"Wrote capsule: {output_md}")


if __name__ == "__main__":
    main()
