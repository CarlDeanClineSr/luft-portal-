#!/usr/bin/env python3
"""
Bootstrap uncertainty on f(t) from flux measurement noise.
"""
import pandas as pd
import numpy as np
import argparse
import json
import os

def bootstrap_f(df, n=500, flux_sigma_frac=0.05, beta=0.05, gamma=1.0):
    samples = []
    flux = df['flux_smoothed'].values
    for _ in range(n):
        noisy = flux * (1 + np.random.normal(0, flux_sigma_frac, size=len(flux)))
        f = -beta * (noisy/100.0)**gamma
        samples.append(f)
    samples = np.array(samples)
    f_mean = samples.mean(axis=0)
    f_std = samples.std(axis=0)
    return f_mean, f_std

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flux_csv', default='data/processed/goes_flux.csv')
    ap.add_argument('--n', type=int, default=500)
    ap.add_argument('--flux_sigma_frac', type=float, default=0.05)
    ap.add_argument('--beta', type=float, default=0.05)
    ap.add_argument('--gamma', type=float, default=1.0)
    ap.add_argument('--out', default='results/f_uncertainty.json')
    args = ap.parse_args()

    df = pd.read_csv(args.flux_csv, parse_dates=['time'])
    f_mean, f_std = bootstrap_f(df, args.n, args.flux_sigma_frac, args.beta, args.gamma)
    os.makedirs('results', exist_ok=True)
    out = {
        'time': df['time'].dt.strftime('%Y-%m-%dT%H:%M:%SZ').tolist(),
        'f_mean': f_mean.tolist(),
        'f_std': f_std.tolist(),
        'beta': args.beta,
        'gamma': args.gamma,
        'flux_sigma_frac': args.flux_sigma_frac
    }
    with open(args.out, 'w') as fh:
        json.dump(out, fh, indent=2)
    print("Saved", args.out)

if __name__ == '__main__':
    main()
