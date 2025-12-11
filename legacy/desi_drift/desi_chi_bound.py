from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Tuple

@dataclass
class ChiBound:
    chi_hat: float
    chi_95: float
    omega_hz: float
    n: int

def fit_sinusoid_bound(times_s: np.ndarray, residuals: np.ndarray, omega_hz: float) -> ChiBound:
    """
    Minimal GLS-like fit for residual(t) ~ chi * cos(omega t) + eps.
    Returns amplitude estimate and a conservative 95% bound using
    sigma * 1.96 / sqrt(N/2) (accounting for cos/sin basis DOF).
    """
    t = times_s
    c = np.cos(2*np.pi*omega_hz * t)
    s = np.sin(2*np.pi*omega_hz * t)

    X = np.column_stack([c, s])
    # OLS as placeholder
    beta, *_ = np.linalg.lstsq(X, residuals, rcond=None)
    amp = np.hypot(beta[0], beta[1])

    # Residual std
    pred = X @ beta
    eps = residuals - pred
    sigma = float(np.std(eps, ddof=2))
    n = len(residuals)

    # Simple 95% bound (conservative)
    chi_95 = amp + 1.96 * sigma / np.sqrt(max(n/2, 1))
    return ChiBound(chi_hat=float(amp), chi_95=float(chi_95), omega_hz=omega_hz, n=n)

if __name__ == "__main__":
    # Synthetic smoke test
    rng = np.random.default_rng(0)
    n = 500
    t = np.linspace(0, 24*3600, n)   # one day
    omega = 1e-4  # Hz
    chi_true = 0.008
    y = chi_true * np.cos(2*np.pi*omega*t) + 0.01 * rng.standard_normal(n)
    out = fit_sinusoid_bound(t, y, omega)
    print(out)
