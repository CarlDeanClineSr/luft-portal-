#!/usr/bin/env python3
"""
simulate_luft_quantum_tunnel.py

Simple LUFT tunnel simulator:
- Sweeps foam parameter f, hierarchy amplifier alpha, B0 and kappa.
- Computes a WKB-like transmissivity proxy and hierarchy amplification.
- Outputs transmissivity maps and example predicted sideband frequencies.

Usage:
    python simulate_luft_quantum_tunnel.py --outdir outputs/sim01
"""

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt

def gamma_of_f(f, B0=17.0, kappa=10.0):
    # Base WKB/Washboard-inspired rate scaling (dimensionless proxy)
    return np.exp(-(B0 / 2.0 + kappa) * f)

def hierarchy_amplifier(f, X_ratio=100.0, alpha=0.1):
    # f_macro = f * X_ratio^alpha
    return f * (X_ratio ** alpha)

def transmissivity_map(f_vals, alpha_vals, B0=17.0, kappa=10.0, E_ref=125.0, E=125.0):
    T = np.zeros((len(alpha_vals), len(f_vals)))
    for i, a in enumerate(alpha_vals):
        for j, f in enumerate(f_vals):
            f_h = hierarchy_amplifier(f, X_ratio=100.0, alpha=a)
            # energy scaling as (E/E_ref)^a (proxy)
            E_scale = (E / E_ref) ** a
            T[i, j] = gamma_of_f(f_h, B0=B0, kappa=kappa) * E_scale
    return T

def plot_map(T, f_vals, alpha_vals, outdir):
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(T, origin='lower', aspect='auto',
                   extent=(f_vals[0], f_vals[-1], alpha_vals[0], alpha_vals[-1]),
                   cmap='plasma')
    ax.set_xlabel('f (Δρ/ρ_avg)')
    ax.set_ylabel('alpha (hierarchy)')
    ax.set_title('LUFT Transmissivity Map (proxy)')
    fig.colorbar(im, label='Transmissivity proxy Γ(f_h) * E^α')
    os.makedirs(outdir, exist_ok=True)
    fname = os.path.join(outdir, 'transmissivity_map.png')
    plt.savefig(fname, dpi=200)
    plt.close(fig)
    print(f"Saved transmissivity map to {fname}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', default='outputs/sim01')
    parser.add_argument('--B0', type=float, default=17.0)
    parser.add_argument('--kappa', type=float, default=10.0)
    parser.add_argument('--E', type=float, default=125.0)
    args = parser.parse_args()

    f_vals = np.linspace(-0.2, 0.2, 161)  # negative f = voids
    alpha_vals = np.linspace(0.01, 0.2, 121)

    T = transmissivity_map(f_vals, alpha_vals, B0=args.B0, kappa=args.kappa, E=args.E)
    plot_map(T, f_vals, alpha_vals, args.outdir)

    # Example: find ridge maxima (where void amplification could produce standout sidebands)
    idx = np.unravel_index(np.argmax(T), T.shape)
    best_alpha = alpha_vals[idx[0]]
    best_f = f_vals[idx[1]]
    print("Top transmissivity at alpha=%.4f, f=%.4f, value=%.3e" % (best_alpha, best_f, T[idx]))

if __name__ == '__main__':
    main()
