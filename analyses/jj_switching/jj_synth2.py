from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from analyses.common.io import ensure_dir

@dataclass
class JJSynthConfig:
    Ic_A: float = 5e-8
    C_F: float = 5e-15
    ramp_Aps: float = 2e-8
    T_K: float = 50e-3
    N_shots: int = 5000
    foam_f: float = 0.0
    seed: int = 42

def synth_switching_currents(cfg: JJSynthConfig) -> dict:
    """
    Synthetic switching-current generator (scaffold).
    Exponential sensitivity emulated as a small mean shift in I_sw for |f|<<1.
    """
    rng = np.random.default_rng(cfg.seed)
    base_mu = 0.92 * cfg.Ic_A
    base_sigma = 0.02 * cfg.Ic_A
    k = -0.08 * cfg.Ic_A  # sensitivity proxy; negative slope for f<0 → higher rates
    mu = base_mu + k * cfg.foam_f
    I_sw = rng.normal(loc=mu, scale=base_sigma, size=cfg.N_shots)
    return {
        "I_sw_A": I_sw.astype(float),
        "T_K": np.full(cfg.N_shots, cfg.T_K, dtype=float),
        "ramp_Aps": np.full(cfg.N_shots, cfg.ramp_Aps, dtype=float),
        "Ic_A": cfg.Ic_A,
        "C_F": cfg.C_F,
        "foam_f": cfg.foam_f,
    }

def save_synth_csv(payload: dict, out_csv: str | Path) -> None:
    import pandas as pd
    ensure_dir(Path(out_csv).parent)
    df = pd.DataFrame({
        "shot_idx": np.arange(len(payload["I_sw_A"])),
        "I_sw_A": payload["I_sw_A"],
        "T_K": payload["T_K"],
        "ramp_Aps": payload["ramp_Aps"],
    })
    df.to_csv(out_csv, index=False)

if __name__ == "__main__":
    cfg = JJSynthConfig(foam_f=-0.05)
    data = synth_switching_currents(cfg)
    save_synth_csv(data, "data/synthetic/jj/jj_I_sw_synth.csv")
    print("Wrote data/synthetic/jj/jj_I_sw_synth.csv")
