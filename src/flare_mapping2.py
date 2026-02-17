#!/usr/bin/env python3
"""
flare_mapping.py

Map GOES proton flux Φ(t) to foam parameter f(t) and (optionally) to effective mass m_eq(t),
following the LUFT flare foam pipeline sketched in New Text Document (149).txt.

Equations (from relay):
  f(t) = f0 + alpha * (Φ(t) / Φ_ref)
  m_eq(t) = m_eq0 * (1 - beta * ΔB(t) / B0)
"""

from __future__ import annotations

import pandas as pd


def map_flux_to_foam(
    phi: pd.Series,
    phi_ref: float = 100.0,
    f0: float = 0.0,
    alpha: float = -0.05,
) -> pd.Series:
    """
    Map proton flux Φ(t) [pfu] to foam parameter f(t).

    Parameters
    ----------
    phi : Series
        Proton flux Φ(t) in pfu, indexed by time.
    phi_ref : float
        Reference flux in pfu; typical ~100 pfu.
    f0 : float
        Baseline foam offset.
    alpha : float
        Scaling coefficient; choose so that peak Φ/Φ_ref gives f ≈ -0.05.
        (Default alpha=-0.05 is a placeholder; tune per event.)

    Returns
    -------
    f : Series
        Foam parameter f(t).
    """
    phi_norm = phi / float(phi_ref)
    f = f0 + alpha * phi_norm
    f.name = "f_foam"
    return f


def map_dB_to_meq(
    dB: pd.Series,
    meq0: float = 1.0,
    B0: float = 1.0,
    beta: float = 0.1,
) -> pd.Series:
    """
    Map geomagnetic perturbation ΔB(t) to effective mass m_eq(t).

    Parameters
    ----------
    dB : Series
        ΔB(t) [same units as B0], indexed by time.
    meq0 : float
        Baseline effective mass (arbitrary units).
    B0 : float
        Baseline field magnitude (same units as dB).
    beta : float
        Dimensionless coefficient chosen so peak ΔB/B0 yields ~5–15% reduction.

    Returns
    -------
    meq : Series
        Effective mass m_eq(t).
    """
    ratio = dB / float(B0)
    meq = meq0 * (1.0 - beta * ratio)
    meq.name = "m_eq"
    return meq
