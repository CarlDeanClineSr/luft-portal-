from __future__ import annotations
import numpy as np
from typing import Dict, Any

try:
    from astropy.timeseries import LombScargle
except Exception:
    LombScargle = None

def sampling_window_power(t: np.ndarray, omega_hz: float, sideband_frac: float = 0.1) -> Dict[str, Any]:
    """
    Compute Lomb–Scargle power of the sampling window at Ω and sidebands.
    We model the window as a unit series at sample times and LS that vector.
    """
    out = {
        "omega_hz": float(omega_hz),
        "power": np.nan,
        "sidebands": [],
        "n_eff": int(len(t)),
        "gap_stats": {"median_gap_s": np.nan, "max_gap_s": np.nan},
    }
    if t.size == 0:
        return out
    # Gap stats
    dt = np.diff(np.sort(t))
    if dt.size:
        out["gap_stats"]["median_gap_s"] = float(np.median(dt))
        out["gap_stats"]["max_gap_s"] = float(np.max(dt))

    if LombScargle is None:
        return out

    # Build a simple window series: ones at sample times → LS via "event" approximation
    # We approximate by treating samples as measurements of value=1 with unit variance.
    y = np.ones_like(t)
    freq = np.array([omega_hz, omega_hz * (1 + sideband_frac), omega_hz * (1 - sideband_frac)], dtype=float)
    ls = LombScargle(t, y)
    p = ls.power(freq)
    out["power"] = float(p[0])
    out["sidebands"] = [{"omega_hz": float(freq[1]), "power": float(p[1])},
                        {"omega_hz": float(freq[2]), "power": float(p[2])}]
    return out
