#!/usr/bin/env python3
"""
Plot χ time series from INTERMAGNET chi calculation CSV
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt


def plot_chi(input_file, output_file):
    df = pd.read_csv(input_file, parse_dates=['timestamp'])
    chi_mean = df['chi'].mean()
    
    plt.figure(figsize=(12, 4))
    plt.plot(df['timestamp'], df['chi'], label='χ', color='blue')
    plt.axhline(0.15, color='red', linestyle='--', label='χ = 0.15')
    plt.axhline(chi_mean, color='green', linestyle=':', label='Mean χ')
    plt.xlabel('Timestamp')
    plt.ylabel('χ')
    plt.title('INTERMAGNET χ Time Series')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"✅ Saved plot → {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input CSV with chi column')
    parser.add_argument('--output', required=True, help='Output PNG path')
    args = parser.parse_args()
    
    plot_chi(args.input, args.output)
