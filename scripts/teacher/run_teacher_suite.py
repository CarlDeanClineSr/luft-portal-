#!/usr/bin/env python3
"""
Teach-The-Engine: Run teacher suite across all datasets.
Discovers files from curriculum-defined inputs and evaluates them against signatures.
Produces aggregate JSON index and markdown report.
"""
import json
import sys
from pathlib import Path

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.teacher.evaluate_dataset import evaluate


def main():
    """Run the teacher suite against all discovered datasets."""
    curriculum_path = Path("data/teacher/curriculum.yaml")
    if not curriculum_path.exists():
        print(f"Error: Curriculum file not found at {curriculum_path}")
        sys.exit(1)
    
    curriculum = yaml.safe_load(curriculum_path.read_text())
    outputs = []
    
    # Discover files from all configured input paths
    for inp in curriculum.get("inputs", []):
        base = Path(inp["path"])
        if not base.exists():
            print(f"Info: Input path {base} does not exist, skipping")
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in [".csv", ".json"]:
                try:
                    res = evaluate(str(p), curriculum)
                except Exception as e:
                    res = {"file": str(p), "status": "error", "error": str(e)}
                outputs.append(res)

    # Write aggregate index
    out_dir = Path("results/teacher")
    fig_dir = Path("figures/teacher")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    idx = {"count": len(outputs), "items": outputs}
    (out_dir / "aggregate_index.json").write_text(json.dumps(idx, indent=2))

    # Build markdown report
    lines = [
        "# Teach-The-Engine Daily Report\n",
        "Autonomic signature checks across vault datasets.\n",
        f"\n**Total files scanned:** {len(outputs)}\n",
        f"**Analyzed:** {sum(1 for o in outputs if o.get('status') == 'analyzed')}\n",
        f"**Skipped:** {sum(1 for o in outputs if o.get('status') == 'skipped')}\n",
        f"**Errors:** {sum(1 for o in outputs if o.get('status') == 'error')}\n"
    ]
    
    for it in outputs:
        lines.append(f"\n## {it['file']}\n")
        lines.append(f"- **status:** {it.get('status')}")
        if it.get('reason'):
            lines.append(f"  - reason: {it.get('reason')}")
        if it.get('error'):
            lines.append(f"  - error: {it.get('error')}")
        for k in ["chi_boundary", "fractal_regulator", "binary_harmonics", "electroweak_bridge", "whistler_gaps"]:
            if k in it:
                lines.append(f"- **{k}:** {json.dumps(it[k])}")
    
    report_path = Path(curriculum["output"]["report_md"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))
    
    print(f"Wrote {report_path} and {out_dir / 'aggregate_index.json'}")
    print(f"Total files: {len(outputs)}, Analyzed: {sum(1 for o in outputs if o.get('status') == 'analyzed')}")


if __name__ == "__main__":
    main()
