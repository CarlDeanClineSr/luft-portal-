#!/usr/bin/env python3
"""
Validate Binary Harmonic Scaling
Tests if 6-hour mode spacing corresponds to 2^8 × proton cyclotron period

Author: Carl Dean Cline Sr.
Date: 2026-01-07
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Physical constants
Q_PROTON = 1.602e-19  # Coulombs
M_PROTON = 1.673e-27  # kg

# 13 temporal modes (hours) - includes baseline (0) and 12 active modes
# Note: 0-hour mode is the baseline and is skipped during ratio calculations
TEMPORAL_MODES = np.array([0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72])


def cyclotron_period(B_nT):
    """
    Calculate proton cyclotron period

    T_ci = 2π m_p / (q_p B)

    Args:
        B_nT: Magnetic field strength in nanoTesla

    Returns:
        Period in seconds
    """
    B_tesla = B_nT * 1e-9
    omega_ci = (Q_PROTON * B_tesla) / M_PROTON
    T_ci = (2 * np.pi) / omega_ci
    return T_ci


def test_binary_scaling():
    """Test if mode spacing = 2^n × T_ci"""

    # Typical interplanetary field strengths
    B_fields = np.array([3, 5, 7, 10, 15])  # nT

    results = []

    for B in B_fields:
        T_ci = cyclotron_period(B)

        # 6-hour mode in seconds
        mode_6h = 6 * 3600  # seconds

        # Calculate ratio
        ratio = mode_6h / T_ci

        # Find nearest power of 2
        log2_ratio = np.log2(ratio)
        nearest_power = np.round(log2_ratio)
        power_of_2 = 2**nearest_power

        # Error
        error_percent = abs(ratio - power_of_2) / power_of_2 * 100

        results.append({
            'B_nT': B,
            'T_ci_seconds': T_ci,
            'ratio_6h_to_Tci': ratio,
            'log2_ratio': log2_ratio,
            'nearest_power': int(nearest_power),
            'power_of_2': power_of_2,
            'error_percent': error_percent,
            'match': error_percent < 10  # Within 10%
        })

    return pd.DataFrame(results)


def test_all_modes():
    """Test all 13 modes for binary structure"""

    B = 7  # Typical IMF at 1 AU
    T_ci = cyclotron_period(B)

    mode_analysis = []

    for mode_hours in TEMPORAL_MODES:
        if mode_hours == 0:
            continue

        mode_seconds = mode_hours * 3600
        ratio = mode_seconds / T_ci
        log2_ratio = np.log2(ratio)

        # Check if ratio is near a power of 2
        nearest_power = np.round(log2_ratio)
        power_of_2 = 2**nearest_power
        error = abs(ratio - power_of_2) / power_of_2 * 100

        mode_analysis.append({
            'mode_hours': mode_hours,
            'mode_seconds': mode_seconds,
            'ratio_to_Tci': ratio,
            'log2_ratio': log2_ratio,
            'nearest_power': int(nearest_power),
            'power_of_2': int(power_of_2),
            'error_percent': error,
            'binary_match': error < 15
        })

    return pd.DataFrame(mode_analysis)


def plot_validation(df_fields, df_modes):
    """Create validation plots"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Panel 1: Field strength dependence
    ax1.plot(df_fields['B_nT'], df_fields['ratio_6h_to_Tci'],
             'bo-', markersize=8, linewidth=2, label='Observed ratio')

    for _, row in df_fields.iterrows():
        ax1.axhline(row['power_of_2'], color='red', linestyle='--', alpha=0.3)
        ax1.text(row['B_nT'], row['power_of_2'],
                 f"2^{int(row['nearest_power'])}", fontsize=9)

    ax1.set_xlabel('Magnetic Field (nT)')
    ax1.set_ylabel('6h mode / T_ci ratio')
    ax1.set_yscale('log', base=2)
    ax1.grid(alpha=0.3)
    ax1.legend()
    ax1.set_title('Binary Scaling Test: 6-hour Mode vs Field Strength')

    # Panel 2: All modes at B = 7 nT
    ax2.bar(df_modes['mode_hours'], df_modes['ratio_to_Tci'],
            alpha=0.6, edgecolor='black', label='Mode / T_ci')

    # Mark powers of 2
    for _, row in df_modes.iterrows():
        ax2.axhline(row['power_of_2'], color='red', linestyle='--', alpha=0.3)

    ax2.set_xlabel('Temporal Mode (hours)')
    ax2.set_ylabel('Ratio to T_ci')
    ax2.set_yscale('log', base=2)
    ax2.grid(alpha=0.3)
    ax2.legend()
    ax2.set_title('All 13 Modes: Binary Structure at B = 7 nT')

    plt.tight_layout()
    return fig


def main():
    print("=" * 70)
    print("VALIDATING BINARY HARMONIC SCALING")
    print("=" * 70)

    # Test 6-hour mode across field strengths
    print("\n🔬 Testing 6-hour mode across field strengths...")
    df_fields = test_binary_scaling()

    print("\nResults:")
    print(df_fields.to_string(index=False))

    matches = df_fields['match'].sum()
    print(f"\n✅ {matches}/{len(df_fields)} field strengths match 2^n scaling")

    # Test all modes at typical field
    print("\n🔬 Testing all 13 modes at B = 7 nT...")
    df_modes = test_all_modes()

    print("\nResults:")
    print(df_modes.to_string(index=False))

    binary_matches = df_modes['binary_match'].sum()
    print(f"\n✅ {binary_matches}/{len(df_modes)} modes match 2^n structure")

    # Ensure results directory exists
    Path('results').mkdir(exist_ok=True)

    # Plot
    print("\n📈 Generating validation plot...")
    fig = plot_validation(df_fields, df_modes)
    fig.savefig('results/binary_harmonic_validation.png', dpi=300)
    print("✅ Plot saved: results/binary_harmonic_validation.png")

    # Save results
    df_fields.to_csv('results/binary_harmonic_fields.csv', index=False)
    df_modes.to_csv('results/binary_harmonic_modes.csv', index=False)
    print("✅ Results saved")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
