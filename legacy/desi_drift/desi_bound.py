from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class ChiBound:
    chi_hat: float
    chi_95: float
    omega_hz: float
    n: int
    delta_rms: float
    p_null: float

def fit_chi_bound(t: np.ndarray, y: np.ndarray, omega_hz: float) -> ChiBound:
    # Two-phase OLS fit
    c = np.cos(2*np.pi*omega_hz * t)
    s = np.sin(2*np.pi*omega_hz * t)
    X = np.column_stack([c, s])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    a, b = beta
    amp = float(np.hypot(a, b))
    y_hat = X @ beta
    eps = y - y_hat
    sigma = float(np.std(eps, ddof=2))
    n = len(y)
    # Conservative bound
    chi_95 = amp + 1.96 * sigma / np.sqrt(max(n/2, 1))
    # RMS improvement
    rms_base = float(np.sqrt(np.mean((y - np.mean(y))**2)))
    rms_model = float(np.sqrt(np.mean(eps**2)))
    delta_rms = rms_base - rms_model
    return ChiBound(chi_hat=amp, chi_95=chi_95, omega_hz=omega_hz, n=n, delta_rms=delta_rms, p_null=np.nan)
