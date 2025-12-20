#!/usr/bin/env python3

"""
LUFT ENGINE CORE DIRECTIVES
This file defines the operational purpose of the engine.
Not documentation. Not narrative. Actual instructions.
"""

from data_sources import (
    get_noaa_text_feeds,
    get_ace_data,
    get_dscovr_data,
    get_omni2_hour,
)

from rules import (
    compute_chi,
    detect_chi_ceiling,
    detect_chi_floor,
    detect_chi_rebound,
    detect_boundary_recoil,
)

from audit import publish_state_capsule


CHI_CEILING = 0.015


def engine_step(timestamp):
    """Run one full engine cycle for a given timestamp."""

    # 1. INGEST ALL DATA
    noaa = get_noaa_text_feeds(timestamp)
    ace = get_ace_data(timestamp)
    dscovr = get_dscovr_data(timestamp)
    omni = get_omni2_hour(timestamp)

    # 2. COMPUTE χ FROM RAW PLASMA + FIELD
    chi = compute_chi(ace, dscovr, omni)

    # 3. APPLY RULES
    ceiling = detect_chi_ceiling(chi, CHI_CEILING)
    floor = detect_chi_floor(chi)
    rebound = detect_chi_rebound(chi)
    recoil = detect_boundary_recoil(ace, dscovr, omni)

    # 4. PUBLISH STATE
    publish_state_capsule(
        timestamp=timestamp,
        chi=chi,
        ceiling=ceiling,
        floor=floor,
        rebound=rebound,
        recoil=recoil,
        ace=ace,
        dscovr=dscovr,
        omni=omni,
        noaa=noaa,
    )


def engine_loop():
    """Run forever. This *is* the engine's purpose."""
    import time
    from datetime import datetime

    while True:
        now = datetime.utcnow()
        engine_step(now)
        time.sleep(3600)  # run hourly
