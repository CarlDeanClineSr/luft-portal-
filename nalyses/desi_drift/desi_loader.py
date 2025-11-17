from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

def load_residuals(csv_path: str | Path, t_center: bool = True) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Load DESI-like residuals CSV with columns: t_s, residual (required).
    Returns: t (np.ndarray), y (np.ndarray), meta (dict)
    """
    df = pd.read_csv(csv_path)
    if not {"t_s","residual"}.issubset(df.columns):
        raise ValueError("CSV must contain columns: t_s, residual")
    t = df["t_s"].to_numpy(dtype=float)
    y = df["residual"].to_numpy(dtype=float)
    meta = {"n": len(df)}
    if t_center and len(t) > 0:
        t0 = float(np.median(t))
        t = t - t0
        meta["t_center"] = t0
    return t, y, meta
