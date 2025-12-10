#!/usr/bin/env python3
"""
Render Capsule Charts for December 2025 CME Heartbeat Data

This script reads data/cme_heartbeat_log_2025_12.csv and generates three charts:
1. chi_amplitude_vs_time.png - Chi amplitude colored by storm phase
2. dynamic_pressure_vs_time.png - Dynamic pressure (P_dyn) over time
3. phase_radians_vs_time.png - Phase radians over time

Charts are saved to capsules/2025_dec_batch/charts/

Usage:
    python scripts/render_capsule_charts.py
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Paths relative to repo root
DATA_PATH = Path("data") / "cme_heartbeat_log_2025_12.csv"
OUTPUT_DIR = Path("capsules") / "2025_dec_batch" / "charts"


def compute_dynamic_pressure(df: pd.DataFrame) -> pd.Series:
    """
    Compute dynamic pressure P_dyn in nPa from density (p/cm^3) and speed (km/s).
    
    Formula (standard solar wind approximation):
        P_dyn [nPa] = 1.6726e-6 * n * v^2
    
    where:
        n = density_p_cm3 (protons per cubic cm)
        v = speed_km_s (km/s)
    """
    n = df["density_p_cm3"]
    v = df["speed_km_s"]
    return 1.6726e-6 * n * v * v


def map_storm_phase_colors(storm_phase: pd.Series) -> pd.Series:
    """
    Map storm_phase to colors:
    - 'peak'        -> 'red'
    - 'post-storm'  -> 'green'
    - 'pre'         -> 'grey'
    """
    mapping = {
        "peak": "red",
        "post-storm": "green",
        "pre": "grey",
    }
    return storm_phase.map(mapping).fillna("grey")


def render_chi_amplitude_chart(df: pd.DataFrame, output_path: Path):
    """
    Render chart 1: Chi amplitude vs time, colored by storm phase.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Map colors
    colors = map_storm_phase_colors(df["storm_phase"])
    
    # Scatter plot with color coding
    ax.scatter(
        df["timestamp_utc"],
        df["chi_amplitude"],
        c=colors,
        s=30,
        alpha=0.7,
        edgecolor="none",
    )
    
    ax.set_xlabel("Time (UTC)", fontsize=12)
    ax.set_ylabel("χ Amplitude", fontsize=12)
    ax.set_title("LUFT CME Heartbeat — χ Amplitude (December 2025)", fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Peak'),
        Patch(facecolor='green', label='Post-storm'),
        Patch(facecolor='grey', label='Pre'),
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"✓ Saved: {output_path}")


def render_dynamic_pressure_chart(df: pd.DataFrame, output_path: Path):
    """
    Render chart 2: Dynamic pressure vs time.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Compute dynamic pressure
    p_dyn = compute_dynamic_pressure(df)
    
    # Line plot
    ax.plot(
        df["timestamp_utc"],
        p_dyn,
        color="black",
        linewidth=1.5,
        label="P_dyn (nPa)",
    )
    
    ax.set_xlabel("Time (UTC)", fontsize=12)
    ax.set_ylabel("Dynamic Pressure P_dyn (nPa)", fontsize=12)
    ax.set_title("LUFT CME Heartbeat — Dynamic Pressure (December 2025)", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    fig.autofmt_xdate()
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"✓ Saved: {output_path}")


def render_phase_radians_chart(df: pd.DataFrame, output_path: Path):
    """
    Render chart 3: Phase radians vs time.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Scatter plot
    ax.scatter(
        df["timestamp_utc"],
        df["phase_radians"],
        color="steelblue",
        s=30,
        alpha=0.7,
        edgecolor="none",
        label="Phase (radians)",
    )
    
    ax.set_xlabel("Time (UTC)", fontsize=12)
    ax.set_ylabel("Phase (radians)", fontsize=12)
    ax.set_title("LUFT CME Heartbeat — Phase Radians (December 2025)", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    fig.autofmt_xdate()
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"✓ Saved: {output_path}")


def main():
    """
    Main function to load data and generate all three charts.
    """
    # Check if data file exists
    if not DATA_PATH.exists():
        print(f"❌ Error: Data file not found at {DATA_PATH.resolve()}", file=sys.stderr)
        sys.exit(1)
    
    # Load CSV
    print(f"📊 Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Parse timestamps
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    
    # Sort by time
    df = df.sort_values("timestamp_utc")
    
    print(f"   Loaded {len(df)} records from {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR.resolve()}")
    
    # Generate charts
    print("\n🎨 Generating charts...")
    
    render_chi_amplitude_chart(
        df,
        OUTPUT_DIR / "chi_amplitude_vs_time.png"
    )
    
    render_dynamic_pressure_chart(
        df,
        OUTPUT_DIR / "dynamic_pressure_vs_time.png"
    )
    
    render_phase_radians_chart(
        df,
        OUTPUT_DIR / "phase_radians_vs_time.png"
    )
    
    print("\n✅ All charts generated successfully!")
    print(f"   Charts saved to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
