from __future__ import annotations
import numpy as np

def synth_switching_currents(
    Ic_A: float = 5e-8,
    C_F: float = 5e-15,
    ramp_Aps: float = 2e-8,
    T_K: float = 50e-3,
    N_shots: int = 5000,
    foam_f: float = 0.0,
    seed: int | None = 42,
) -> dict:
    """
    Generate synthetic switching currents I_sw under a simple model.
    We emulate the exponential sensitivity via a small mean shift ~ k * f.
    This is a scaffold for pipeline shakedown; replace with full WKB later.

    Returns dict with arrays for I_sw_A, T_K, ramp_Aps and metadata.
    """
    rng = np.random.default_rng(seed)
    # Base mean as a fraction of Ic (toy), std ~ few %
    base_mu = 0.92 * Ic_A
    base_sigma = 0.02 * Ic_A

    # Exponential sensitivity approximated as linear mean shift for small |f|
    k = -0.08 * Ic_A  # tune to reproduce d ln Γ/df ~ -8.6 qualitatively
    mu = base_mu + k * foam_f
    I_sw = rng.normal(loc=mu, scale=base_sigma, size=N_shots)

    return {
        "I_sw_A": I_sw.astype(float),
        "T_K": np.full(N_shots, T_K, dtype=float),
        "ramp_Aps": np.full(N_shots, ramp_Aps, dtype=float),
        "Ic_A": Ic_A,
        "C_F": C_F,
        "foam_f": foam_f,
        "seed": seed,
    }
