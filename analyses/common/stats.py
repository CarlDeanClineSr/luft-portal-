from __future__ import annotations
import numpy as np

def bonferroni_p(p_single: float, m_tests: int) -> float:
    return min(1.0, p_single * max(m_tests, 1))

def coh_threshold_ok(C: float, min_C: float = 0.8) -> bool:
    return C >= min_C
