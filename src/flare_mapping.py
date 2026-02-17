#!/usr/bin/env python3
"""
Map proton flux to foam parameter f(t) and hierarchy amplified f_h(t).
"""
import pandas as pd
import numpy as np
import argparse
import json
import os

def map_flux_to_f(flux, flux_ref=100.0, beta=0.05, gamma=1.0):
    # δρ/ρ ≈ -beta * (flux/flux_ref)^gamma
    return -beta * (flux/flux_ref)**gamma

def amplify_hierarchy(f, X_ratio, alpha):
    return np.exp(alpha * np.log(X_ratio)) * f

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flux_csv', default='data/processed/goes_flux.csv')
    ap.add_argument('--X_ratio', type=float, default=100.0)
    ap.add_argument('--alpha', type=float, default=0.1)
    ap.add_argument('--beta', type=float, default=0.05)
    ap.add_argument('--gamma', type=float, default=1.0)
    ap.add_argument('--out', default='data/processed/f_series.csv')
    args = ap.parse_args()

    df = pd.read_csv(args.flux_csv, parse_dates=['time'])
    df['f'] = map_flux_to_f(df['flux_smoothed'], beta=args.beta, gamma=args.gamma)
    df['f_hierarchy'] = amplify_hierarchy(df['f'], args.X_ratio, args.alpha)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)
    meta = {
        'X_ratio': args.X_ratio,
        'alpha': args.alpha,
        'beta': args.beta,
        'gamma': args.gamma,
        'flux_ref': 100.0
    }
    with open(args.out.replace('.csv', '_meta.json'), 'w') as fh:
        json.dump(meta, fh, indent=2)
    print("Wrote", args.out, "rows:", len(df))

if __name__ == '__main__':
    main()
