from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class ChiBound:
    chi_hat: float
    chi_95: float
    omega_hz: float
    n: int

def fit_sinusoid_bound(times_s: np.ndarray, residuals: np.ndarray, omega_hz: float) -> ChiBound:
    t = times_s
    c = np.cos(2*np.pi*omega_hz * t)
    s = np.sin(2*np.pi*omega_hz * t)
    X = np.column_stack([c, s])
    beta, *_ = np.linalg.lstsq(X, residuals, rcond=None)
    amp = float(np.hypot(beta[0], beta[1]))
    pred = X @ beta
    eps = residuals - pred
    sigma = float(np.std(eps, ddof=2))
    n = len(residuals)
    chi_95 = amp + 1.96 * sigma / np.sqrt(max(n/2, 1))
    return ChiBound(chi_hat=amp, chi_95=chi_95, omega_hz=omega_hz, n=n)

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/synthetic/desi/desi_residuals_synth.csv")
    out = fit_sinusoid_bound(df["t_s"].to_numpy(), df["residual"].to_numpy(), omega_hz=1e-4)
    print(out)
