"""
Validation harness for χ-corrected physics repairs and periodic table exports.

Usage:
    python tools/validate_chi_repairs.py
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

CHI_CAP = 0.15
G_CONST = 6.67430e-11  # m^3 kg^-1 s^-2
BINDING_TOLERANCE = 0.01


@dataclass
class ValidationResult:
    id: str
    status: str
    details: Dict[str, object]

    def as_dict(self) -> Dict[str, object]:
        return {"id": self.id, "status": self.status, **self.details}


def load_repairs(base_path: Path | None = None) -> Dict[str, object]:
    base = base_path or Path(__file__).resolve().parent.parent
    with open(base / "data" / "chi_repairs" / "physics_repairs.json", "r", encoding="utf-8") as f:
        return json.load(f)


def validate_newton_repair(repairs: List[Dict[str, object]], chi_value: float = CHI_CAP) -> ValidationResult:
    entry = next((r for r in repairs if r.get("id") == "newton_gravity"), None)
    if entry is None:
        return ValidationResult(id="newton_gravity", status="FAIL", details={"reason": "missing entry"})

    tc = entry.get("test_case", {})
    chi = float(entry.get("chi_value", chi_value))
    try:
        m1 = float(tc["m1_kg"])
        m2 = float(tc["m2_kg"])
        r = float(tc["r_m"])
        expected_percent = float(tc["percent_change"])
    except (KeyError, TypeError, ValueError):
        return ValidationResult(id="newton_gravity", status="FAIL", details={"reason": "invalid test case"})

    f_original = G_CONST * m1 * m2 / (r ** 2)
    f_corrected = G_CONST * m1 * m2 / ((r * (1 + chi)) ** 2)
    percent_delta = (f_corrected / f_original - 1) * 100

    within_tolerance = abs(percent_delta - expected_percent) < 1.0
    status = "PASS" if within_tolerance and f_corrected < f_original else "FAIL"

    return ValidationResult(
        id="newton_gravity",
        status=status,
        details={
            "f_original": f_original,
            "f_corrected": f_corrected,
            "percent_delta": percent_delta,
        },
    )


def validate_periodic_table(base_path: Path | None = None, chi_value: float = CHI_CAP) -> ValidationResult:
    base = base_path or Path(__file__).resolve().parent.parent
    csv_path = base / "data" / "chi_repairs" / "periodic_table_chi.csv"

    mismatches: List[str] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                original = float(row["Original_Binding_eV"])
                corrected = float(row["Chi_Corrected_Binding_eV"])
            except (ValueError, KeyError):
                mismatches.append(row.get("Element", "unknown"))
                continue

            expected = original * (1 + chi_value)
            if abs((corrected - expected) / original) > BINDING_TOLERANCE:
                mismatches.append(row.get("Element", "unknown"))

    status = "PASS" if not mismatches else "FAIL"
    return ValidationResult(id="periodic_table_chi", status=status, details={"mismatches": mismatches})


def run_all_validations(base_path: Path | None = None) -> Dict[str, object]:
    payload = load_repairs(base_path)
    repairs = payload.get("repairs", [])
    chi_value = float(payload.get("chi_value", CHI_CAP))

    results = [
        validate_newton_repair(repairs, chi_value=chi_value),
        validate_periodic_table(base_path, chi_value=chi_value),
    ]

    summary = {"chi_cap": chi_value, "results": [r.as_dict() for r in results]}
    summary["status"] = "PASS" if all(r.status == "PASS" for r in results) else "FAIL"
    return summary


if __name__ == "__main__":
    output = run_all_validations()
    print(json.dumps(output, indent=2))
