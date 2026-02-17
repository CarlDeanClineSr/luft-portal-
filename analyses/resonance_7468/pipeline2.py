from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

try:
    from astropy.timeseries import LombScargle
except Exception:
    LombScargle = None

@dataclass
class SiteResult:
    peak_freq_hz: float
    power: float
    fap: float

@dataclass
class CoherenceResult:
    C: float
    snr_post_rfi: float

def lomb_scargle_site(times_s: np.ndarray, values: np.ndarray, freq_grid_hz: np.ndarray) -> SiteResult:
    if LombScargle is None:
        raise RuntimeError("astropy is required for Lomb-Scargle")
    ls = LombScargle(times_s, values)
    power = ls.power(freq_grid_hz)
    idx = int(np.argmax(power))
    f_peak = float(freq_grid_hz[idx])
    fap = float(ls.false_alarm_probability(power[idx]))
    return SiteResult(peak_freq_hz=f_peak, power=float(power[idx]), fap=fap)

def cross_site_phase_coherence(times_s_list: List[np.ndarray], values_list: List[np.ndarray], freq_hz: float) -> CoherenceResult:
    phases = []
    amps = []
    for t, x in zip(times_s_list, values_list):
        phi = 2*np.pi*freq_hz * t
        c = np.exp(-1j * phi)
        A = np.vdot(c, x) / len(x)
        phases.append(np.angle(A))
        amps.append(np.abs(A))
    vec = np.mean(np.exp(1j * np.array(phases)))
    C = float(np.abs(vec))
    snr_post_rfi = float(np.mean(amps) / (np.std(amps) + 1e-12))
    return CoherenceResult(C=C, snr_post_rfi=snr_post_rfi)

def rfi_subtract(values: np.ndarray, templates: List[np.ndarray]) -> np.ndarray:
    if not templates:
        return values
    X = np.column_stack(templates)
    beta, *_ = np.linalg.lstsq(X, values, rcond=None)
    return values - X @ beta
