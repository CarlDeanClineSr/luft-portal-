#  Capsule: GOES Event Particle & Magnetics

## Capsule Metadata (frontmatter)
id: goes-event-audit-yyyy-mm-ddThhmmss
title: "GOES Geostationary Particle & Magnetics Audit"
tags: ["", "GOES", "geomag", "particle", "event"]
status: "active"
provenance: "https://www.swpc.noaa.gov/products/goes-xray-flux"

## Key Fields (JSON)
{
  "timestamp": "2025-11-22T13:41:00Z",
  "instrument": "GOES",
  "particle": {
    "proton_flux_pfu": 125,
    "electron_flux_pfu": 2200,
    "xray_flux_W_m2": 1.2e-6
  },
  "magnetic": {
    "bx_nT": 1.33,
    "by_nT": 3.09,
    "bz_nT": -0.94
  },
  "quality": {
    "event_flag": "active",
    "calibration": "NOAA-released"
  },
  "url_data": "https://services.swpc.noaa.gov/products/goes-xray-flux.json"
}

##  Analysis Keys:
- Trigger on proton flux > 100 pfu for “harvester” capsule
- Compare Bz and particle spikes to foam modulation
- Daily event summary for thrust/void predictions
