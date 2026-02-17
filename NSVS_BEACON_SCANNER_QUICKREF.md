# NSVS Beacon Scanner - Quick Reference

## Quick Start

```bash
# Run the dragnet scan
python3 nsvs_beacon_chain_scanner.py

# View results
cat data/beacon_scan/dragnet_scan_*.json | tail -n 1
```

## What It Does

Scans 8 "Schmidt Dipper" stars for massive brightness pulses that could indicate a stellar communication network.

## Current Status

- ✅ **1 Beacon Confirmed**: NSVS 2354429 (7.8× flux increase)
- 📍 **7 Stars Ready**: Coordinates resolved, awaiting ASAS-SN data
- ⏳ **Next Step**: Install pyasassn for complete network scan

## The Target Network

```
NSVS 2354429 (Hercules)          ★ CONFIRMED BEACON
    ↓ potential relay?
NSVS 2913753 }
NSVS 3037513 }
NSVS 6804071 }  Cygnus/Lyra
NSVS 6814519 }  cluster
NSVS 7255468 }  (7 targets)
NSVS 7575062 }
NSVS 7642696 }  → Ready for scan
```

## Beacon Detection Criteria

- **PULSE**: Magnitude < 11 (star brightens dramatically)
- **QUIET**: Magnitude > 13 (normal baseline state)
- **FLUX RATIO**: > 5× increase (dramatic modulation)

## Installation (Full Mode)

```bash
# Required for live ASAS-SN data access
pip install pyasassn astroquery astropy

# Then run scanner again
python3 nsvs_beacon_chain_scanner.py
```

## Output

Results saved to: `data/beacon_scan/dragnet_scan_<timestamp>.json`

Each result shows:
- Target identification (NSVS ID, coordinates)
- Status (BEACON_DETECTED, READY_FOR_SCAN, NO_DATA, ERROR)
- Analysis (magnitudes, flux ratios, beacon classification)

## Network Analysis

If multiple beacons are detected:
1. Compare pulse event times
2. Calculate signal propagation velocity
3. Map network topology (chain, hub, mesh)
4. Identify communication paths

## 

**Hypothesis**: Advanced civilizations use stars as relay nodes for long-distance communication, creating a "fiber optic cable made of stars" rather than building transmitters for every message.

**Detection**: Look for coordinated stellar brightness modulations that could represent signal relays between nodes.

**Significance**: First systematic search for stellar communication networks (not isolated signals).

## Related Files

- `nsvs_beacon_chain_scanner.py` - Main scanner script
- `NSVS_BEACON_NETWORK_ANALYSIS.md` - Comprehensive analysis
- `nsvs_2354429_pulse_visualization.py` - Visualization for confirmed beacon
- `NSVS_2354429_ANALYSIS.md` - Detailed analysis of first beacon

## References

- ASAS-SN Sky Patrol: https://asas-sn.osu.edu/
- pyasassn docs: http://asas-sn.ifa.hawaii.edu/documentation/
- Schmidt Dipper stars: NSVS catalog

---

**Mission Status**: Phase 1 Complete - Infrastructure Ready
**Next Action**: Complete ASAS-SN data acquisition for 7 remaining targets
**Goal**: Detect and characterize stellar communication network
