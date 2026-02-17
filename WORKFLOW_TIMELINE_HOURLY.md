# Workflow Execution Timeline - One Hour View

This document shows exactly when each high-frequency workflow executes during a typical hour.

## Visual Timeline (60-minute cycle)

```
:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          Space Weather (2min)
     🛰️ ACE (2min)             Magnetometer (3min)
     ☀️ Solar Activity (5min)  🔴 Flare Monitor (3min)

:01 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          💫 Plasma (3min)
     🛰️ ACE (2min)             ☄️ CME Detection (5min)
                               🧲 Geomagnetic (10min)

:02 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          Space Weather (2min)
     🛰️ ACE (2min)             🧲 Mag Field (3min)
                               ⚡ Electron Flux (5min)

:03 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          🛰️ SOHO (3min)
     🛰️ ACE (2min)             Magnetometer (3min)
     💫 Plasma (3min)          🔴 Flare Monitor (3min)
     ⚡ Proton Flux (5min)     🌌 Auroral (10min)

:04 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          🛰️ STEREO-A (4min)
     🛰️ ACE (2min)             🧲 Mag Field (3min)
                               🛰️ GOES (5min)

:05 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          Space Weather (2min)
     🛰️ ACE (2min)             ☀️ Solar Activity (5min)
     🔴 CME Heartbeat (5min)   ☄️ CME Detection (5min)
     🔴 Solar Wind (5min)      ⚡ Electron Flux (5min)
     🪐 MAVEN (10min)          📊 DST Index (30min)

:06 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          🛰️ SOHO (3min)
     🛰️ ACE (2min)             Magnetometer (3min)
     💫 Plasma (3min)          🔴 Flare Monitor (3min)
     ☄️ CME Detection (5min)   ⚡ Proton Flux (5min)
     📊 Summary (15min)

:07 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          🧲 Mag Field (3min)
     🛰️ ACE (2min)             🔴 Solar Wind Audit (30min)

:08 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          Space Weather (2min)
     🛰️ ACE (2min)             ⚡ Proton Flux (5min)
                               📖 Vault Narrator (15min)

:09 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          🛰️ SOHO (3min)
     🛰️ ACE (2min)             Magnetometer (3min)
     💫 Plasma (3min)          🔴 Flare Monitor (3min)
                               🛰️ GOES (5min)

:10 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          🧲 Mag Field (3min)
     🛰️ ACE (2min)             ☀️ Solar Activity (5min)
     🔴 CME Heartbeat (5min)   ⚡ Electron Flux (5min)
     📈 Vault Forecast (15min) ⚡ Parker Solar Probe (10min)
     🧲 USGS Magnetometer (10min)
     🖥️ Engine Status (10min)

:11 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          ☄️ CME Detection (5min)
     🛰️ ACE (2min)             🧲 Geomagnetic (10min)

:12 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR (2min)          Space Weather (2min)
     🛰️ ACE (2min)             🛰️ SOHO (3min)
     Magnetometer (3min)       🔴 Flare Monitor (3min)
     ⚡ Proton Flux (5min)

...pattern continues every 60 minutes...

:15 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [Major sync point - 15-minute workflows all execute]
     🛰️ Voyager Audit          χ Boundary Monitor
     📊 Dashboard Updates       📈 Vault Forecast
     📊 Summary

:20 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🛰️ DSCOVR                 🛰️ ACE
     📰 NOAA Feed Parser (20min)

:25 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [15-minute workflows + MAVEN]
     📈 Vault Forecast         🪐 MAVEN

:30 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [Major sync point - 30-minute workflows]
     📊 DST Index              🔴 Solar Wind Audit

:35 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [15-minute workflows]
     📊 DST Index (30min)      🪐 MAVEN

:40 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [15-minute workflows]
     📈 Vault Forecast         📰 NOAA Feed Parser

:45 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [Major sync point - 15-minute workflows]
     🪐 MAVEN

:50 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     ⚡ Parker Solar Probe (10min)

:55 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     [15-minute workflows]
     📈 Vault Forecast         🪐 MAVEN
```

## Legend

- 🛰️ = Satellite data collection
- ☀️ = Solar monitoring
- 🔴 = Critical/real-time data
- ⚡ = Particle flux monitoring
- 🧲 = Magnetic field data
- 💫 = Plasma data
- ☄️ = CME/event detection
- 🪐 = Planetary missions
- 📊 = Analysis/reporting
- 📈 = Forecasting
- 🖥️ = System monitoring
- 📰 = Data feeds
- 🌌 = Auroral/geomagnetic
- 📖 = Documentation/narrative

## Execution Count Per Hour

| Frequency | Count | Workflows |
|-----------|-------|-----------|
| Every 2 min | 30 runs | DSCOVR, ACE, Space Weather Alerts |
| Every 3 min | 20 runs | SOHO, Magnetometer, Plasma, Mag Field, Flare Monitor |
| Every 4 min | 15 runs | STEREO-A |
| Every 5 min | 12 runs | NOAA Solar Wind, CME Heartbeat, GOES, Solar Activity, Electron/Proton Flux, CME Detection |
| Every 10 min | 6 runs | PSP, MAVEN, USGS Mag, Engine Status, Geomagnetic, Auroral |
| Every 15 min | 4 runs | Chi Boundary, Voyager, Dashboard, Vault Forecast, Vault Narrator, Summary |
| Every 20 min | 3 runs | NOAA Feed Parser |
| Every 30 min | 2 runs | DST Index, Solar Wind Audit |

**Total: ~720 executions per hour** (approximately 12 per minute on average)

## Peak Activity Times

**Highest Activity:** Minutes ending in 0, 5, 10, 15 (major synchronization points)
- These minutes have 10-15 workflows executing simultaneously

**Moderate Activity:** Minutes ending in 1, 2, 3, 4, 6, 7, 8, 9
- These minutes have 3-8 workflows executing

**Strategic Offsets:** Workflows are intentionally offset to:
1. Avoid API rate limits
2. Prevent git push conflicts  
3. Distribute GitHub Actions load
4. Ensure continuous data flow

## Data Freshness

| Data Type | Maximum Age | Typical Age |
|-----------|-------------|-------------|
| L1 Solar Wind | 2 minutes | 1 minute |
| Space Weather Alerts | 2 minutes | 1 minute |
| Solar Flares | 3 minutes | 1.5 minutes |
| Magnetic Field | 3 minutes | 1.5 minutes |
| Plasma Data | 3 minutes | 1.5 minutes |
| GOES X-ray/Particles | 5 minutes | 2.5 minutes |
| PSP/MAVEN | 10 minutes | 5 minutes |
| System Status | 10 minutes | 5 minutes |
| Forecasts/Summaries | 15 minutes | 7.5 minutes |

## Redundancy & Reliability

Multiple satellites monitor the same phenomena:
- **Solar Wind:** DSCOVR + ACE + SOHO (3 sources)
- **Magnetic Field:** DSCOVR + ACE + Ground Magnetometers (3+ sources)
- **X-ray Flux:** GOES-16 + GOES-18 (2 sources)
- **Particle Flux:** GOES-16 + GOES-18 (2 sources)

If any single source fails, others continue providing coverage.

---

**This schedule ensures CONTINUOUS, REDUNDANT, HIGH-FREQUENCY monitoring of all critical space weather parameters 24/7/365.**
