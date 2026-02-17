---
id: goes-event-audit-2025-11-22T13:41:00Z
title: "GOES Geostationary Particle & Magnetics Audit — 2025-11-22T13:41:00Z"
tags: ["LUFT","GOES","geomag","particle","event","harvester"]
status: "active"
provenance: "https://www.swpc.noaa.gov/products/goes-xray-flux"
owner: "Dr. Carl Dean Cline Sr."
---

# CAPSULE: GOES Geostationary Particle & Magnetics Audit

## Key Fields (JSON)
```json
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
```

## LUFT Analysis Keys
- Trigger: proton_flux_pfu > 100 pfu → "harvester" capsule.
- Compare Bz and particle spikes to foam modulation for void prediction.
- Daily event summary for thrust/void predictions.
