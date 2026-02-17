from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class JJResult:
    f_hat: float
    sigma_f: float
    mu0: float
    sigma0: float
    n: int

def mle_foam_fraction(I_sw_A: np.ndarray, Ic_A: float) -> JJResult:
    """
    Minimal estimator (scaffold): treat foam as a mean shift parameter on I_sw.
    Replace with full switching-rate likelihood in production.
    """
    mu_emp = float(np.mean(I_sw_A))
    sigma_emp = float(np.std(I_sw_A, ddof=1))
    mu0 = 0.92 * Ic_A
    k = -0.08 * Ic_A if Ic_A != 0 else 0.0
    f_hat = (mu_emp - mu0) / k if k != 0 else 0.0
    sigma_mu = sigma_emp / np.sqrt(max(len(I_sw_A), 1))
    sigma_f = abs(sigma_mu / k) if k != 0 else float("inf")
    return JJResult(f_hat=f_hat, sigma_f=sigma_f, mu0=mu0, sigma0=sigma_emp, n=len(I_sw_A))

if __name__ == "__main__":
    # Smoke test
    import pandas as pd
    df = pd.read_csv("data/synthetic/jj/jj_I_sw_synth.csv")
    res = mle_foam_fraction(df["I_sw_A"].to_numpy(), Ic_A=5e-8)
    print(res)
