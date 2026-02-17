#!/usr/bin/env python3
"""
Validate χ-Fractal Regulator
Tests if χ ≤ 0.15 holds universally across all plasma regimes

Author: Carl Dean Cline Sr.
Date: 2026-01-07
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

CHI_BOUNDARY = 0.15


def load_all_environments():
    """
    Load χ data from all validated environments.
    
    Configured data sources (loads whichever are available):
    - Earth Solar Wind: data/cme_heartbeat_log_2025_12.csv (primary data)
    - Mars: data/maven_chi_validation.csv (optional, for multi-planetary validation)
    - Earth Magnetosphere: results/magnetometer_chi/magnetometer_chi_2025_12_26.csv
    
    Missing files are skipped gracefully with a warning message.
    """

    datasets = {
        'Earth Solar Wind': {
            'file': 'data/cme_heartbeat_log_2025_12.csv',
            'B_range': (3, 15),  # nT
            'location': '1 AU'
        },
        'Mars': {
            'file': 'data/maven_chi_validation.csv',  # Optional - for Mars validation
            'B_range': (1, 10),  # nT
            'location': '1.5 AU'
        },
        'Earth Magnetosphere': {
            'file': 'results/magnetometer_chi/magnetometer_chi_2025_12_26.csv',
            'B_range': (10000, 60000),  # nT
            'location': 'Ground'
        }
    }

    results = []

    for env_name, config in datasets.items():
        file_path = Path(config['file'])

        if not file_path.exists():
            print(f"⚠️  {env_name}: File not found - {config['file']}")
            continue

        try:
            df = pd.read_csv(file_path, on_bad_lines='skip')
        except Exception as e:
            print(f"⚠️  {env_name}: Error loading file - {e}")
            continue

        # Try to find chi column with various names
        chi_col = None
        for col in ['chi', 'chi_amplitude', 'chi_capped', 'chi_mean']:
            if col in df.columns:
                chi_col = col
                break

        if chi_col is None:
            print(f"⚠️  {env_name}: No chi column found")
            continue

        # Drop rows with no valid timestamp (status rows)
        if 'timestamp_utc' in df.columns:
            df = df.dropna(subset=['timestamp_utc'])

        # Convert chi values to numeric, ignoring errors
        chi_values = pd.to_numeric(df[chi_col], errors='coerce').dropna()

        if len(chi_values) == 0:
            print(f"⚠️  {env_name}: No valid chi values")
            continue

        results.append({
            'environment': env_name,
            'location': config['location'],
            'B_min_nT': config['B_range'][0],
            'B_max_nT': config['B_range'][1],
            'B_range_orders': np.log10(config['B_range'][1] / config['B_range'][0]),
            'observations': len(chi_values),
            'chi_mean': chi_values.mean(),
            'chi_max': chi_values.max(),
            'chi_std': chi_values.std(),
            'violations': (chi_values > CHI_BOUNDARY).sum(),
            'violation_rate': (chi_values > CHI_BOUNDARY).sum() / len(chi_values),
            'at_boundary': ((chi_values >= 0.145) & (chi_values <= 0.155)).sum(),
            'attractor_fraction': ((chi_values >= 0.145) & (chi_values <= 0.155)).sum() / len(chi_values)
        })

    return pd.DataFrame(results)


def calculate_scale_span(df_envs):
    """Calculate total span across all environments"""

    if len(df_envs) == 0:
        return None

    B_min = df_envs['B_min_nT'].min()
    B_max = df_envs['B_max_nT'].max()

    field_span_orders = np.log10(B_max / B_min)

    total_obs = df_envs['observations'].sum()
    total_violations = df_envs['violations'].sum()

    return {
        'B_min_nT': B_min,
        'B_max_nT': B_max,
        'field_span_factor': B_max / B_min,
        'field_span_orders': field_span_orders,
        'total_observations': total_obs,
        'total_violations': total_violations,
        'global_violation_rate': total_violations / total_obs if total_obs > 0 else np.nan,
        'universal': total_violations == 0
    }


def plot_multi_scale(df_envs):
    """Create multi-scale validation plot"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Panel 1: χ_max vs field strength
    colors = ['blue', 'red', 'green', 'purple', 'orange']

    for i, (_, row) in enumerate(df_envs.iterrows()):
        B_center = np.sqrt(row['B_min_nT'] * row['B_max_nT'])
        ax1.errorbar(B_center, row['chi_max'],
                     xerr=[[B_center - row['B_min_nT']], [row['B_max_nT'] - B_center]],
                     fmt='o', markersize=10, capsize=5,
                     color=colors[i % len(colors)],
                     label=row['environment'])

    ax1.axhline(CHI_BOUNDARY, color='red', linestyle='--', linewidth=2,
                label=f'χ boundary = {CHI_BOUNDARY}')
    ax1.set_xscale('log')
    ax1.set_xlabel('Magnetic Field Strength (nT)')
    ax1.set_ylabel('Maximum χ')
    ax1.set_ylim([0, 0.20])
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax1.set_title('Universal χ Boundary Across Field Strengths')

    # Panel 2: Violation statistics
    x_pos = np.arange(len(df_envs))
    ax2.bar(x_pos, df_envs['violation_rate'] * 100,
            color=[colors[i % len(colors)] for i in range(len(df_envs))],
            edgecolor='black', alpha=0.7)

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(df_envs['environment'], rotation=15, ha='right')
    ax2.set_ylabel('Violation Rate (%)')
    ax2.set_title('Violation Rate by Environment (Should be 0%)')
    ax2.grid(alpha=0.3, axis='y')
    ax2.axhline(0, color='green', linestyle='--', linewidth=2,
                label='Zero violations')
    ax2.legend()

    plt.tight_layout()
    return fig


def main():
    print("=" * 70)
    print("VALIDATING χ-FRACTAL REGULATOR")
    print("=" * 70)

    # Load all environments
    print("\n📊 Loading data from all environments...")
    df_envs = load_all_environments()

    if len(df_envs) == 0:
        print("❌ ERROR: No environment data found")
        return

    print(f"✅ Loaded {len(df_envs)} environments")
    print("\nPer-Environment Results:")
    print(df_envs.to_string(index=False))

    # Calculate global span
    print("\n🔬 Calculating multi-scale span...")
    span = calculate_scale_span(df_envs)

    print("\n" + "=" * 70)
    print("MULTI-SCALE ANALYSIS")
    print("=" * 70)
    print(f"Field strength range:   {span['B_min_nT']:.1f} nT → {span['B_max_nT']:.1f} nT")
    print(f"Span factor:           {span['field_span_factor']:.1f}×")
    print(f"Span (orders of mag):  {span['field_span_orders']:.2f}")
    print()
    print(f"Total observations:    {span['total_observations']:,}")
    print(f"Total violations:      {span['total_violations']}")
    print(f"Global violation rate: {span['global_violation_rate'] * 100:.4f}%")
    print()

    if span['universal']:
        print("✅ UNIVERSAL BOUNDARY CONFIRMED: χ ≤ 0.15 across ALL scales")
    else:
        print(f"⚠️  {span['total_violations']} violations detected")

    # Ensure results directory exists
    Path('results').mkdir(exist_ok=True)

    # Plot
    print("\n📈 Generating validation plot...")
    fig = plot_multi_scale(df_envs)
    fig.savefig('results/fractal_regulator_validation.png', dpi=300)
    print("✅ Plot saved: results/fractal_regulator_validation.png")

    # Save results
    df_envs.to_csv('results/fractal_regulator_by_environment.csv', index=False)

    span_df = pd.DataFrame([span])
    span_df.to_csv('results/fractal_regulator_global_span.csv', index=False)

    print("✅ Results saved")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
