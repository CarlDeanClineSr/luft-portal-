import importlib.util
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gravity_control_fixes.py"
spec = importlib.util.spec_from_file_location("gravity_control_fixes", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load gravity_control_fixes module from {MODULE_PATH}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CHI = module.CHI
run_pipeline = module.run_pipeline


def test_run_pipeline_creates_expected_outputs(tmp_path):
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 00:00",
                "2026-01-01 01:00",
                "2026-01-01 02:00",
                "2026-01-01 03:00",
            ],
            "chi_amplitude": [0.132, 0.134, 0.139, 0.145],
        }
    )

    input_path = tmp_path / "chart.csv"
    df.to_csv(input_path, index=False)

    result = run_pipeline(input_path, tmp_path)

    figures_dir = tmp_path / "figures"
    data_dir = tmp_path / "data"
    reports_dir = tmp_path / "reports"

    assert (figures_dir / "chi_amplitude_series.png").exists()
    assert (figures_dir / "bowing_effect.png").exists()
    assert (figures_dir / "periodic_table_shifts.png").exists()
    assert (data_dir / "physics_repairs.json").exists()
    assert (reports_dir / "physics_repairs_summary.md").exists()

    repairs = json.loads((data_dir / "physics_repairs.json").read_text())
    assert "Newton_Gravity" in repairs
    assert result["stats"]["violations"] == 0
    assert result["stats"]["mean"] < CHI
