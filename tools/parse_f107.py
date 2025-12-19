#!/usr/bin/env python3
"""
Parse daily F10.7 cm solar radio flux into CSV + latest MD card.
Deps: pandas, requests
"""

from datetime import datetime, timezone
from pathlib import Path
import io

import pandas as pd
import requests

URL = "https://services.swpc.noaa.gov/text/solar_radio_flux.txt"
OUT_CSV = Path("data/noaa_parsed/solar_radio_flux.csv")
OUT_MD = Path("reports/latest_f107.md")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)

def fetch_df() -> pd.DataFrame:
    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    # Keep only lines that begin with a digit (data rows), skip metadata like ":Product:"
    data_lines = [ln for ln in r.text.splitlines() if ln and ln[0].isdigit()]
    if not data_lines:
        raise ValueError("No data rows found in solar_radio_flux feed.")

    buf = io.StringIO("\n".join(data_lines))
    df = pd.read_csv(
        buf,
        sep=r"\s+",
        comment="#",
        header=None,
        names=["yyyymmdd", "obs_flux", "adj_flux"],
        usecols=[0, 1, 2],
    )
    df["date"] = pd.to_datetime(df["yyyymmdd"], format="%Y%m%d")
    df["fetched_utc"] = datetime.now(timezone.utc).isoformat()
    return df[["date", "obs_flux", "adj_flux", "fetched_utc"]]

def write_md(latest: pd.Series) -> None:
    lines = [
        "# F10.7 Daily Flux (latest)",
        f"Fetched: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}",
        "",
        f"- Date: {latest['date']:%Y-%m-%d}",
        f"- Observed: {latest['obs_flux']} sfu",
        f"- Adjusted: {latest['adj_flux']} sfu",
    ]
    OUT_MD.write_text("\n".join(lines))

def main():
    df = fetch_df()
    if OUT_CSV.exists():
        old = pd.read_csv(OUT_CSV, parse_dates=["date"])
        df_all = pd.concat([old, df], ignore_index=True).drop_duplicates(subset=["date"], keep="last")
    else:
        df_all = df
    df_all.sort_values("date").to_csv(OUT_CSV, index=False)
    latest = df_all.sort_values("date").iloc[-1]
    write_md(latest)
    print(f"Rows total: {len(df_all)}, latest date: {latest['date']:%Y-%m-%d}")

if __name__ == "__main__":
    main()
