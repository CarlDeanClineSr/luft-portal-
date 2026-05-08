#!/usr/bin/env python3
"""
LUFT Daily Harvester - Runs in GitHub Actions
Scrapes all .csv, .md, .html, .json, .ipynb, .txt files + recent commit metadata.
Outputs: daily_manifest.json + summary.csv for Colab use.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
EXTENSIONS = {".csv", ".md", ".html", ".json", ".ipynb", ".txt", ".py"}
OUTPUT_DIR = ROOT / "daily_harvest"
OUTPUT_DIR.mkdir(exist_ok=True)

def get_recent_commits(days=1):
    """Get files changed in last N days (fast delta)."""
    try:
        cmd = f'git log --since="{days} day ago" --name-only --pretty=format: | sort -u'
        result = subprocess.check_output(cmd, shell=True, text=True)
        return [line.strip() for line in result.splitlines() if line.strip()]
    except Exception:
        return []

def process_file(file_path: Path):
    """Extract metadata without blowing up memory."""
    stats = {
        "path": str(file_path.relative_to(ROOT)),
        "size_bytes": file_path.stat().st_size,
        "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
        "extension": file_path.suffix.lower(),
    }

    if file_path.suffix.lower() == ".csv":
        try:
            # Stream read only header + row count (no full load)
            df = pd.read_csv(file_path, nrows=0)
            stats["columns"] = len(df.columns)
            # Count rows efficiently
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                stats["row_count"] = sum(1 for _ in f) - 1  # minus header
        except Exception as e:
            stats["error"] = str(e)
            stats["row_count"] = 0
    elif file_path.suffix.lower() in {".md", ".html", ".txt"}:
        try:
            stats["char_count"] = file_path.stat().st_size  # rough
        except:
            pass
    elif file_path.suffix.lower() == ".ipynb":
        stats["type"] = "notebook"

    return stats

def main():
    print(f"[{datetime.utcnow()}] LUFT Daily Harvester starting...")

    # 1. Find ALL matching files in current tree
    all_files = []
    for ext in EXTENSIONS:
        all_files.extend(ROOT.rglob(f"*{ext}"))

    print(f"Found {len(all_files):,} files to scan.")

    # 2. Process them
    manifest = []
    for f in all_files:
        if f.is_file():
            manifest.append(process_file(f))

    # 3. Recent commit delta (for Colab "what changed today")
    changed_files = get_recent_commits(days=1)
    print(f"Files changed in last 24h: {len(changed_files)}")

    # 4. Save outputs
    manifest_path = OUTPUT_DIR / f"daily_manifest_{datetime.utcnow().strftime('%Y%m%d')}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Simple summary CSV
    summary_df = pd.DataFrame(manifest)
    summary_path = OUTPUT_DIR / f"daily_summary_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    summary_df.to_csv(summary_path, index=False)

    print(f"✅ Harvest complete: {len(manifest):,} files indexed")
    print(f"   • Manifest: {manifest_path}")
    print(f"   • Summary CSV: {summary_path}")
    print(f"   • Ready for Colab notebooks")

if __name__ == "__main__":
    main()
