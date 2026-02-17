from pathlib import Path

from tools.validate_chi_repairs import (
    CHI_CAP,
    load_repairs,
    run_all_validations,
    validate_newton_repair,
)


def test_newton_repair_percent_delta():
    payload = load_repairs(Path(__file__).parent.parent)
    result = validate_newton_repair(payload["repairs"])
    assert result.status == "PASS"
    assert result.details["percent_delta"] < 0


def test_run_all_validations_passes():
    summary = run_all_validations(Path(__file__).parent.parent)
    assert summary["chi_cap"] == CHI_CAP
    assert summary["status"] == "PASS"
    assert all(r["status"] == "PASS" for r in summary["results"])
