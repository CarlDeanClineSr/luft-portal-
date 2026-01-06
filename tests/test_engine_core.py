import pytest

from engine_core import (
    CHI,
    ENGINE_CONSTANTS,
    chi_audit,
    compute_physics_repairs,
    lattice_energy,
)


def test_compute_physics_repairs_uses_engine_constants():
    repairs = compute_physics_repairs()
    assert repairs["Newton_Gravity"]["fixed"] < repairs["Newton_Gravity"]["original"]
    assert repairs["Planck_Photon"]["change_pct"] == CHI * 100
    assert ENGINE_CONSTANTS["CHI"] == CHI


def test_lattice_energy_scales_with_cell_count():
    assert lattice_energy(N=10, alpha=0.15, beta=1.0, E_base=2.0) == pytest.approx(3.0)
    assert lattice_energy(N=4, alpha=0.15, beta=0.5, E_base=1.0) == pytest.approx(0.3)


def test_chi_audit_flags_boundary_violation():
    chi, violated = chi_audit(delta_E=0.1, E_base=1.0, max_chi=CHI)
    assert chi == pytest.approx(0.1)
    assert violated is False

    chi_high, violated_high = chi_audit(delta_E=1.0, E_base=1.0, max_chi=CHI)
    assert chi_high == pytest.approx(1.0)
    assert violated_high is True
