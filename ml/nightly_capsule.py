#!/usr/bin/env python3
"""
Generate a nightly capsule summary:
- Load latest rebound fit JSON and events CSV
- Summarize coefficients, event count, alerts
- Write reports/daily_capsule.md
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

RESULTS_DIR = Path("results")
REPORTS_DIR = Path("reports")
ALERTS_DIR = Path("alerts")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def latest_file(pattern):
    files = sorted(Path(".").glob(pattern))
    return files[-1] if files else None

def main():
    fit_file = latest_file("results/rebound_fit_*_fit.json")
    events_file = latest_file("results/rebound_fit_*_events.csv")
    alert_log = ALERTS_DIR / "alert_log.csv"

    coeffs = {}
    if fit_file:
        with open(fit_file) as f:
            coeffs = json.load(f).get("coefficients", [])

    events_count = 0
    if events_file:
        df = pd.read_csv(events_file)
        events_count = len(df)

    alerts = []
    if alert_log.exists():
        alerts = pd.read_csv(alert_log, header=None).tail(5).to_string(index=False)

    capsule_path = REPORTS_DIR / "daily_capsule.md"
    with open(capsule_path, "w") as f:
        f.write(f"# Nightly Capsule\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"Events processed: {events_count}\n\n")
        f.write(f"Coefficients: {coeffs}\n\n")
        f.write("Recent alerts:\n")
        f.write(f"{alerts}\n")
    print(f"[OK] Wrote nightly capsule: {capsule_path}")

if __name__ == "__main__":
    main()
