#!/usr/bin/env python3
"""
jj_gamma_model.py

Compute Josephson escape rate Γ(t) and ln Γ(t) from foam parameter f(t),
as described in the LUFT flare foam pipeline (relay 149).

Core relation:
  Γ(t) = Γ0 * exp[-(B0/2 + κ) * f(t)]
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def gamma_from_foam(
    f: pd.Series,
    gamma0: float = 1.0,
    B0: float = 17.0,
    kappa: float = 0.0,
) -> pd.DataFrame:
    """
    Compute Γ(t) and ln Γ(t) from foam parameter f(t).

    Parameters
    ----------
    f : Series
        Foam parameter f(t), indexed by time.
    gamma0 : float
        Baseline escape rate Γ0 (arbitrary units).
    B0 : float
        Baseline WKB exponent (e.g. ~17).
    kappa : float
        Additional foam sensitivity term (0.01–0.5 range for sweeps).

    Returns
    -------
    df : DataFrame
        Columns:
          - 'Gamma' : Γ(t)
          - 'ln_Gamma' : ln Γ(t)
    """
    S = (B0 / 2.0) + kappa
    ln_gamma = np.log(gamma0) - S * f.values
    gamma = np.exp(ln_gamma)

    df = pd.DataFrame(
        {
            "Gamma": gamma,
            "ln_Gamma": ln_gamma,
        },
        index=f.index,
    )
    return df
