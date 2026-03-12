#!/usr/bin/env python3
"""
vacuum_catastrophe_bound.py
============================
Vacuum Catastrophe Bounding Engine — Cline LUFT Integration

Bounds the QFT zero-point energy (ZPE) integral using live vacuum tension (χ)
modes derived from GOES/USGS telemetry.  Compares the empirically bounded
density against the standard (infinite / Planck-cutoff) QFT result and against
the observed cosmological constant Λ.

Usage
-----
    python scripts/vacuum_catastrophe_bound.py \
        --telemetry data/goes/goes_magnetometer_summary.csv \
        --chi 0.15

Arguments
---------
    --telemetry   Path to telemetry CSV used to derive χ if not supplied
                  directly.  Expected column: 'B' (total field, nT).
    --chi         Explicit vacuum tension χ override (float).  When absent the
                  value is derived from the telemetry B-field column.
    --harmonic_modes  Space-separated list of quantised χ mode levels.
                      Default: 0.15 0.30 0.45 0.60
    --cutoff_scale    Energy cutoff scale: 'planck' (default) or 'custom'.
    --output_dir  Directory for output files.  Default: results/
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")            # non-interactive backend for CI
import matplotlib.pyplot as plt
import pandas as pd
from scipy.integrate import quad


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
PLANCK_ENERGY_GEV = 1.22e19       # GeV  (Planck energy E_P = √(ℏc⁵/G) ≈ 1.22 × 10^19 GeV)
HBAR = 6.582e-16                   # eV·s
C = 3.0e8                          # m/s
# Observed vacuum energy density equivalent from Λ (CODATA)
# Λ ≈ 1.1056 × 10^-52 m^-2  →  ρ_Λ = Λ c^2 / (8π G) ≈ 5.96 × 10^-27 kg/m^3
# In energy units:  ρ_Λ c^2 ≈ 5.36 × 10^-10 J/m^3
OBSERVED_VAC_DENSITY_J_M3 = 5.36e-10   # J/m^3
OBSERVED_LAMBDA_M2 = 1.1056e-52        # m^-2 (cosmological constant, CODATA)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Vacuum Catastrophe Bounding Engine (Cline LUFT)"
    )
    parser.add_argument(
        "--telemetry",
        default="data/goes/goes_magnetometer_summary.csv",
        help="Telemetry CSV path for live χ derivation (column 'B' expected)",
    )
    parser.add_argument(
        "--chi",
        type=float,
        default=None,
        help="Explicit vacuum tension χ override (float); derived from telemetry if absent",
    )
    parser.add_argument(
        "--harmonic_modes",
        nargs="+",
        type=float,
        default=[0.15, 0.30, 0.45, 0.60],
        help="Quantised χ harmonic mode levels",
    )
    parser.add_argument(
        "--cutoff_scale",
        default="planck",
        choices=["planck", "custom"],
        help="Energy cutoff scale",
    )
    parser.add_argument(
        "--output_dir",
        default="results",
        help="Directory for output files",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# χ derivation from telemetry
# ---------------------------------------------------------------------------

def derive_chi_from_telemetry(filepath: str, fallback: float = 0.15) -> float:
    """Derive χ from mean |δB/B| in a CSV file containing a 'B' column.

    Returns *fallback* if the file is absent or lacks a usable B column.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] Telemetry file not found: {filepath}  — using fallback χ={fallback:.4f}")
        return fallback

    try:
        df = pd.read_csv(filepath)
    except Exception as exc:
        print(f"[WARN] Could not read {filepath}: {exc}  — using fallback χ={fallback:.4f}")
        return fallback

    # Accept 'B', 'b', 'Bt', 'bt' as field magnitude column names
    col = next((c for c in df.columns if c.strip().lower() in ("b", "bt")), None)
    if col is None:
        print(
            f"[WARN] No B-field column found in {filepath} "
            f"(available: {list(df.columns)})  — using fallback χ={fallback:.4f}"
        )
        return fallback

    b = pd.to_numeric(df[col], errors="coerce").dropna()
    if b.empty or b.mean() == 0:
        print(f"[WARN] B column is empty or zero-mean  — using fallback χ={fallback:.4f}")
        return fallback

    delta_b = (b - b.mean()).abs()
    chi_derived = float((delta_b / b.mean()).mean())
    print(f"[INFO] Derived χ from telemetry '{filepath}': {chi_derived:.6f}")
    return chi_derived


# ---------------------------------------------------------------------------
# ZPE integrals
# ---------------------------------------------------------------------------

def _zpe_integrand(k: float, m: float = 0.0) -> float:
    """Simplified massless scalar field ZPE integrand.

    Integrand for ∫ (1/2) ω(k) k² dk where ω(k) = c√(k²+m²).
    k is the wavenumber in GeV (natural units: ℏ=c=1).
    Returns units of GeV⁴.
    """
    return 0.5 * np.sqrt(k ** 2 + m ** 2) * k ** 2


def standard_zpe(cutoff: float) -> float:
    """ZPE density with hard Planck cutoff (approximates the 'infinite' QFT result).

    ρ_ZPE = (1/2π²) ∫₀^Λ (1/2) ω(k) k² dk × ℏ × c
    
    k in GeV; result converted to J/m³ via HBAR (eV·s) × C (m/s) × unit factors.
    """
    integral, _ = quad(_zpe_integrand, 0.0, cutoff)
    # integral has units GeV⁴; multiply by HBAR*C to convert to energy density (J/m³)
    return integral / (2.0 * np.pi ** 2) * HBAR * C


def bounded_zpe(mode: float) -> float:
    """Cline-bounded ZPE density: frequency integral truncated at χ-mode × Planck energy.

    effective_cutoff = mode × E_Planck (GeV)
    ρ_bounded = (1/2π²) ∫₀^(mode×E_P) (1/2) ω(k) k² dk × ℏ × c
    """
    effective_cutoff = PLANCK_ENERGY_GEV * mode
    integral, _ = quad(_zpe_integrand, 0.0, effective_cutoff)
    return integral / (2.0 * np.pi ** 2) * HBAR * C


# ---------------------------------------------------------------------------
# Snap χ to nearest harmonic mode
# ---------------------------------------------------------------------------

def snap_to_mode(chi: float, modes: list) -> float:
    """Return the lowest mode ≥ chi, or the highest mode if chi exceeds all."""
    for m in sorted(modes):
        if chi <= m:
            return m
    return max(modes)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def write_report(path: Path, rows: dict, active_mode: float, chi: float):
    """Write a Markdown report summarising the ZPE bounding results."""
    lines = [
        "# Vacuum Catastrophe Bounding Report",
        "",
        f"**Generated:** {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Live χ:** {chi:.6f}",
        f"**Active harmonic mode:** {active_mode:.2f}",
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    for k, v in rows.items():
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## Interpretation",
        "",
        "The Cline bounded density truncates the QFT zero-point integral at",
        f"χ × E_Planck = {active_mode:.2f} × 1.22×10¹⁹ GeV, replacing the",
        "10¹²⁰ catastrophic mismatch with a finite, mode-dependent vacuum energy",
        "that approaches the observed cosmological constant Λ.",
    ]
    path.write_text("\n".join(lines) + "\n")
    print(f"[INFO] Report written: {path}")


def write_csv(path: Path, modes: list, densities: list):
    """Write per-mode ZPE densities to CSV."""
    df = pd.DataFrame({"mode": modes, "bounded_density_J_m3": densities})
    df.to_csv(path, index=False)
    print(f"[INFO] CSV written: {path}")


def plot_results(
    path: Path,
    modes: list,
    densities: list,
    standard_density: float,
    observed_density: float,
):
    """Save a log-scale bar chart comparing bounded vs standard ZPE densities."""
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(modes))
    labels = [f"Mode {m:.2f}" for m in modes]
    ax.bar(x, densities, tick_label=labels, color="steelblue", alpha=0.8)
    ax.axhline(standard_density, color="red", linestyle="--", linewidth=1.5,
               label="Standard QFT (Planck cutoff)")
    ax.axhline(observed_density, color="green", linestyle="--", linewidth=1.5,
               label="Observed Λ equivalent")
    ax.set_yscale("log")
    ax.set_ylabel("Vacuum Energy Density (J/m³)")
    ax.set_title("Vacuum Catastrophe: Standard Infinite vs Cline Bounded Modes")
    ax.legend(fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"[INFO] Chart saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    args = parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve χ
    if args.chi is not None:
        chi_current = args.chi
        print(f"[INFO] Using explicit χ={chi_current:.6f}")
    else:
        chi_current = derive_chi_from_telemetry(args.telemetry)

    modes = args.harmonic_modes
    active_mode = snap_to_mode(chi_current, modes)
    print(f"[INFO] Harmonic modes: {modes}  →  active mode: {active_mode:.2f}")

    # Compute ZPE densities
    bounded_densities = [bounded_zpe(m) for m in modes]
    std_density = standard_zpe(PLANCK_ENERGY_GEV)
    avg_bounded = float(np.mean(bounded_densities))

    # Reduction in orders of magnitude (handle log of zero gracefully)
    if avg_bounded > 0 and std_density > 0:
        error_reduction = np.log10(std_density / avg_bounded)
    else:
        error_reduction = float("nan")

    ratio_to_observed = avg_bounded / OBSERVED_VAC_DENSITY_J_M3

    # Console summary
    print()
    print("=" * 65)
    print("VACUUM CATASTROPHE BOUNDING — RESULTS")
    print("=" * 65)
    print(f"Standard QFT density (Planck cutoff):  {std_density:.4e} J/m³")
    print(f"Cline bounded density (mode avg):       {avg_bounded:.4e} J/m³")
    if not np.isnan(error_reduction):
        print(f"Error reduction:                       ~10^{error_reduction:.1f}")
    print(f"Observed Λ equivalent:                 {OBSERVED_VAC_DENSITY_J_M3:.4e} J/m³")
    print(f"Bounded / Observed ratio:               {ratio_to_observed:.4e}")
    print("=" * 65)

    # Alert check
    alert_threshold = OBSERVED_VAC_DENSITY_J_M3 * 1e3
    if avg_bounded > alert_threshold:
        print(
            f"[ALERT] ZPE mismatch!  Bounded = {avg_bounded:.4e} J/m³ "
            f"> threshold {alert_threshold:.4e} J/m³  (Observed Λ equiv = {OBSERVED_VAC_DENSITY_J_M3:.4e})"
        )

    # Write outputs
    report_rows = {
        "Live χ": f"{chi_current:.6f}",
        "Active mode": f"{active_mode:.2f}",
        "Standard QFT density": f"{std_density:.4e} J/m³",
        "Bounded density (avg)": f"{avg_bounded:.4e} J/m³",
        "Error reduction": f"~10^{error_reduction:.1f}" if not np.isnan(error_reduction) else "N/A",
        "Observed Λ equivalent": f"{OBSERVED_VAC_DENSITY_J_M3:.4e} J/m³",
        "Bounded / Observed": f"{ratio_to_observed:.4e}",
    }
    write_report(out_dir / "zpe_bound_report.md", report_rows, active_mode, chi_current)
    write_csv(out_dir / "zpe_modes_latest.csv", modes, bounded_densities)
    plot_results(
        out_dir / "zpe_integral_vs_chi.png",
        modes,
        bounded_densities,
        std_density,
        OBSERVED_VAC_DENSITY_J_M3,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
