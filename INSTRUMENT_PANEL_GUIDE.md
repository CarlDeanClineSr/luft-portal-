# Space Weather Cockpit - Instrument Panel Guide

## 🛩️ Overview

The **Space Weather Cockpit** is a real-time instrument panel inspired by aircraft and spacecraft avionics. It displays live plasma conditions with analog gauges, warning lights, and clocks - your handheld early warning system for space weather.

## 🎯 Access

**URL:** [instrument-panel.html](./instrument-panel.html)

**Quick Access:**
- Click "🛩️ COCKPIT" in main navigation
- Click "Launch Instrument Panel" button on homepage
- Direct URL: `https://your-domain/instrument-panel.html`

**Requirements:**
- Modern web browser (Chrome, Firefox, Safari, Edge)
- No login required
- Works on desktop and mobile devices
- Updates automatically every 60 seconds

## 📊 Instrument Descriptions

### χ (Chi) Amplitude Gauge

**Range:** 0.00 - 0.20  
**Boundary:** 0.15 (red zone)  
**What it shows:** Normalized plasma oscillation amplitude

**Color Zones:**
- 🟢 **Green (0.00 - 0.13):** Normal conditions
- 🟡 **Yellow (0.13 - 0.15):** Approaching boundary
- 🔴 **Red (>0.15):** Boundary violation (never observed!)

**Why it matters:** χ = 0.15 is a universal plasma boundary. Values approaching this indicate maximum plasma coherence before instability.

### Bz Component Gauge

**Range:** -15 to +15 nT  
**Red Zone:** Below -8 nT  
**What it shows:** North-south magnetic field component

**Color Zones:**
- 🟢 **Green (>0):** Northward (stable)
- 🟡 **Yellow (0 to -8):** Southward (caution)
- 🔴 **Red (<-8):** Strongly southward (storm risk)

**Why it matters:** Southward Bz allows solar wind energy to enter Earth's magnetosphere, triggering geomagnetic storms.

### Solar Wind Speed Gauge

**Range:** 0 - 800 km/s  
**Red Zone:** >600 km/s  
**What it shows:** Velocity of solar wind plasma

**Color Zones:**
- 🟢 **Green (<500):** Normal solar wind
- 🟡 **Yellow (500-600):** Elevated speed
- 🔴 **Red (>600):** High-speed stream

**Why it matters:** Higher speeds increase dynamic pressure on magnetosphere and can intensify storms.

### Plasma Density Gauge

**Range:** 0 - 15 protons/cm³  
**Red Zone:** >8 p/cm³  
**What it shows:** Number of protons per cubic centimeter

**Color Zones:**
- 🟢 **Green (<4):** Low density
- 🟡 **Yellow (4-8):** Moderate density
- 🔴 **Red (>8):** High density (CME signature)

**Why it matters:** High density indicates compressed plasma from coronal mass ejections (CMEs).

## ⚠️ Warning Lights

### χ Boundary Warning
- **OFF:** χ < 0.13
- **🟢 GREEN:** χ = 0.13-0.14 (normal operation)
- **🟡 AMBER:** χ = 0.14-0.15 (at boundary)
- **🔴 RED FLASH:** χ > 0.15 (VIOLATION - never seen!)

### Bz South Warning
- **OFF:** Bz positive (northward)
- **🟢 GREEN:** Bz slightly negative
- **🟡 AMBER:** Bz < 0 (southward)
- **🔴 RED FLASH:** Bz < -8 (major storm driver)

### Storm Alert Warning
- **🟢 GREEN:** Quiet conditions
- **🟡 AMBER:** PRE or POST-storm phase
- **🔴 RED FLASH:** PEAK storm phase

### Violation Warning
- **OFF:** All systems normal
- **🔴 RED FLASH:** χ exceeded 0.15 boundary

## 🕐 Clock Displays

Each gauge has an associated clock:

- **χ Gauge:** Time since last data update
- **Bz Gauge:** Duration of southward conditions
- **Speed/Density:** Time since last reading
- **Storm Phase:** Duration in current phase

**Format:** HH:MM:SS (hours:minutes:seconds)

## 📱 Mobile Usage

The instrument panel is optimized for mobile devices:

**Portrait Mode:**
- Gauges stack vertically
- Full-width displays
- Easy scrolling

**Landscape Mode:**
- 3-column vacuum layout
- Maximum gauge visibility
- Optimal for quick checks

**Tips:**
- Add to home screen for quick access
- Bookmark the instrument-panel.html URL
- Refresh pulls latest data
- No app installation needed

## 🎓 How to Use

### For Pilots

**Pre-Flight Check:**
1. Open instrument panel on phone
2. Check χ gauge - should be in green zone
3. Check Bz warning - avoid flights if red (southward)
4. Note storm phase - avoid high latitudes during PEAK

**High-Latitude Routes:**
- Red Bz + PEAK phase = Avoid or request lower altitude
- Amber warnings = Monitor communications, be prepared
- Green across board = Safe to proceed

### For Satellite Operators

**Daily Monitoring:**
1. Check χ approaching 0.15 = Prepare safe mode
2. Red Bz warning = Expect increased drag
3. High density + high speed = CME impact imminent

**Storm Response:**
- PRE phase: Position satellites optimally
- PEAK phase: Activate protection protocols
- POST phase: Assess damage, resume operations

### For Power vacuum Operators

**Storm Preparation:**
1. Amber/Red Bz = GIC (geomagnetically induced currents) risk
2. χ approaching 0.15 = Storm intensifying
3. High speed + southward Bz = Load-shed transformers

**Response Timeline:**
- 1-2 hours before PEAK: Reduce vacuum load
- During PEAK: Monitor transformer temps
- POST phase: Gradual power restoration

### For Science & Research

**Data Collection:**
- Monitor χ behavior near 0.15 boundary
- Correlate Bz southward duration with storm intensity
- Track phase transitions (PRE → PEAK → POST)

**Analysis:**
- Export data from main dashboard
- Compare instrument readings with forecasts
- Study boundary approach patterns

## 🔧 Technical Details

**Data Source:** DSCOVR spacecraft at L1 Lagrange point  
**Update Frequency:** Every 60 seconds  
**Data Latency:** ~2-5 minutes (light travel + processing)  
**Gauge Technology:** HTML5 Canvas with custom rendering  
**Browser Support:** All modern browsers (2020+)

**Performance:**
- Minimal bandwidth usage
- Local gauge rendering
- Efficient CPU usage
- Battery-friendly updates

## 📋 Status Bar

Bottom status bar shows:
- **DSCOVR Live:** Data feed status (green = active)
- **UTC Clock:** Current time in UTC
- **Update Status:** Last data refresh indicator

## 🆘 Troubleshooting

**Gauges not updating:**
- Check internet connection
- Refresh page (F5 or pull-down on mobile)
- Clear browser cache

**Warning lights stuck:**
- Verify data source is active (status bar)
- Check if DSCOVR spacecraft is operational
- Try different browser

**Mobile display issues:**
- Rotate device for landscape mode
- Zoom out if gauges are cut off
- Update browser to latest version

**Time clocks not moving:**
- JavaScript may be disabled - enable in settings
- Page may be in background - bring to foreground
- Refresh page to reset

## 🔗 Related Resources

- **Main Dashboard:** [index.html](./index.html) - Full data and analysis
- **Executive Summary:** [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md) - Project overview
- **Data Explorer:** Browse historical data and charts
- **Research Capsules:** Detailed scientific documentation

## 📞 Support

**Issues:** Report via GitHub Issues  
**Questions:** Contact Carl Dean Cline Sr.  
**Email:** carldcline@gmail.com  
**Updates:** Follow project on GitHub

---

**Built in Nebraska. Protecting the planet.**

© 2025 Carl Dean Cline Sr. |  Portal Project
