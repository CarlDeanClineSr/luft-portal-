#!/usr/bin/env python3
"""
Paper Visualization Generator for LUFT Portal

Generates publication-quality figures for academic papers:
- Figure 1: Saturation Histogram ("The Wall")
- Figure 2: Recovery Dynamics Time Series

Uses data from: data/cme_heartbeat_log_2025_12.csv

The theoretical limit used is (m_e/m_p)^(1/4) ≈ 0.153
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# =============================================================================
# Physical Constants
# =============================================================================
ELECTRON_MASS_KG = 9.109e-31  # Electron mass in kg
PROTON_MASS_KG = 1.672e-27    # Proton mass in kg

# Theoretical quantum limit: (m_e/m_p)^(1/4) ≈ 0.153
MASS_RATIO_LIMIT = (ELECTRON_MASS_KG / PROTON_MASS_KG) ** 0.25

# =============================================================================
# Histogram Configuration
# =============================================================================
HISTOGRAM_MIN = 0.0
HISTOGRAM_MAX = 0.4
HISTOGRAM_BINS = 100

# =============================================================================
# Time Series Slice Configuration
# =============================================================================
# Default starting index for time series slice
SLICE_START_DEFAULT = 450
# Offset from end of data if data is shorter than default start
SLICE_END_OFFSET = 350
# Number of rows to include in slice
SLICE_LENGTH = 300
# Minimum acceptable slice size before using full dataset
SLICE_MIN_SIZE = 50

# =============================================================================
# File Paths
# =============================================================================
DATA_FILE = Path('data/cme_heartbeat_log_2025_12.csv')
OUTPUT_DIR = Path('paper_visuals')


def load_and_prepare_data(data_file: Path) -> pd.DataFrame:
    """
    Load and prepare data from the CME heartbeat log CSV.

    The CSV has columns: timestamp_utc, chi_amplitude, phase_radians,
    storm_phase, density_p_cm3, speed_km_s, bz_nT, bt_nT, source
    (plus optional chi_at_boundary, chi_violation, chi_status)

    The CSV may have inconsistent formatting with some rows containing
    full data and some containing partial data. This function handles
    such inconsistencies.

    Returns a cleaned DataFrame with:
    - timestamp: parsed datetime
    - chi_calc: normalized magnetic perturbation (uses chi_amplitude directly)
    - is_transient: 1 for 'peak' phase, 0 for others
    """
    # Read CSV with error handling for malformed rows
    # Use on_bad_lines='skip' to skip problematic rows
    df = pd.read_csv(data_file, on_bad_lines='skip')

    # Drop rows where timestamp_utc is missing or invalid
    df = df.dropna(subset=['timestamp_utc'])

    # Filter out rows with empty or whitespace-only timestamps
    df = df[df['timestamp_utc'].astype(str).str.strip() != '']

    # Filter out rows that don't look like valid timestamps
    # Valid timestamps start with a year (e.g., 2025-)
    df = df[df['timestamp_utc'].astype(str).str.match(r'^\d{4}-')]

    # Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
    df = df.dropna(subset=['timestamp'])

    # Drop rows where chi_amplitude is missing or invalid
    df = df.dropna(subset=['chi_amplitude'])

    # Use chi_amplitude as chi_calc (already normalized)
    df['chi_calc'] = pd.to_numeric(df['chi_amplitude'], errors='coerce')
    df = df.dropna(subset=['chi_calc'])

    # Create is_transient flag based on storm_phase
    # 'peak' indicates transient/active shock events
    df['is_transient'] = (df['storm_phase'] == 'peak').astype(int)

    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)

    return df


def generate_saturation_histogram(df: pd.DataFrame, output_dir: Path,
                                  mass_ratio_limit: float) -> str:
    """
    Generate Figure 1: The Saturation "Wall" Histogram.

    Shows the empirical distribution of chi values, highlighting the
    theoretical quantum limit.
    """
    plt.figure(figsize=(12, 7))

    # Define histogram bins
    hist_bins = np.linspace(HISTOGRAM_MIN, HISTOGRAM_MAX, HISTOGRAM_BINS)

    # Plot Steady State (Quiescent) - The blue wall
    steady_state = df[df['is_transient'] == 0]
    sns.histplot(
        data=steady_state,
        x='chi_calc',
        bins=hist_bins,
        color="#004e92",  # Professional dark blue
        alpha=0.7,
        label='Steady State (Quiescent Plasma)',
        stat='density',
        element="step"
    )

    # Plot Transients (Shocks) - The red tail
    transients = df[df['is_transient'] == 1]
    if len(transients) > 0:
        sns.histplot(
            data=transients,
            x='chi_calc',
            bins=hist_bins,
            color="#d9534f",  # Professional red
            alpha=0.4,
            label='Transient (Active Shock/CME)',
            stat='density',
            element="step"
        )

    # The Theoretical Limit Line
    plt.axvline(x=mass_ratio_limit, color='black', linestyle='--', linewidth=2.5,
                label=r'Quantum Limit $(m_e/m_p)^{1/4} \approx 0.153$')

    # Styling
    plt.xlim(0, 0.35)
    plt.xlabel(r'Normalized Magnetic Perturbation ($\chi = \delta B / B_0$)',
               fontsize=14, fontweight='bold')
    plt.ylabel('Probability Density', fontsize=14, fontweight='bold')
    plt.title('Empirical Discovery: The 0.15 Saturation "Wall"',
              fontsize=16, pad=20)
    plt.legend(fontsize=12)
    plt.tight_layout()

    # Save
    outfile = output_dir / 'Fig1_Saturation_Wall.png'
    plt.savefig(outfile, dpi=300)
    plt.close()

    return str(outfile)


def generate_recovery_dynamics(df: pd.DataFrame, output_dir: Path,
                               mass_ratio_limit: float) -> str:
    """
    Generate Figure 2: Recovery Dynamics Time Series.

    Shows chi over time with violation zones highlighted.
    """
    # Find a good example slice with activity
    # Look for periods where chi approaches or exceeds the limit
    n_rows = len(df)
    start_idx = min(SLICE_START_DEFAULT, max(0, n_rows - SLICE_END_OFFSET))
    end_idx = min(start_idx + SLICE_LENGTH, n_rows)

    slice_df = df.iloc[start_idx:end_idx].copy()

    # If slice is too small, use all data
    if len(slice_df) < SLICE_MIN_SIZE:
        slice_df = df.copy()

    plt.figure(figsize=(12, 6))

    # Plot the Chi time series
    plt.plot(slice_df['timestamp'], slice_df['chi_calc'],
             color='#333333', linewidth=1.5, label=r'Observed $\chi$')

    # Highlight the violation area (above 0.153)
    plt.fill_between(
        slice_df['timestamp'],
        mass_ratio_limit,
        slice_df['chi_calc'],
        where=(slice_df['chi_calc'] > mass_ratio_limit),
        interpolate=True,
        color='#d9534f',
        alpha=0.3,
        label='Transient Violation Zone'
    )

    # The Limit Line
    plt.axhline(y=mass_ratio_limit, color='#004e92', linestyle='--',
                linewidth=2, label='Attractor Boundary (0.153)')

    # Styling
    plt.ylabel(r'$\chi$', fontsize=14, fontweight='bold')
    plt.xlabel('Time', fontsize=14, fontweight='bold')
    plt.title('Dynamic Regulation: Transient Violation and Rapid Recovery',
              fontsize=16, pad=20)
    plt.legend(loc='upper right', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save
    outfile = output_dir / 'Fig2_Recovery_Dynamics.png'
    plt.savefig(outfile, dpi=300)
    plt.close()

    return str(outfile)


def main():
    """Main entry point for generating paper visuals."""
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Set professional styling
    sns.set_theme(style="whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'

    print(f"Loading data from {DATA_FILE}...")
    if not DATA_FILE.exists():
        print(f"ERROR: Data file not found: {DATA_FILE}")
        return 1

    df = load_and_prepare_data(DATA_FILE)
    print(f"Loaded {len(df)} rows of data")

    # Generate Figure 1: Saturation Histogram
    print("Generating Figure 1: Saturation Histogram...")
    fig1_path = generate_saturation_histogram(df, OUTPUT_DIR, MASS_RATIO_LIMIT)
    print(f"Saved {fig1_path}")

    # Generate Figure 2: Recovery Dynamics
    print("Generating Figure 2: Recovery Dynamics...")
    fig2_path = generate_recovery_dynamics(df, OUTPUT_DIR, MASS_RATIO_LIMIT)
    print(f"Saved {fig2_path}")

    print(f"\nVisuals generation complete. Check the '{OUTPUT_DIR}' folder.")
    return 0


if __name__ == "__main__":
    exit(main())
