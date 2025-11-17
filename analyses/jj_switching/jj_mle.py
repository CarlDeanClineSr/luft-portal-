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

def mle_foam_fraction(I_sw_A: np.ndarray, Ic_A: float, ramp_Aps: float) -> JJResult:
    """
    Minimal estimator: treat foam as a mean shift parameter on I_sw.
    I_sw ~ Normal(mu0 + k f, sigma0). Estimate f by linear regression.
    This is a scaffold; replace with full switching-rate likelihood later.
    """
    x = np.ones_like(I_sw_A)
    y = I_sw_A

    # Estimate baseline mean and std from data (robust could be used)
    mu_emp = float(np.mean(y))
    sigma_emp = float(np.std(y, ddof=1))

    # Calibrate k: sensitivity coefficient (simplified)
    k = -0.08 * Ic_A

    # Linearized MLE for f: f_hat ≈ (mu_emp - mu0) / k; assume mu0≈0.92*Ic
    mu0 = 0.92 * Ic_A
    f_hat = (mu_emp - mu0) / k if k != 0 else 0.0

    # Fisher-like uncertainty: sigma_f ≈ sigma_mu / |k|
    sigma_mu = sigma_emp / np.sqrt(len(y))
    sigma_f = abs(sigma_mu / k) if k != 0 else np.inf

    return JJResult(f_hat=f_hat, sigma_f=sigma_f, mu0=mu0, sigma0=sigma_emp, n=len(y))

if __name__ == "__main__":
    # Smoke test with synthetic data
    from jj_synth import synth_switching_currents
    d = synth_switching_currents(foam_f=-0.05)
    res = mle_foam_fraction(d["I_sw_A"], d["Ic_A"], d["ramp_Aps"][0])
    print(res)
