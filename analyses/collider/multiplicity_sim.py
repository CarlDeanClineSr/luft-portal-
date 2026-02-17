from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class NBParams:
    k: float
    p: float

def rng_nb(n: int, k: float, p: float, seed: int | None = 0) -> np.ndarray:
    """
    Negative binomial (Poisson-gamma) sampler.
    k > 0 (shape), 0 < p < 1 (prob success). Mean = k*(1-p)/p
    """
    rng = np.random.default_rng(seed)
    # Gamma for Poisson rate: rate ~ Gamma(k, theta) with mean k*theta
    theta = (1 - p) / p
    lam = rng.gamma(shape=k, scale=theta, size=n)
    return rng.poisson(lam)

def simulate_mixture(n: int,
                     base: NBParams,
                     foam: NBParams,
                     w: float,
                     f: float = -0.05,
                     alpha: float = 0.1,
                     gamma: float = 0.05,
                     kappa: float = 10.0,
                     M_ref: float = 150.0,
                     seed: int = 42) -> dict:
    """
    Simulate multiplicities with an NB mixture and optional foam map.
    """
    rng = np.random.default_rng(seed)
    z = rng.uniform(size=n)
    # Component picks
    comp = (z > w).astype(int)
    # Draw raw counts
    M_base = rng_nb(n, base.k, base.p, seed=rng.integers(1e9))
    M_foam = rng_nb(n, foam.k, foam.p, seed=rng.integers(1e9))

    # Foam hierarchy map (applies to foam component only)
    # f_h = exp(alpha * log(M_raw / M_ref)) * f
    with np.errstate(divide="ignore"):
        fh = np.exp(alpha * np.log(np.maximum(M_foam, 1e-6) / M_ref)) * f
    # M_map = M_raw * (1 + gamma * f_h) * exp(-kappa * |f|)
    M_map = (M_foam.astype(float) *
             (1.0 + gamma * fh) *
             np.exp(-kappa * abs(f)))

    # Assemble observed counts
    M_obs = np.where(comp == 0, M_base.astype(float), M_map)
    # Round to counts and clip to >= 0
    M_obs = np.clip(np.rint(M_obs), 0, None).astype(int)

    return {
        "M_obs": M_obs,
        "comp": comp,
        "params": dict(base=base.__dict__, foam=foam.__dict__,
                       w=w, f=f, alpha=alpha, gamma=gamma, kappa=kappa, M_ref=M_ref),
    }

if __name__ == "__main__":
    base = NBParams(k=8.0, p=0.6)
    foam = NBParams(k=5.0, p=0.55)
    d = simulate_mixture(n=10000, base=base, foam=foam, w=0.85)
    M = d["M_obs"]
    tail = M[M > 150]
    print("N:", len(M), "tail N:", len(tail), "tail mean:", tail.mean() if len(tail) else 0.0)
