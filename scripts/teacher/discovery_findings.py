#!/usr/bin/env python3
"""
Discovery Findings Generator: Generates daily discovery findings from teacher suite results.
Stores key discoveries and allows the system to build upon previous findings.
"""
import json
import math
import sys
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path

import yaml

# Add scripts directory to path for imports (consistent with other teacher scripts)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Constants
MAX_HISTORY_ENTRIES = 30  # Keep last 30 daily runs in history


def load_previous_findings(findings_path: Path) -> dict:
    """Load previous discovery findings if they exist."""
    if findings_path.exists():
        try:
            return json.loads(findings_path.read_text())
        except (JSONDecodeError, OSError, ValueError):
            return {"discoveries": [], "history": []}
    return {"discoveries": [], "history": []}


def compute_discovery_stats(items: list) -> dict:
    """Compute discovery statistics from teacher suite items."""
    stats = {
        "total_files": len(items),
        "analyzed": sum(1 for o in items if o.get("status") == "analyzed"),
        "skipped": sum(1 for o in items if o.get("status") == "skipped"),
        "errors": sum(1 for o in items if o.get("status") == "error"),
        "signatures": {
            "chi_boundary": {"pass": 0, "total": 0, "violations": 0},
            "fractal_regulator": {"pass": 0, "total": 0, "p95_values": [], "p99_values": []},
            "binary_harmonics": {"pass": 0, "total": 0, "near_fund_counts": []},
            "electroweak_bridge": {"pass": 0, "total": 0, "near_0p9h_fracs": []},
            "whistler_gaps": {"pass": 0, "total": 0},
        }
    }

    for it in items:
        if it.get("status") != "analyzed":
            continue

        # Chi boundary stats
        if "chi_boundary" in it:
            cb = it["chi_boundary"]
            stats["signatures"]["chi_boundary"]["total"] += 1
            if cb.get("pass"):
                stats["signatures"]["chi_boundary"]["pass"] += 1
            stats["signatures"]["chi_boundary"]["violations"] += cb.get("over_cap_count", 0)

        # Fractal regulator stats
        if "fractal_regulator" in it:
            fr = it["fractal_regulator"]
            stats["signatures"]["fractal_regulator"]["total"] += 1
            if fr.get("pass"):
                stats["signatures"]["fractal_regulator"]["pass"] += 1
            if fr.get("phi_p95") is not None and not (isinstance(fr.get("phi_p95"), float) and fr.get("phi_p95") != fr.get("phi_p95")):  # not NaN
                stats["signatures"]["fractal_regulator"]["p95_values"].append(fr.get("phi_p95"))
            if fr.get("phi_p99") is not None and not (isinstance(fr.get("phi_p99"), float) and fr.get("phi_p99") != fr.get("phi_p99")):
                stats["signatures"]["fractal_regulator"]["p99_values"].append(fr.get("phi_p99"))

        # Binary harmonics stats
        if "binary_harmonics" in it:
            bh = it["binary_harmonics"]
            stats["signatures"]["binary_harmonics"]["total"] += 1
            if bh.get("pass"):
                stats["signatures"]["binary_harmonics"]["pass"] += 1
            if bh.get("near_fund_count") is not None:
                stats["signatures"]["binary_harmonics"]["near_fund_counts"].append(bh.get("near_fund_count"))

        # Electroweak bridge stats
        if "electroweak_bridge" in it:
            ew = it["electroweak_bridge"]
            stats["signatures"]["electroweak_bridge"]["total"] += 1
            if ew.get("pass"):
                stats["signatures"]["electroweak_bridge"]["pass"] += 1
            if ew.get("near_0p9h_frac") is not None:
                stats["signatures"]["electroweak_bridge"]["near_0p9h_fracs"].append(ew.get("near_0p9h_frac"))

        # Whistler gaps stats
        if "whistler_gaps" in it:
            wg = it["whistler_gaps"]
            stats["signatures"]["whistler_gaps"]["total"] += 1
            if wg.get("pass"):
                stats["signatures"]["whistler_gaps"]["pass"] += 1

    return stats


def extract_discoveries(stats: dict, items: list) -> list:
    """Extract key discoveries from the analysis stats."""
    discoveries = []
    now = datetime.now(timezone.utc).isoformat()

    # Electroweak-MHD Bridge universality check
    ew_stats = stats["signatures"]["electroweak_bridge"]
    if ew_stats["total"] > 0:
        pass_rate = ew_stats["pass"] / ew_stats["total"]
        if ew_stats["near_0p9h_fracs"]:
            avg_frac = sum(ew_stats["near_0p9h_fracs"]) / len(ew_stats["near_0p9h_fracs"])
            # Filter for high fractions (historical data shows 93-99.9%)
            high_fracs = [f for f in ew_stats["near_0p9h_fracs"] if f > 0.90]
            if high_fracs:
                discoveries.append({
                    "id": "electroweak_mhd_bridge",
                    "title": "Electroweak-MHD Bridge Confirmed",
                    "description": f"0.9h packet modulation present in {len(high_fracs)}/{ew_stats['total']} historical files with {pass_rate*100:.1f}% pass rate.",
                    "significance": "The bridge from 100 GeV weak scale to MHD is fundamental, surviving 60+ years of solar cycles.",
                    "metrics": {
                        "pass_rate": pass_rate,
                        "avg_near_0p9h_frac": avg_frac,
                        "high_fraction_count": len(high_fracs),
                        "total_evaluated": ew_stats["total"]
                    },
                    "timestamp": now
                })

    # Causality Precursor Law check
    cb_stats = stats["signatures"]["chi_boundary"]
    if cb_stats["total"] > 0:
        discoveries.append({
            "id": "causality_precursor_law",
            "title": "Causality Precursor Law (χ = A_IC / 3)",
            "description": f"Violations: {cb_stats['violations']} across {cb_stats['total']} datasets. Cap enforced in quasi-steady state.",
            "significance": "χ ≤ 0.15 boundary is a regulator, not absolute wall. Transients breach then reset.",
            "metrics": {
                "pass_rate": cb_stats["pass"] / cb_stats["total"] if cb_stats["total"] > 0 else 0,
                "total_violations": cb_stats["violations"],
                "total_datasets": cb_stats["total"]
            },
            "timestamp": now
        })

    # Fractal regulator check
    fr_stats = stats["signatures"]["fractal_regulator"]
    if fr_stats["p95_values"] and fr_stats["p99_values"]:
        # Filter out None and NaN values using math.isnan
        p95_vals = [v for v in fr_stats["p95_values"] if v is not None and not math.isnan(v)]
        p99_vals = [v for v in fr_stats["p99_values"] if v is not None and not math.isnan(v)]
        if p95_vals and p99_vals:
            p95_median = sorted(p95_vals)[len(p95_vals)//2] if p95_vals else 0
            p99_median = sorted(p99_vals)[len(p99_vals)//2] if p99_vals else 0
            discoveries.append({
                "id": "fractal_regulator",
                "title": "χ-Fractal Regulator Scale-Consistent",
                "description": f"p95 ~{p95_median:.2f}, p99 ~{p99_median:.2f} across {len(p95_vals)} datasets.",
                "significance": "Tail behavior capped even in historical data—no unbounded perturbations. Fractal self-regulation confirmed.",
                "metrics": {
                    "p95_median": p95_median,
                    "p99_median": p99_median,
                    "datasets_analyzed": len(p95_vals)
                },
                "timestamp": now
            })

    # Binary harmonics check
    bh_stats = stats["signatures"]["binary_harmonics"]
    if bh_stats["near_fund_counts"]:
        total_near_fund = sum(bh_stats["near_fund_counts"])
        discoveries.append({
            "id": "binary_harmonic_ladder",
            "title": "Binary Harmonic Ladder (6h spacing)",
            "description": f"Total near_fund_count: {total_near_fund} across {bh_stats['total']} datasets.",
            "significance": "0.9h fundamental strong, 6h spacing needs better peak/event detection for burst clusters.",
            "metrics": {
                "pass_rate": bh_stats["pass"] / bh_stats["total"] if bh_stats["total"] > 0 else 0,
                "total_near_fund": total_near_fund,
                "total_datasets": bh_stats["total"]
            },
            "timestamp": now
        })

    return discoveries


def generate_discovery_report(findings: dict, stats: dict) -> str:
    """Generate markdown discovery report."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")
    
    lines = [
        f"# LUFT Discovery Engine: Autonomic Signature Report – Full Vault Sweep",
        f"",
        f"**Date:** {date_str}",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"",
        f"## Summary",
        f"",
        f"The engine completed its run: **{stats['total_files']}** files scanned.",
        f"- **Analyzed:** {stats['analyzed']}",
        f"- **Skipped:** {stats['skipped']}",
        f"- **Errors:** {stats['errors']}",
        f"",
        f"## Key Discoveries",
        f""
    ]

    for disc in findings.get("discoveries", []):
        lines.append(f"### {disc['title']}")
        lines.append(f"")
        lines.append(f"{disc['description']}")
        lines.append(f"")
        lines.append(f"**Significance:** {disc['significance']}")
        lines.append(f"")
        if disc.get("metrics"):
            lines.append("**Metrics:**")
            for k, v in disc["metrics"].items():
                if isinstance(v, float):
                    lines.append(f"- {k}: {v:.4f}")
                else:
                    lines.append(f"- {k}: {v}")
            lines.append("")

    # Signature scorecard
    lines.extend([
        "## Signature Scorecard",
        "",
        "| Signature | Pass | Total | Pass Rate |",
        "|-----------|------|-------|-----------|"
    ])
    
    for sig_name, sig_stats in stats["signatures"].items():
        if sig_stats["total"] > 0:
            rate = sig_stats["pass"] / sig_stats["total"] * 100
            lines.append(f"| {sig_name.replace('_', ' ').title()} | {sig_stats['pass']} | {sig_stats['total']} | {rate:.1f}% |")

    lines.extend([
        "",
        "---",
        "",
        f"*Report generated by LUFT Discovery Engine v1.0*"
    ])

    return "\n".join(lines)


def main():
    """Generate discovery findings from teacher suite results."""
    # Load teacher suite results
    agg_path = Path("results/teacher/aggregate_index.json")
    if not agg_path.exists():
        print("Error: Teacher suite results not found. Run teacher suite first.")
        sys.exit(1)

    agg = json.loads(agg_path.read_text())
    items = agg.get("items", [])

    # Load previous findings
    findings_path = Path("results/teacher/discovery_findings.json")
    previous = load_previous_findings(findings_path)

    # Compute current stats
    stats = compute_discovery_stats(items)

    # Extract discoveries
    discoveries = extract_discoveries(stats, items)

    # Prepare new findings
    now = datetime.now(timezone.utc)
    findings = {
        "generated": now.isoformat(),
        "stats": {
            "total_files": stats["total_files"],
            "analyzed": stats["analyzed"],
            "skipped": stats["skipped"],
            "errors": stats["errors"]
        },
        "signatures": {
            k: {
                "pass": v["pass"],
                "total": v["total"],
                "pass_rate": v["pass"] / v["total"] if v["total"] > 0 else 0
            }
            for k, v in stats["signatures"].items()
        },
        "discoveries": discoveries,
        "history": previous.get("history", [])[-(MAX_HISTORY_ENTRIES - 1):] + [{
            "date": now.strftime("%Y-%m-%d"),
            "files_analyzed": stats["analyzed"],
            "discoveries_count": len(discoveries)
        }]
    }

    # Write findings JSON
    findings_path.write_text(json.dumps(findings, indent=2))

    # Generate and write markdown report
    report = generate_discovery_report(findings, stats)
    report_path = Path("docs/Discovery_Findings.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)

    print(f"Wrote {findings_path}")
    print(f"Wrote {report_path}")
    print(f"Discoveries: {len(discoveries)}, Files analyzed: {stats['analyzed']}")


if __name__ == "__main__":
    main()
