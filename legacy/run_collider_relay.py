from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from analyses.collider.multiplicity_sim import NBParams, simulate_mixture
from analyses.collider.multiplicity_fit import fit_nb_mle, fit_mixture_nb

def main():
    outdir = Path("results/collider")
    outdir.mkdir(parents=True, exist_ok=True)

    # Synthetic demo (replace with real data loader)
    base = NBParams(8.0, 0.6)
    foam = NBParams(5.5, 0.55)
    sim = simulate_mixture(50000, base, foam, w=0.9, seed=7)
    M = sim["M_obs"]

    # Baseline NB
    fr = fit_nb_mle(M)

    # Mixture NB+NB'
    mix, ll1, bic1 = fit_mixture_nb(M)

    # Tail boost (M > M_ref)
    M_ref = sim["params"]["M_ref"]
    tail = M[M > M_ref]
    tail_boost = float(tail.mean()/np.mean(M[M > 0]) - 1.0) if len(tail) else 0.0

    # ΔBIC (baseline needs BIC0)
    bic0 = fr.bic
    delta_bic = float(bic0 - bic1)

    summary = {
        "baseline": {"k": fr.k, "p": fr.p, "bic": fr.bic},
        "mixture": mix,
        "delta_BIC": delta_bic,
        "tail_boost": tail_boost,
        "N": int(len(M)),
        "notes": "Synthetic demonstration; replace with real open-data counts.",
    }
    (outdir / "relay009_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
