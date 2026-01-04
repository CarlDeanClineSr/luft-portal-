from engine_core import CHI, ENGINE_CONSTANTS, compute_physics_repairs


def test_compute_physics_repairs_uses_engine_constants():
    repairs = compute_physics_repairs()
    assert repairs["Newton_Gravity"]["fixed"] < repairs["Newton_Gravity"]["original"]
    assert repairs["Planck_Photon"]["change_pct"] == CHI * 100
    assert ENGINE_CONSTANTS["CHI"] == CHI
