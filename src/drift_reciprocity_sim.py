#!/usr/bin/env python3
"""
Simulate drift reciprocity: f updated from v_d feedback.
"""
import numpy as np
import pandas as pd
import argparse
import json
import os
import matplotlib.pyplot as plt

def v_d(f, X_ratio, base_grad=1.0, m_eq0=1.0, delta_t=1.0):
    # m_eq reduction model: m_eq = m_eq0 * (1 + 0.1 * f)
    m_eq = m_eq0 * (1 + 0.1 * f)
    # enforce positivity
    m_eq = np.maximum(m_eq, 1e-6)
    return (base_grad / m_eq) * np.sqrt(np.maximum(1 + f, 1e-6)) / delta_t * np.exp(np.log(X_ratio)*0.0)  # gradient placeholder

def simulate(f0=-0.05, X_ratio=100.0, alpha=0.1, steps=500, lambda_=0.02, eta=0.01):
    f_values = [f0]
    v_values = []
    for i in range(steps):
        f_current = f_values[-1]
        # amplify hierarchy for drift link
        f_h = np.exp(alpha * np.log(X_ratio)) * f_current
        v = v_d(f_h, X_ratio)
        v_values.append(v)
        f_next = f_current + lambda_ * (v / v_values[0] - 1) - eta * f_current
        f_values.append(f_next)
    return np.array(f_values), np.array(v_values)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--f0', type=float, default=-0.05)
    ap.add_argument('--X_ratio', type=float, default=100.0)
    ap.add_argument('--alpha', type=float, default=0.1)
    ap.add_argument('--steps', type=int, default=500)
    ap.add_argument('--lambda_', type=float, default=0.02)
    ap.add_argument('--eta', type=float, default=0.01)
    ap.add_argument('--out', default='results/drift_reciprocity.json')
    ap.add_argument('--plot', default='figures/drift_reciprocity.png')
    args = ap.parse_args()

    f_series, v_series = simulate(args.f0, args.X_ratio, args.alpha, args.steps, args.lambda_, args.eta)
    stability = 'stable' if np.abs(f_series[-1]) < 2 * np.abs(args.f0) else 'unstable'
    os.makedirs('results', exist_ok=True)
    os.makedirs('figures', exist_ok=True)
    fig, ax = plt.subplots(2, 1, figsize=(9,6))
    ax[0].plot(f_series, label='f')
    ax[0].set_title('f reciprocal evolution')
    ax[1].plot(v_series, label='v_d')
    ax[1].set_title('v_d evolution')
    for a in ax: a.legend()
    fig.tight_layout()
    fig.savefig(args.plot)
    summary = {
        'f0': args.f0,
        'f_final': float(f_series[-1]),
        'v_initial': float(v_series[0]),
        'v_final': float(v_series[-1]),
        'stability': stability
    }
    with open(args.out, 'w') as fh:
        json.dump(summary, fh, indent=2)
    print("Saved", args.out, "stability:", stability)

if __name__ == '__main__':
    main()
