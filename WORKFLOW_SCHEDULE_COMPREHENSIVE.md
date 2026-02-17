# High-Frequency Workflow Schedule Documentation

## Overview
This document describes the comprehensive automated data ingestion system for the  Portal, featuring 70+ workflows that run at various intervals to continuously collect L1 satellite data, space weather observations, and scientific measurements.

## Workflow Schedule Summary

### Every 2 Minutes (Highest Frequency)
- **DSCOVR L1 Data** (`dscovr_data_ingest.yml`) - Primary L1 solar wind source
- **ACE L1 Realtime** (`l1_ace_realtime_2min.yml`) - ACE magnetic field & plasma
- **Space Weather Alerts** (`space_weather_alerts_2min.yml`) - Critical alerts & warnings

### Every 3 Minutes
- **SOHO L1 Realtime** (`l1_soho_realtime_3min.yml`) - SOHO composition data
- **Magnetometer Network** (`magnetometer_realtime_3min.yml`) - USGS & INTERMAGNET
- **Plasma Monitor** (`plasma_monitor_3min.yml`) - Multi-source plasma data
- **Magnetic Field Monitor** (`magnetic_field_monitor_3min.yml`) - Comprehensive B-field
- **Solar Flare Monitor** (`solar_flare_monitor_3min.yml`) - Rapid flare detection

### Every 4 Minutes
- **STEREO-A L1 Data** (`l1_stereo_realtime_4min.yml`) - STEREO beacon mode

### Every 5 Minutes
- **NOAA Solar Wind** (`hourly_noaa_solarwind.yml`) - High-cadence solar wind
- **CME Heartbeat Logger** (`cme_heartbeat_logger.yml`) - CME detection & logging
- **GOES Ingest** (`goes_ingest.yml`) - GOES X-ray & particle data
- **Solar Activity Monitor** (`solar_activity_5min.yml`) - Comprehensive solar monitoring
- **Electron Flux Monitor** (`electron_flux_5min.yml`) - GOES electron flux
- **Proton Flux Monitor** (`proton_flux_5min.yml`) - GOES proton flux
- **CME Detection** (`cme_detection_5min.yml`) - Coronal mass ejection signatures

### Every 10 Minutes
- **PSP (Parker Solar Probe)** (`psp_ingest_10min.yml`) - PSP data when available
- **MAVEN Mars Data** (`maven_realtime_10min.yml`) - Mars atmosphere & plasma
- **USGS Magnetometer** (`hourly_usgs_magnetometer.yml`) - Ground magnetometers
- **Engine Status** (`engine_status.yml`) - System health monitoring
- **Geomagnetic Indices** (`geomagnetic_indices_10min.yml`) - Kp, Ap, DST indices
- **Auroral Activity** (`auroral_activity_10min.yml`) - Aurora forecasts & intensity

### Every 15 Minutes
- **Chi Boundary Monitor** (`chi_boundary_monitor.yml`) - χ ≤ 0.15 boundary analysis
- **Voyager Audit** (`-voyager-audit-superaction.yml`) - Multi-satellite audit
- **Dashboard Updates** (`update_dashboard_graph.yml`) - Real-time visualization
- **Vault Forecast** (`vault_10row_forecast.yml`) - Predictive analytics
- **Vault Narrator** (`vault_narrator.yml`) - System narration
- **Hourly Summary** (`hourly_summary.yml`) - Comprehensive summaries

### Every 20 Minutes
- **NOAA Feed Parser** (`noaa_parse_feeds.yml`) - Text product ingestion

### Every 30 Minutes
- **DST Index** (`hourly_dst_index.yml`) - Geomagnetic storm index
- **Solar Wind Audit** (`solar_wind_audit.yml`) - Comprehensive validation

### Hourly (Every 60 Minutes)
- **Fundamental Correlation** (`fundamental_correlation.yml`) - Cross-correlation analysis
- **Imperial Indexer** (`imperial_indexer.yml`) - Scientific indexing (every 6 hours)
- **Physics Repairs** (`physics_repairs.yml`) - Data quality checks (every 6 hours)
- **Physics Paper Harvester** (`physics_paper_harvester.yml`) - ArXiv harvesting (every 6 hours)
- **GOES Data Audit** (`goes_data_audit.yml`) - Quality assurance (every 6 hours)
- **Momentum Test** (`momentum_test.yml`) - Physics validation (every 6 hours)
- **NOAA Text Parser** (`noaa_text_parser.yml`) - Advanced parsing (every 6 hours)
- **Fractal Echo Scanner** (`fractal_echo_scanner_15min.yml`) - Pattern detection (every 12 hours)

### Daily Workflows
- **CERN LHC** (`daily_cern_lhc.yml`) - 05:00 UTC
- **GISTEMP** (`daily_gistemp.yml`) - 05:00 UTC
- **LIGO Gravitational Waves** (`daily_ligo_gw.yml`) - 05:00 UTC
- **MAVEN Mars** (`daily_maven_mars.yml`) - 05:00 UTC (supplemented by 10-min workflow)
- **NOAA Forecast** (`daily_noaa_forecast.yml`) - 05:00 & 17:00 UTC
- **ML Rebound** (`daily_ml_rebound.yml`) - 02:30 UTC
- **Paper Extraction** (`daily_paper_extraction.yml`) - 02:00 UTC
- **Reconnection Simulation** (`daily_reconnection_simulation.yml`) - 03:00 UTC
- **Auto-Append Baseline** (`auto-append-baseline.yml`) - 06:00 UTC
- **Append Baseline Watch** (`append_baseline_watch.yml`) - 12:00 UTC
- **Cygnus Army Census** (`cygnus_army_census.yml`) - 12:00 UTC
- **Lightning Analyzer** (`lightning_analyzer.yml`) - 12:00 UTC
- **INTERMAGNET Chi** (`intermagnet_chi_analysis.yml`) - 06:15 UTC
- **INTERMAGNET Daily** (`intermagnet_daily_chi.yml`) - 12:00 UTC
- **Knowledge Index** (`knowledge_index.yml`) - 12:15 UTC
- **Index Job** (`index-job.yml`) - 06:15 UTC
- **Link Harvest** (`link_harvest_daily.yml`) - 03:00 UTC
- **Nightly Capsule** (`nightly_capsule.yml`) - 03:00 UTC
- **Pages Deployment** (`pages-deployment.yml`) - 06:00 UTC
- **Star Relay Scanner** (`star_relay_scanner.yml`) - 06:00 UTC
- **Teacher Suite** (`teacher_suite.yml`) - 12:00 UTC
- **FFT Sideband** (`run_fft_sideband.yml`) - 06:00 UTC
- **Rebound Test** (`run_rebound_test.yml`) - 06:00 UTC
- **Graviton Sideband** (`graviton_sideband_analysis.yml`) - 00:00 UTC
- **Imperial Unified Engine** (`imperial_unified_engine.yml`) - 00:00 UTC
- **Inspire Harvest** (`inspire_harvest.yml`) - 00:00 UTC

## Data Sources

### L1 Lagrange Point Satellites
- **DSCOVR** - Deep Space Climate Observatory (primary real-time source)
- **ACE** - Advanced Composition Explorer
- **SOHO** - Solar and Heliospheric Observatory
- **STEREO-A** - Solar Terrestrial Relations Observatory (beacon mode)

### Geostationary Satellites
- **GOES-16/18** - X-ray flux, particle flux, magnetometer

### Planetary Missions
- **PSP** - Parker Solar Probe (in situ solar wind)
- **MAVEN** - Mars Atmosphere and Volatile EvolutioN

### Ground-Based Networks
- **USGS** - United States Geological Survey magnetometers
- **INTERMAGNET** - International Real-time Magnetic Observatory Network
- **NOAA** - National Oceanic and Atmospheric Administration

### Space Weather Products
- Solar wind plasma (density, velocity, temperature)
- Magnetic field (Bx, By, Bz, Bt)
- X-ray flux (flare detection)
- Proton & electron flux (radiation belts)
- Geomagnetic indices (Kp, Ap, DST)
- CME detection & tracking
- Auroral forecasts

## Time Distribution Strategy

Workflows are distributed across time slots to:
1. **Avoid API Rate Limits** - Staggered queries to NOAA, NASA, USGS
2. **Prevent Git Conflicts** - Offset commit times for different data streams
3. **Ensure Continuous Coverage** - Multiple satellites provide redundancy
4. **Optimize Resource Usage** - Balanced GitHub Actions usage

## Workflow Naming Convention

- `l1_*` - L1 Lagrange point satellite data
- `*_realtime_*` - Real-time high-frequency data streams
- `*_monitor_*` - Active monitoring workflows
- `*_ingest_*` - Data ingestion workflows
- `daily_*` - Once-daily workflows
- `hourly_*` - Hourly or sub-hourly workflows

## Concurrency Management

Each high-frequency workflow uses a unique concurrency group to prevent:
- Simultaneous executions of the same workflow
- Git push conflicts
- Resource contention

Example:
```yaml
concurrency:
  group: l1-ace-realtime
  cancel-in-progress: false
```

## Error Handling

All workflows include:
- **Graceful Degradation** - Continue on fetch failures
- **JSON Validation** - Using `jq` to validate downloaded data
- **Fallback Sources** - Secondary endpoints when primary fails
- **Detailed Logging** - Success/failure reporting per data source

## Monitoring & Alerts

Key workflows that monitor system health:
- `engine_status.yml` - Every 10 minutes
- `hourly_summary.yml` - Every 15 minutes
- `space_weather_alerts_2min.yml` - Critical alerts

## Manual Trigger Support

All workflows support `workflow_dispatch` for:
- Manual testing
- Backfilling missed data
- Emergency data collection

## Total Workflow Count

- **High-Frequency (≤5 min):** 13 workflows
- **Medium-Frequency (10-20 min):** 16 workflows
- **Hourly/Multi-Hour:** 12 workflows
- **Daily:** 28 workflows
- **Manual/On-Demand:** 10 workflows
- **Total:** 70+ workflows

## Data Pipeline Flow

```
L1 Satellites → High-Freq Ingest (2-5 min) → Real-Time Processing → 
  → Monitoring & Analysis (10-15 min) → Summaries (15-30 min) → 
  → Daily Aggregation & Reporting → Long-Term Archive
```

## System Capacity

With this schedule, the system processes:
- **~720 workflow runs per hour** during peak activity
- **~17,280 workflow runs per day**
- **~120,000+ workflow runs per week**
- **Continuous 24/7/365 data collection**

This ensures comprehensive real-time monitoring of space weather, solar wind, geomagnetic activity, and multi-satellite data streams for the  Portal Imperial Physics Observatory.

---

**Last Updated:** 2026-02-03  
**Status:** Operational - All workflows active post-maintenance
