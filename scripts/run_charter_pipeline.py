from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from analyses.common.io import ensure_dir, save_json
from analyses.jj_switching.jj_synth import JJSynthConfig, synth_switching_currents, save_synth_csv
from analyses.jj_switching.jj_mle import mle_foam_fraction
from analyses.desi_drift.desi_synth import synth_desi_residuals, save_residuals_csv
from analyses.desi_drift.desi_chi_bound import fit_sinusoid_bound
from analyses.resonance_7468.synth_tri_site import synth_site_series, write_site_csv
from analyses.resonance_7468.pipeline import lomb_scargle_site, cross_site_phase_coherence

def run_jj():
    print("== JJ foam auditor (synthetic) ==")
    cfg = JJSynthConfig(foam_f=-0.05)
    payload = synth_switching_currents(cfg)
    out_csv = Path("data/synthetic/jj/jj_I_sw_synth.csv")
    save_synth_csv(payload, out_csv)
    df = pd.read_csv(out_csv)
    res = mle_foam_fraction(df["I_sw_A"].to_numpy(), Ic_A=cfg.Ic_A)
    accept = res.sigma_f <= 0.015
    print(f"f_hat={res.f_hat:.4f}  sigma_f={res.sigma_f:.4f}  N={res.n}  ACCEPT={accept}")
    save_json("results/charter/jj_result.json", res.__dict__)
    return accept

def run_desi():
    print("== DESI Λ drift bound (synthetic) ==")
    t, y = synth_desi_residuals(n=500, hours=24.0, omega_hz=1e-4, chi_true=0.008, noise=0.01)
    out_csv = Path("data/synthetic/desi/desi_residuals_synth.csv")
    save_residuals_csv(t, y, out_csv)
    cb = fit_sinusoid_bound(t, y, omega_hz=1e-4)
    accept = cb.chi_95 < 0.01
    print(f"chi_hat={cb.chi_hat:.4f}  chi_95={cb.chi_95:.4f}  N={cb.n}  ACCEPT={accept}")
    save_json("results/charter/desi_bound.json", cb.__dict__)
    return accept

def run_resonance():
    print("== 7,468 Hz resonance (synthetic tri-site) ==")
    f0 = 7468.0
    n = 5000
    times_list = []
    values_list = []
    for seed in [1,2,3]:
        t, x = synth_site_series(n=n, f0_hz=f0, amp=1.0, noise=1.0, seed=seed)
        write_site_csv(t, x, f"data/synthetic/7468/site{seed}.csv")
        times_list.append(t)
        values_list.append(x)
    # Simple per-site LS over a narrow grid
    import numpy as np
    grid = np.linspace(f0-10.0, f0+10.0, 2000)
    site_accept = True
    faps = []
    for t, x in zip(times_list, values_list):
        sr = lomb_scargle_site(t, x, grid)
        print(f"site peak={sr.peak_freq_hz:.3f} Hz  fap={sr.fap:.3e}")
        faps.append(sr.fap)
        site_accept &= (sr.fap < 0.01)
    # Coherence
    from analyses.resonance_7468.pipeline import cross_site_phase_coherence
    coh = cross_site_phase_coherence(times_list, values_list, f0)
    accept = site_accept and (coh.C > 0.8) and (coh.snr_post_rfi >= 5.0)
    print(f"C={coh.C:.3f}  SNR_post_RFI={coh.snr_post_rfi:.2f}  ACCEPT={accept}")
    save_json("results/charter/7468_summary.json", {
        "faps": faps, "C": coh.C, "snr_post_rfi": coh.snr_post_rfi, "accept": accept
    })
    return accept

if __name__ == "__main__":
    ensure_dir("results/charter")
    ok_jj = run_jj()
    ok_desi = run_desi()
    try:
        ok_7468 = run_resonance()
    except Exception as e:
        ok_7468 = False
        print("Resonance check skipped (requires astropy):", e)
    print("\n=== Summary ===")
    print(f"JJ:   {'PASS' if ok_jj else 'FAIL'}")
    print(f"DESI: {'PASS' if ok_desi else 'FAIL'}")
    print(f"7468: {'PASS' if ok_7468 else 'SKIP/FAIL'}")
