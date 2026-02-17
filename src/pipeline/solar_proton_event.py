#!/usr/bin/env python3
"""
Solar Proton Event Pipeline — LUFT Foam & Hierarchy Test
Run stages: ingest -> map -> amplify -> jj_model -> drift -> stats -> report
"""
import argparse, os, json, pandas as pd, numpy as np
from datetime import datetime
from pathlib import Path

# Placeholder imports for existing modules (adjust path names)
from data_ingest_goes import load_goes, preprocess
from flare_mapping import map_flux_to_f, amplify_hierarchy
from jj_gamma_model import compute_gamma
from drift_reciprocity_sim import simulate as reciprocity_sim

def stats_null_test(df, noise_sigma=0.3):
    # Null lnGamma = lnGamma with f=0 (i.e. lnGamma0)
    lnGamma0 = np.full_like(df['lnGamma'].values, df['lnGamma'].iloc[0])
    delta = df['lnGamma'].values - lnGamma0
    z = delta / noise_sigma
    max_z = float(np.max(z))
    return {'max_z': max_z, 'mean_z': float(np.mean(z)), 'n': len(z)}

def energy_accounting(df, proton_energy_MeV=50.0, c_thrust=0.04):
    # Rough energy usage vs injection
    # E_in(t) ~ flux * proton_energy; E_used ~ (Gamma boost factor fractional) * scaling
    flux = df['flux_smoothed'].values
    f_h = df['f_hierarchy'].values
    S = df.attrs.get('S', 18.0)
    lnGamma_rel = -S * f_h
    gamma_rel = np.exp(lnGamma_rel)
    # Approx thrust/usage fraction
    usage = c_thrust * (gamma_rel - 1.0)
    Ein = flux * proton_energy_MeV
    ratio = np.trapz(usage, dx=1) / np.trapz(Ein, dx=1)
    return {'energy_ratio': float(ratio), 'mean_usage': float(np.mean(usage))}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2025-11-10T00:00:00Z')
    ap.add_argument('--end', default='2025-11-14T00:00:00Z')
    ap.add_argument('--alpha', type=float, default=0.1)
    ap.add_argument('--X_ratio', type=float, default=100.0)
    ap.add_argument('--beta', type=float, default=0.05)
    ap.add_argument('--gamma', type=float, default=1.0)
    ap.add_argument('--B0', type=float, default=17.0)
    ap.add_argument('--kappa', type=float, default=10.0)
    ap.add_argument('--outdir', default='results/event_run')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df_flux = load_goes(None, pd.Timestamp(args.start), pd.Timestamp(args.end))
    df_flux = preprocess(df_flux)
    df_flux['f'] = map_flux_to_f(df_flux['flux_smoothed'], flux_ref=100.0, beta=args.beta, gamma=args.gamma)
    df_flux['f_hierarchy'] = amplify_hierarchy(df_flux['f'], args.X_ratio, args.alpha)

    S = (args.B0/2.0 + args.kappa)
    Gamma, lnGamma, _ = compute_gamma(df_flux['f_hierarchy'].values, args.B0, args.kappa, Gamma0=1.0)
    df_flux['Gamma'] = Gamma
    df_flux['lnGamma'] = lnGamma
    df_flux.attrs['S'] = S

    # Stats
    stat_res = stats_null_test(df_flux)
    energy_res = energy_accounting(df_flux)
    summary = {
        'window': {'start': args.start, 'end': args.end},
        'params': {
            'alpha': args.alpha, 'X_ratio': args.X_ratio, 'beta': args.beta, 'gamma': args.gamma,
            'B0': args.B0, 'kappa': args.kappa, 'S': S
        },
        'stats': stat_res,
        'energy': energy_res,
        'lnGamma_min': float(df_flux['lnGamma'].min()),
        'lnGamma_max': float(df_flux['lnGamma'].max())
    }
    with open(os.path.join(args.outdir, 'summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=2)

    df_flux.to_csv(os.path.join(args.outdir, 'flux_f_gamma_timeseries.csv'), index=False)
    print("Saved summary and timeseries to", args.outdir)

if __name__ == '__main__':
    main()
