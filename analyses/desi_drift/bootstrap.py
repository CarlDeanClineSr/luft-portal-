from __future__ import annotations
import numpy as np
from typing import Optional, Tuple

def _fit_amp(t: np.ndarray, y: np.ndarray, omega_hz: float) -> float:
    c = np.cos(2*np.pi*omega_hz * t)
    s = np.sin(2*np.pi*omega_hz * t)
    beta, *_ = np.linalg.lstsq(np.column_stack([c, s]), y, rcond=None)
    return float(np.hypot(beta[0], beta[1]))

def bootstrap_amp_ci(
    t: np.ndarray,
    y: np.ndarray,
    omega_hz: float,
    K: int = 10000,
    seed: int = 0,
    group_ids: Optional[np.ndarray] = None,
    q_low: float = 0.05,
    q_mid: float = 0.50,
    q_high: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Returns (chi_05, chi_50, chi_95) via bootstrap.
    If group_ids provided, resample groups (block-aware).
    """
    rng = np.random.default_rng(seed)
    amps = np.empty(K, dtype=float)

    if group_ids is None:
        n = len(t)
        for k in range(K):
            idx = rng.integers(0, n, size=n)
            amps[k] = _fit_amp(t[idx], y[idx], omega_hz)
    else:
        gids = np.asarray(group_ids)
        uniq = np.unique(gids)
        # Build index lists per group
        per_group = [np.where(gids == g)[0] for g in uniq]
        for k in range(K):
            picks = rng.integers(0, len(uniq), size=len(uniq))
            idx = np.concatenate([per_group[i] for i in picks]) if len(picks) else np.array([], int)
            amps[k] = _fit_amp(t[idx], y[idx], omega_hz) if idx.size else np.nan
        amps = amps[~np.isnan(amps)]
    if amps.size == 0:
        return (np.nan, np.nan, np.nan)
    return (float(np.quantile(amps, q_low)),
            float(np.quantile(amps, q_mid)),
            float(np.quantile(amps, q_high)))
