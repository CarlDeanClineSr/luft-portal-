#!/usr/bin/env python3
"""
Lightweight validator for GOES capsules.

Usage:
  python scripts/capsule_validator.py path/to/capsule.md

Checks for:
- File existence
- Required lines: title, Generated, Time, Satellite, Band, Observed flux
Exits 0 on success; >0 on validation failure.
"""
from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_KEYS = ["# GOES X-ray Flux Capsule", "Generated:", "Time:", "Satellite:", "Band:", "Observed flux:"]


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/capsule_validator.py path/to/capsule.md")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Validation failed: file not found: {path}")
        sys.exit(2)

    text = path.read_text()
    for key in REQUIRED_KEYS:
        if key not in text:
            print(f"Validation failed: missing '{key}'")
            sys.exit(3)

    print("Capsule validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
