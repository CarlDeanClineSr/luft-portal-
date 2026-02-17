from __future__ import annotations
import numpy as np
from pathlib import Path
import pandas as pd
from analyses.common.io import ensure_dir

def synth_desi_residuals(n: int = 500, hours: float = 24.0, omega_hz: float = 1e-4, chi_true: float = 0.008, noise: float = 0.01, seed: int = 0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, hours*3600.0, n)
    y = chi_true * np.cos(2*np.pi*omega_hz*t) + noise * rng.standard_normal(n)
    return t, y

def save_residuals_csv(t: np.ndarray, y: np.ndarray, out_csv: str | Path) -> None:
    ensure_dir(Path(out_csv).parent)
    pd.DataFrame({"t_s": t, "residual": y}).to_csv(out_csv, index=False)

if __name__ == "__main__":
    t, y = synth_desi_residuals()
    save_residuals_csv(t, y, "data/synthetic/desi/desi_residuals_synth.csv")
    print("Wrote data/synthetic/desi/desi_residuals_synth.csv")
