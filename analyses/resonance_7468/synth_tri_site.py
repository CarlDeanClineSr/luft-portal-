from __future__ import annotations
import numpy as np
from pathlib import Path
import pandas as pd
from analyses.common.io import ensure_dir

def synth_site_series(n: int, f0_hz: float, amp: float, noise: float, seed: int):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 24*3600, n)
    sig = amp * np.cos(2*np.pi*f0_hz * t + rng.uniform(0, 2*np.pi))
    x = sig + noise * rng.standard_normal(n)
    return t, x

def write_site_csv(t: np.ndarray, x: np.ndarray, out_csv: str | Path):
    ensure_dir(Path(out_csv).parent)
    pd.DataFrame({"t_s": t, "value": x}).to_csv(out_csv, index=False)

if __name__ == "__main__":
    f0 = 7468.0
    n = 5000
    for i, seed in enumerate([1, 2, 3], start=1):
        t, x = synth_site_series(n=n, f0_hz=f0, amp=1.0, noise=1.0, seed=seed)
        write_site_csv(t, x, f"data/synthetic/7468/site{i}.csv")
    print("Wrote data/synthetic/7468/site1..3.csv")
