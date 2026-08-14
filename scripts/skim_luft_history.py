#!/usr/bin/env python3
"""
LUFT Portal Full-History Skim Extractor (Cloud-Native)
======================================================
Skims the complete operational record of the Magnetic Substrate engine
(~49k commits, full file tree, workflows) and generates a visual heatmap.
Designed to run autonomously via GitHub Actions.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

REPO_ROOT = Path(".").resolve()
REPORT_FILE = REPO_ROOT / "LUFT_HISTORY_SKIM_REPORT.md"
HEATMAP_FILE = REPO_ROOT / "commit_heatmap.png"

def run_git(cmd):
    """Run git command with error handling."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Git command failed: {' '.join(cmd)}")
        return ""

def generate_heatmap(dates):
    """Generates a visual heatmap of commit frequency."""
    if not dates:
        return
    
    print("→ Generating commit frequency heatmap …")
    df = pd.DataFrame(dates, columns=['date'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna()
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Count commits per month
    monthly_counts = df['year_month'].value_counts().sort_index()
    
    if monthly_counts.empty:
        return

    plt.figure(figsize=(12, 6))
    sns.barplot(x=monthly_counts.index.astype(str), y=monthly_counts.values, color="steelblue")
    plt.xticks(rotation=45, ha='right')
    plt.title("LUFT Portal Operational Telemetry (Commits per Month)")
    plt.ylabel("Total Commits")
    plt.xlabel("Month")
    plt.tight_layout()
    plt.savefig(HEATMAP_FILE, dpi=150)
    plt.close()

def skim_commits():
    """Extract commit telemetry."""
    print("→ Scanning commit history …")
    total = run_git(["rev-list", "--count", "HEAD"])
    authors = run_git(["shortlog", "-sn", "--all"]).splitlines()
    first = run_git(["log", "--reverse", "--pretty=format:%ci", "-1"])
    last  = run_git(["log", "-1", "--pretty=format:%ci"])

    # Get raw dates for the heatmap
    raw_dates = run_git(["log", "--pretty=format:%ad", "--date=short", "--all"]).splitlines()
    
    months = run_git(["log", "--pretty=format:%ad", "--date=format:%Y-%m", "--all"]).splitlines()
    month_counts = Counter(m for m in months if m)

    generate_heatmap(raw_dates)

    return {
        "total_commits": int(total) if total.isdigit() else 0,
        "first_commit": first or "unknown",
        "last_commit": last or "unknown",
        "top_authors": authors[:20],
        "monthly_activity": dict(sorted(month_counts.items()))
    }

def skim_files():
    """Walk the current tree and classify every file."""
    print("→ Walking current file tree …")
    stats = {
        "total_files": 0,
        "by_extension": Counter(),
        "capsules": [],
        "scripts": [],
        "data_files": [],
        "workflows": [],
        "large_files": []
    }

    for root, dirs, files in os.walk(REPO_ROOT):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            path = Path(root) / f
            rel = str(path.relative_to(REPO_ROOT))
            stats["total_files"] += 1

            ext = path.suffix.lower() or "[no-ext]"
            stats["by_extension"][ext] += 1

            size = path.stat().st_size
            if size > 5_000_000:  # > 5 MB
                stats["large_files"].append((rel, size))

            name = f.lower()
            if "capsule" in name or rel.startswith("capsules/"):
                stats["capsules"].append(rel)

            if ext in {".py", ".sh", ".ipynb"} or "script" in name:
                stats["scripts"].append(rel)

            if ext in {".csv", ".json", ".txt", ".dat", ".h5"} or "data" in rel.lower():
                stats["data_files"].append(rel)

            if ".github/workflows" in rel and ext in {".yml", ".yaml"}:
                stats["workflows"].append(rel)

    return stats

def generate_report(commit_stats, file_stats):
    """Write a clean Markdown report."""
    print(f"→ Writing report to {REPORT_FILE.name} …")

    lines = [
        "# LUFT Portal Full-History Skim Report",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## 1. Commit Telemetry",
        f"- **Total Commits:** {commit_stats['total_commits']:,}",
        f"- **First Commit:** {commit_stats['first_commit']}",
        f"- **Last Commit:** {commit_stats['last_commit']}",
        "",
        "*(See `commit_heatmap.png` for visual activity breakdown)*",
        "",
        "### Top Authors",
        "```text",
        *commit_stats["top_authors"],
        "```",
        "",
        "## 2. File Tree Architecture",
        f"- **Total Files:** {file_stats['total_files']:,}",
        f"- **Scripts (.py / .sh / .ipynb):** {len(file_stats['scripts']):,}",
        f"- **Data Files (.csv / .json / .txt / .h5 / .dat):** {len(file_stats['data_files']):,}",
        f"- **Capsules:** {len(file_stats['capsules']):,}",
        f"- **GitHub Actions Workflows:** {len(file_stats['workflows']):,}",
        "",
        "### Top File Extensions",
        "| Extension | Count |",
        "|-----------|-------|"
    ]

    for ext, count in file_stats["by_extension"].most_common(15):
        lines.append(f"| `{ext}` | {count:,} |")

    if file_stats["large_files"]:
        lines.extend([
            "",
            "### Massive Data Files (> 5 MB)",
            "| File Path | Size (MB) |",
            "|-----------|-----------|"
        ])
        for path, size in sorted(file_stats["large_files"], key=lambda x: x[1], reverse=True)[:20]:
            lines.append(f"| `{path}` | {size / 1_000_000:.2f} |")

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    if not (REPO_ROOT / ".git").exists():
        print("[WARN] Not running inside a git repository. Skim will fail.")

    print("========================================")
    print(" LUFT PORTAL HISTORY SKIM INITIATED")
    print("========================================")

    commit_stats = skim_commits()
    file_stats = skim_files()
    generate_report(commit_stats, file_stats)

    print("========================================")
    print(f" [SUCCESS] Report saved → {REPORT_FILE}")
    print("========================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
