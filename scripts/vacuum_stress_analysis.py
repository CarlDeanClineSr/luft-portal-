#!/usr/bin/env python3
"""
Vacuum Stress Analysis — MAVEN Telemetry Loader
Dynamically locates the most recent MAVEN summary CSV and derives χ.
"""

import glob
import os
import pandas as pd


def acquire_latest_telemetry(directory_path="data/maven/"):
    """
    Dynamically locates the most recent MAVEN summary CSV.
    Prevents pipeline breaks from filename drift during harvests.
    """
    print(f">>> SCANNING DIRECTORY: {directory_path}")
    search_pattern = os.path.join(directory_path, "*summary*.csv")
    files = glob.glob(search_pattern)

    if not files:
        raise FileNotFoundError(f"❌ FATAL: No summary files in {directory_path}")

    # Sort by modification time (newest first) — reliable cross-platform
    latest_file = max(files, key=os.path.getmtime)
    print(f"✅ TARGET ACQUIRED: {latest_file}")

    return pd.read_csv(latest_file)


if __name__ == "__main__":
    df = acquire_latest_telemetry()

    # Derive χ = 1 - (Avg / Max) from numeric columns
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) == 0:
        print("⚠️  No numeric columns found — cannot compute χ.")
    else:
        col = numeric_cols[0]
        avg_val = df[col].mean()
        max_val = df[col].max()
        chi = 1.0 - (avg_val / max_val) if max_val != 0 else None
        print(f"   Column used : {col}")
        print(f"   Avg={avg_val:.4f}  Max={max_val:.4f}  χ={chi:.4f}" if chi is not None else "   χ undefined (max=0)")
