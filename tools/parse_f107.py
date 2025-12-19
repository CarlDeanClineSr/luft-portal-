#!/usr/bin/env python3
"""
Parse daily F10.7 cm solar radio flux into CSV + latest MD card.
Handles both formats:
- YYYYMMDD OBS ADJ ...
- YYYY MM DD OBS ADJ ...
Deps: pandas, requests
"""
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd
import requests

URL = "https://services.swpc.noaa.gov/text/solar_radio_flux.txt"
OUT_CSV = Path("data/noaa_parsed/solar_radio_flux.csv")
OUT_MD = Path("reports/latest_f107.md")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)


def parse_lines(text: str) -> pd.DataFrame:
    records = []
    for ln in text.splitlines():
        if not ln or not ln[0].isdigit():
            continue
        toks = ln.split()
        # Format 1: YYYYMMDD OBS ADJ ...
        if len(toks) >= 3 and len(toks[0]) == 8 and toks[0].isdigit():
            yyyymmdd = toks[0]
            obs = toks[1]
            adj = toks[2]
        # Format 2: YYYY MM DD OBS ADJ ...
        elif len(toks) >= 5 and len(toks[0]) == 4 and toks[0].isdigit():
            year, month, day = toks[0], toks[1], toks[2]
            if month.isdigit() and day.isdigit():
                yyyymmdd = f"{year}{month.zfill(2)}{day.zfill(2)}"
                obs = toks[3]
                adj = toks[4]
            else:
                continue
        else:
            continue
        try:
            obs_f = float(obs)
            adj_f = float(adj)
        except Exception:
            continue
        records.append({"yyyymmdd": yyyymmdd, "obs_flux": obs_f, "adj_flux": adj_f})
    if not records:
        return pd.DataFrame(columns=["yyyymmdd", "obs_flux", "adj_flux"])
    return pd.DataFrame(records)


def fetch_df() -> pd.DataFrame:
    try:
        r = requests.get(URL, timeout=30)
        r.raise_for_status()
    except Exception as exc:
        print(f"WARNING: F10.7 fetch failed: {exc}")
        sys.exit(0)

    df = parse_lines(r.text)
    if df.empty:
        print("WARNING: No numeric data rows in F10.7 feed; skipping.")
        sys.exit(0)

    df["date"] = pd.to_datetime(df["yyyymmdd"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"])
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
        df_all = (
            pd.concat([old, df], ignore_index=True)
            .drop_duplicates(subset=["date"], keep="last")
            .sort_values("date")
        )
    else:
        df_all = df.sort_values("date")
    df_all.to_csv(OUT_CSV, index=False)
    latest = df_all.iloc[-1]
    write_md(latest)
    print(f"Rows total: {len(df_all)}, latest date: {latest['date']:%Y-%m-%d}")


if __name__ == "__main__":
    main()
