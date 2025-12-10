from __future__ import annotations
import numpy as np
from typing import Tuple

def shuffled_time_pvalue(t: np.ndarray, y: np.ndarray, omega_hz: float, K: int = 500, seed: int = 0) -> Tuple[float, float]:
    """
    Permute times K times; return (p_null, chi_null_mean).
    """
    rng = np.random.default_rng(seed)
    c = np.cos(2*np.pi*omega_hz * t)
    s = np.sin(2*np.pi*omega_hz * t)
    X = np.column_stack([c, s])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    chi_hat = float(np.hypot(beta[0], beta[1]))

    chi_null = []
    for _ in range(K):
        t_perm = rng.permutation(t)
        c_p = np.cos(2*np.pi*omega_hz * t_perm); s_p = np.sin(2*np.pi*omega_hz * t_perm)
        Xp = np.column_stack([c_p, s_p])
        bp, *_ = np.linalg.lstsq(Xp, y, rcond=None)
        chi_null.append(float(np.hypot(bp[0], bp[1])))
    chi_null = np.array(chi_null)
    p_null = float(np.mean(chi_null >= chi_hat))
    return p_null, float(np.mean(chi_null))
