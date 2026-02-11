#  Capsule: DSCOVR L1 Solar Wind & Magnetics

## Capsule Metadata (frontmatter)
id: dscovr-l1-audit-yyyy-mm-ddThhmmss
title: "DSCOVR L1 Solar Wind and Magnetics Audit"
tags: ["", "DSCOVR", "solar-wind", "magnetics", "L1"]
status: "active"
provenance: "https://www.swpc.noaa.gov/products/solar-wind"

## Key Fields (JSON)
{
  "timestamp": "2025-11-22T13:41:00Z",
  "instrument": "DSCOVR",
  "plasma": {
    "density_p_cm3": 5.20,
    "speed_km_sec": 420.2,
    "temperature_K": 78000
  },
  "magnetic": {
    "bt_nT": 10.36,
    "bx_nT": 3.11,
    "by_nT": -7.43,
    "bz_nT": -1.85
  },
  "quality": {
    "plasma_flag": "nominal",
    "mag_flag": "nominal",
    "calibration": "NOAA-released"
  },
  "url_data": "https://services.swpc.noaa.gov/products/solar-wind/dscovr.json"
}

##  Analysis Keys:
- f = Δρ/ρ_avg (foam fraction, compute from density vs. 30-day baseline)
- χ, Ω, sidebands (from speed and field time series; Fourier scan by  analysis)
- Event triggers: Check for Bz < -2.0 nT & Proton density > 8 p/cm³ (potential for void events)
- Audit: Monotonic timestamp, unit check, QC flag pass
