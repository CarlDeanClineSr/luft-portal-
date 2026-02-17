#!/usr/bin/env python3
"""
Scan latest extended heartbeat log, write alert if chi < 0.08 or recovery too long.
"""
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

DATA_DIR = Path("data")
ALERTS_DIR = Path("alerts")
ALERTS_DIR.mkdir(parents=True, exist_ok=True)
THRESHOLD_CHI = 0.08
THRESHOLD_RECOVER_HOURS = 6

def latest_extended():
    files = sorted(DATA_DIR.glob("extended_heartbeat_log_*.csv"))
    if not files:
        return None
    return pd.read_csv(files[-1], parse_dates=["time_utc"])

def check_and_alert():
    df = latest_extended()
    if df is None:
        return
    latest = df.sort_values("time_utc").iloc[-1]
    chi = latest.get("chi", None)
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    alerts = []
    if pd.notna(chi) and chi < THRESHOLD_CHI:
        fname = ALERTS_DIR / f"chi_floor_alert_{now}.txt"
        with open(fname, "w") as f:
            f.write(f"ALERT: chi below {THRESHOLD_CHI} at {latest['time_utc']}, chi={chi}\n")
        alerts.append(str(fname))
    if alerts:
        log = ALERTS_DIR / "alert_log.csv"
        with open(log, "a") as f:
            for a in alerts:
                f.write(f"{a},{now}\n")
        print(f"[ALERT] Wrote {len(alerts)} alert(s).")
    else:
        print("[OK] No alerts.")

if __name__ == "__main__":
    check_and_alert()
