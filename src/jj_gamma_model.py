#!/usr/bin/env python3
"""
Compute Γ(t) and ln Γ(t) given f_hierarchy(t).
Γ = Γ0 * exp[-S f_h]; S = (B0/2 + κ)
"""
import pandas as pd
import numpy as np
import argparse
import os
import json
import matplotlib.pyplot as plt

def compute_gamma(fh, B0=17.0, kappa=10.0, Gamma0=1.0):
    S = (B0/2.0 + kappa)
    lnGamma = np.log(Gamma0) - S * fh
    return np.exp(lnGamma), lnGamma, S

def spectral(lnGamma, dt_seconds):
    # basic FFT amplitude spectrum
    n = len(lnGamma)
    freq = np.fft.rfftfreq(n, dt_seconds)
    amp = np.abs(np.fft.rfft(lnGamma - np.mean(lnGamma)))
    return freq, amp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--f_csv', default='data/processed/f_series.csv')
    ap.add_argument('--B0', type=float, default=17.0)
    ap.add_argument('--kappa', type=float, default=10.0)
    ap.add_argument('--Gamma0', type=float, default=1.0)
    ap.add_argument('--out', default='results/jj_gamma_summary.json')
    ap.add_argument('--plot', default='figures/jj_gamma_timeseries.png')
    args = ap.parse_args()

    df = pd.read_csv(args.f_csv, parse_dates=['time'])
    gamma, lnGamma, S = compute_gamma(df['f_hierarchy'].values, args.B0, args.kappa, args.Gamma0)
    df['Gamma'] = gamma
    df['lnGamma'] = lnGamma
    os.makedirs('results', exist_ok=True)
    os.makedirs('figures', exist_ok=True)
    df.to_csv('results/jj_gamma_timeseries.csv', index=False)

    # Spectrum
    dt = (df['time'].iloc[1] - df['time'].iloc[0]).total_seconds()
    freq, amp = spectral(df['lnGamma'].values, dt)
    target_band = (freq > 1e-5) & (freq < 5e-4)  # around storm periodicities
    peak_freq = freq[target_band][np.argmax(amp[target_band])] if target_band.any() else None

    # Plot
    fig, ax = plt.subplots(2, 1, figsize=(10, 7))
    ax[0].plot(df['time'], df['lnGamma'], label='ln Γ')
    ax[0].set_title('ln Γ(t)')
    ax[0].legend()
    ax[1].loglog(freq, amp, label='Spectrum')
    ax[1].axvline(peak_freq, color='r', linestyle='--', label='Peak')
    ax[1].set_xlabel('Frequency (Hz)')
    ax[1].set_ylabel('Amplitude')
    ax[1].legend()
    fig.tight_layout()
    fig.savefig(args.plot)
    summary = {
        'S': S,
        'peak_freq': float(peak_freq) if peak_freq else None,
        'lnGamma_min': float(df['lnGamma'].min()),
        'lnGamma_max': float(df['lnGamma'].max())
    }
    with open(args.out, 'w') as fh:
        json.dump(summary, fh, indent=2)
    print("Saved", args.out, "and plot", args.plot)

if __name__ == '__main__':
    main()
