#!/usr/bin/env python3
"""
Regime B QGP Capsule Generator
Proxies χ from reported limits in QGP papers (no raw time series needed).
Designed for papers like STAR QGP review (arXiv:2601.12977).
"""

import json
import os
from datetime import datetime


def generate_qgp_capsule(paper_id="2601.12977", t_max=287.0, t_avg=156.5,
                         v2_max=0.20, v2_avg=0.08, r_min=0.2, r_max=0.8):
    """
    Regime B: Compression capsule for QGP papers.
    Proxies χ from reported limits (no raw series needed).
    """
    print(f"\n>>> GENERATING REGIME B CAPSULE FOR {paper_id}...")

    # Proxies: χ = 1 - (Avg / Max) → higher = more compression/stress
    chi_t = 1 - (t_avg / t_max) if t_max > 0 else None
    chi_v = 1 - (v2_avg / v2_max) if v2_max > 0 else None
    chi_r = 1 - (r_min / r_max) if r_max > 0 else None

    capsule = {
        "metadata": {
            "paper_id": paper_id,
            "timestamp": datetime.utcnow().isoformat(),
            "regime": "micro-phase-boundary",
            "medium_state": "extreme_compression"
        },
        "extracted_limits": {
            "temperature_max_MeV": t_max,
            "temperature_avg_MeV": t_avg,
            "harmonic_v2_max": v2_max,
            "harmonic_v2_avg": v2_avg,
            "suppression_R_min": r_min,
            "suppression_R_max": r_max
        },
        "computed_chi_proxies": {
            "chi_T_thermal_stress": chi_t,
            "chi_v_harmonic_shear": chi_v,
            "chi_R_suppression_bias": chi_r
        },
        "mode_hits": {
            "above_0.15": any([v >= 0.15 for v in [chi_t, chi_v, chi_r] if v is not None]),
            "above_0.30": any([v >= 0.30 for v in [chi_t, chi_v, chi_r] if v is not None])
        }
    }

    os.makedirs("results/papers", exist_ok=True)
    filename = f"results/papers/qgp_star_{paper_id}_capsule.json"
    with open(filename, "w") as f:
        json.dump(capsule, f, indent=2)

    print(f"✅ CAPSULE SECURED: {filename}")
    print(f"   -> Thermal Chi (χ_T): {chi_t:.4f}" if chi_t is not None else "   No T data")
    print(f"   -> Harmonic Chi (χ_v): {chi_v:.4f}" if chi_v is not None else "   No v2 data")
    print(f"   -> Suppression Chi (χ_R): {chi_r:.4f}" if chi_r is not None else "   No R data")

    return capsule


if __name__ == "__main__":
    generate_qgp_capsule(
        t_max=287.0, t_avg=156.5,
        v2_max=0.20, v2_avg=0.08,
        r_min=0.2, r_max=0.8
    )
