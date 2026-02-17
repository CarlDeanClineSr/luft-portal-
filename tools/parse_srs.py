 #!/usr/bin/env python3
"""
Parse NOAA Solar Region Summary into CSV + latest MD summary.
Deps: pandas, requests
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

# Primary URL and fallback endpoints
PRIMARY_URL = "https://services.swpc.noaa.gov/text/solar-region-summary.txt"
FALLBACK_URLS = [
    "https://www.swpc.noaa.gov/products/solar-region-summary",
]
OUT_CSV = Path("data/noaa_parsed/srs_daily.csv")
OUT_MD = Path("reports/latest_srs.md")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)

REGION_RE = re.compile(
    r"^(?P<num>\d{4,})\s+"
    r"(?P<loc>[NS]\d{2}[EW]\d{2,3})\s+"
    r"(?P<lo>\d+)\s+"
    r"(?P<area>\d+)\s+"
    r"(?P<z>\w+)\s+"
    r"(?P<ll>\d+)\s+"
    r"(?P<nn>\d+)\s+"
    r"(?P<mag>\w+)",
    re.MULTILINE,
)

def fetch_text() -> str:
    """
    Try primary URL first, then fallbacks. Exit gracefully if all fail.
    Returns the fetched text or exits with code 0 if all endpoints fail.
    """
    urls_to_try = [PRIMARY_URL] + FALLBACK_URLS

    for idx, url in enumerate(urls_to_try):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            if idx > 0:
                print(f"[INFO] Primary URL failed, succeeded with fallback: {url}")
            return r.text
        except requests.exceptions.RequestException as e:
            if idx < len(urls_to_try) - 1:
                print(f"[WARN] Failed to fetch from {url}: {e}. Trying next endpoint...")
            else:
                print(f"[WARN] All SRS endpoints failed. Last error from {url}: {e}")
                print("[WARN] Exiting gracefully - no data to parse.")
                sys.exit(0)

def parse_regions(txt: str) -> pd.DataFrame:
    rows = []
    for m in REGION_RE.finditer(txt):
        rows.append(m.groupdict())
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["lo"] = pd.to_numeric(df["lo"], errors="coerce")
    df["area"] = pd.to_numeric(df["area"], errors="coerce")
    df["ll"] = pd.to_numeric(df["ll"], errors="coerce")
    df["nn"] = pd.to_numeric(df["nn"], errors="coerce")
    df["fetched_utc"] = datetime.now(timezone.utc).isoformat()
    return df

def write_md(df: pd.DataFrame, raw: str) -> None:
    if df.empty:
        OUT_MD.write_text("# Solar Region Summary\nNo regions parsed.\n")
        return
    top = df.sort_values("area", ascending=False).head(5)
    lines = ["# Solar Region Summary (latest fetch)", ""]
    lines.append(f"Fetched: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    lines.append("")
    lines.append("## Top 5 by Area")
    lines.append("| Num | Loc | Area | Mag |")
    lines.append("|-----|-----|------|-----|")
    for _, r in top.iterrows():
        lines.append(f"| {r['num']} | {r['loc']} | {int(r['area'])} | {r['mag']} |")
    alerts = df[(df["mag"].str.contains("DEL", case=False)) | (df["mag"].str.contains("BGD", case=False))]
    lines.append("")
    lines.append("## Alerts")
    if alerts.empty:
        lines.append("- None (no Delta/Beta-Gamma-Delta regions).")
    else:
        for _, r in alerts.iterrows():
            lines.append(f"- Region {r['num']} ({r['mag']}) at {r['loc']} area {int(r['area'])}")
    lines.append("")
    lines.append("<details><summary>Raw excerpt</summary>")
    lines.append("")
    lines.append("```")
    lines.append(raw.strip()[:4000])
    lines.append("```")
    lines.append("</details>")
    OUT_MD.write_text("\n".join(lines))

def main():
    raw = fetch_text()
    df = parse_regions(raw)
    if not df.empty:
        if OUT_CSV.exists():
            old = pd.read_csv(OUT_CSV)
            df_all = pd.concat([old, df], ignore_index=True)
            df_all.to_csv(OUT_CSV, index=False)
        else:
            df.to_csv(OUT_CSV, index=False)
    write_md(df, raw)
    print(f"Parsed regions: {len(df)}")

if __name__ == "__main__":
    main() 
