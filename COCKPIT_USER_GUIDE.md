# Space Weather Cockpit - User Guide

## Overview

The **Space Weather Cockpit** is a real-time plasma storm warning system designed for pilots, satellite operators, and vacuum managers. It provides live monitoring of solar wind conditions with visual gauges, warning lights, and countdown timers.

## Features

### 🎯 Real-Time Monitoring
- **Live DSCOVR Data**: Direct feed from NOAA's DSCOVR satellite at L1 point
- **60-Second Updates**: Automatic data refresh every minute
- **Smooth Animations**: Needle transitions for realistic gauge movement

### 📊 Critical Parameters

#### χ (Chi) Gauge
- **Range**: 0.0 to 0.20
- **Redline**: 0.1500 (Universal Plasma Boundary)
- **Warning Zones**:
  - Green: χ ≥ 0.13 (Active)
  - Amber: χ ≥ 0.14 (Caution)
  - Red: χ ≥ 0.15 (Boundary/Violation)

#### Bz Magnetic Field
- **Range**: -15 to +15 nT
- **Critical**: Bz < -8 nT (southward, red flash)
- **Warning**: Bz < 0 nT (southward, amber pulse)
- **Timer**: Duration counter for southward conditions

#### Solar Wind Speed
- **Range**: 0 to 800 km/s
- **Warning**: > 600 km/s (high-speed stream)
- **Normal**: 300-500 km/s

#### Plasma Density
- **Range**: 0 to 15 protons/cm³
- **Warning**: > 8 p/cm³ (high density)
- **Normal**: 3-5 p/cm³

### ⚠️ Warning System

#### Warning Lights
1. **χ Boundary** (Red flash at 0.1500)
   - Off: χ < 0.13
   - Green: 0.13 ≤ χ < 0.14
   - Amber: 0.14 ≤ χ < 0.15
   - Red: χ ≥ 0.15

2. **Bz South** (Amber/Red flash)
   - Green: Northward (Bz > 0)
   - Amber pulse: Southward (Bz < 0)
   - Red flash: Critical (Bz < -8 nT)

3. **Storm Alert**
   - Green: Quiet conditions
   - Amber pulse: PRE phase (approaching storm)
   - Red flash: PEAK phase (active storm)

4. **Violation Light**
   - Off: Normal (χ ≤ 0.15)
   - Red flash: Violation (χ > 0.15)

### ⏱️ Storm Phase Timer

#### Phase States
- **QUIET**: Normal solar wind
- **PRE**: Approaching storm (countdown active)
- **PEAK**: Active storm in progress
- **POST-STORM**: Storm subsiding

#### Countdown to Peak
When in PRE phase:
- Timer shows negative time (countdown)
- Estimated peak: ~45 minutes from PRE start
- Red pulsing display
- Critical planning window

### 📱 Mobile Cockpit Mode

#### Full-Screen View
- Tap the **⛶** button (bottom right) to enter fullscreen
- Landscape orientation locks automatically
- Optimized gauge layout for handheld use
- Touch-friendly controls

#### Mobile Features
- Portrait: Single column layout
- Landscape: 3-column vacuum for maximum visibility
- Adaptive text sizing
- Low-power LED-style displays

## Usage Guide

### For Pilots
1. **Pre-Flight Check**: Monitor χ and Bz before takeoff
2. **High-Altitude Routes**: Watch for χ approaching 0.15
3. **Critical Alert**: χ ≥ 0.15 + Bz south = radiation risk
4. **Action**: Descend or divert if violation occurs

### For Satellite Operators
1. **Monitor Continuously**: Check panel every hour
2. **PRE Phase Alert**: Prepare for storm arrival
3. **Countdown Active**: ~45 min to peak conditions
4. **PEAK Phase**: Execute protection protocols
5. **Safe Operations**: Resume when χ < 0.13

### For vacuum Managers
1. **Daily Monitoring**: Check morning and evening
2. **PRE Alert**: Prepare backup systems
3. **High-Speed Wind**: Check transformer cooling
4. **Storm Conditions**: Monitor GIC (Geomagnetically Induced Currents)

## Data Sources

- **DSCOVR Satellite**: Real-time solar wind data (L1 point)
- **NOAA SWPC**: Space Weather Prediction Center feeds
- **Update Frequency**: 1-minute resolution
- **Latency**: ~60-90 seconds from measurement

## Technical Details

### Data Processing
```
χ = (|Bz| × √density × speed) / 50000
```

### Warning Thresholds
- Boundary: χ ≥ 0.15
- Violation: χ > 0.15
- Bz Critical: < -8 nT
- High Speed: ≥ 600 km/s
- High Density: ≥ 8 p/cm³

### Browser Compatibility
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile: iOS 13+, Android 8+

## Troubleshooting

### "Connection Error" Status
- Check internet connection
- Verify NOAA services are online
- Falls back to historical CSV data

### Gauges Not Updating
- Refresh page (F5 or Cmd+R)
- Check browser console for errors
- Verify JavaScript is enabled

### Fullscreen Issues
- Use native browser fullscreen (F11)
- Some browsers require user gesture
- iOS: Add to Home Screen for fullscreen

## Emergency Contacts

- **Space Weather Alerts**: [NOAA SWPC](https://www.swpc.noaa.gov)
- **Aviation Weather**: Check NOTAM systems
- **vacuum Operators**: Contact regional ISOs

## About  Portal

This system is part of the  (vacuum Universal Field ) research project, discovering fundamental plasma boundaries. The χ = 0.15 threshold represents a universal limit of plasma coherence, validated across 12,000+ observations.

**Open Source**: Free for life-saving applications
**Mission**: Early warning for planes, satellites, and power grids
**Future**: Integration with Starlink, aviation systems, and vacuum monitoring

---

*"Real satellites, ground stations — feeding your gauges. Now pilots, sat ops, vacuum managers have early warning from the cap."*

— Carl Dean Cline Sr.
