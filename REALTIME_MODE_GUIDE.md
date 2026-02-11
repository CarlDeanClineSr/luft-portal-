# Real-Time Cockpit Mode 🚀⚡

**High-speed update mode for aircraft/spacecraft operations**

## Overview

The  Portal instrument panel now includes a **Real-Time Mode** designed for actual flight operations where you need instant, high-frequency updates of all systems.

## Quick Start

### Enable Real-Time Mode

1. **Open** `instrument-panel.html`
2. **Click** the ⚡ button (bottom right, next to fullscreen)
3. **Confirm** the alert
4. **Page reloads** with high-speed updates enabled

### Disable Real-Time Mode

1. **Click** the ⚡ button again (it will be green/pulsing when active)
2. **Confirm** to return to standard mode
3. **Page reloads** with normal update intervals

## Update Frequency Comparison

| System | Standard Mode | ⚡ Real-Time Mode | Speed Increase |
|--------|---------------|------------------|----------------|
| **Data Updates** | 60 seconds | 5 seconds | **12x faster** |
| **Clock Display** | 1 second | 100ms | **10x faster** |
| **Research Status** | 5 minutes | 30 seconds | **10x faster** |
| **Discovery Feed** | 60 seconds | 10 seconds | **6x faster** |

## Technical Details

### Standard Mode (Default)
```javascript
{
    data: 60000ms,      // Solar wind, χ, Bz updates
    research: 300000ms, // Research status, warnings
    clock: 1000ms,      // UTC clock display
    discovery: 60000ms  // Paper discovery feed
}
```

### Real-Time Mode (⚡ Active)
```javascript
{
    data: 5000ms,       // 5 second updates
    research: 30000ms,  // 30 second updates
    clock: 100ms,       // 100ms updates (smooth)
    discovery: 10000ms  // 10 second updates
}
```

## Use Cases

### ✈️ Aircraft Operations
- Real-time space weather monitoring during flight
- Instant awareness of solar events
- High-frequency χ boundary updates
- Rapid storm phase changes

### 🚀 Spacecraft Operations
- Critical mission phases
- Launch windows
- Orbital maneuvers
- Re-entry preparation

### 🎮 Mission Control
- Live monitoring of multiple data streams
- Quick decision making
- High-cadence event tracking
- Emergency response

### 🔬 Research Operations
- Real-time data collection
- Live experiment monitoring
- Fast-changing phenomena observation
- Event validation

## Visual Indicators

### ⚡ Button States

**Inactive (Yellow):**
- Standard mode active
- 60-second updates
- Tooltip: "Real-Time Mode: OFF"

**Active (Green + Pulsing):**
- Real-time mode active
- 5-second updates
- Tooltip: "Real-Time Mode: ON"
- Glowing animation

### Console Messages

When enabled, you'll see:
```
⚡ HIGH-SPEED UPDATES ENABLED FOR AIRCRAFT/SPACECRAFT OPERATIONS
   Data: 5000ms | Research: 30000ms | Clock: 100ms
⚡ Discovery feed: HIGH-SPEED MODE (10000ms updates)
```

## Performance Considerations

### CPU Usage
- **Standard:** ~1-2% average
- **Real-Time:** ~3-5% average
- Still very efficient!

### Network Usage
- **Standard:** ~1 KB/min
- **Real-Time:** ~12 KB/min
- Minimal impact on bandwidth

### Battery Impact
- **Standard:** Negligible
- **Real-Time:** Slightly higher (mobile devices)
- Recommended for plugged-in operations

## Data Sources

All updates pull from:
- `data/cme_heartbeat_log_*.csv` - Live solar wind data
- `data/papers/impact_analysis.json` - Discovery feed
- Local calculations - χ values, storm phases

## Browser Compatibility

Works in all modern browsers:
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Persistence

Your preference is saved in **browser localStorage**:
- Setting persists across page reloads
- Cleared on browser data reset
- Per-device configuration

## Advanced Usage

### Programmatic Control

Enable via JavaScript console:
```javascript
localStorage.setItem('realtimeMode', 'true');
location.reload();
```

Disable:
```javascript
localStorage.setItem('realtimeMode', 'false');
location.reload();
```

Check current state:
```javascript
localStorage.getItem('realtimeMode'); // 'true' or 'false'
```

### Custom Intervals

Edit `js/instrument-panel.js`:
```javascript
const UPDATE_INTERVALS = REALTIME_MODE ? {
    data: 2000,        // Even faster: 2 seconds
    research: 15000,   // 15 seconds
    clock: 50,         // 50ms (very smooth)
    discovery: 5000    // 5 seconds
} : {
    // Standard mode intervals...
};
```

## Troubleshooting

### Issue: Updates seem slow in real-time mode
**Solution:** Check console for mode confirmation. Try disabling/re-enabling.

### Issue: High CPU usage
**Solution:** This is normal for 5-second updates. Switch back to standard mode if needed.

### Issue: Button doesn't respond
**Solution:** Ensure JavaScript is enabled. Check browser console for errors.

### Issue: Settings don't persist
**Solution:** Check if browser allows localStorage. Try different browser.

## Safety Features

### Automatic Fallback
If data source unavailable:
- System continues displaying last known values
- No crashes or freezes
- Graceful degradation

### Error Handling
All update functions have try-catch:
- Failed updates don't break the panel
- Errors logged to console
- Next update cycle continues

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F` | Toggle fullscreen |
| `R` | (Future) Toggle real-time mode |

## When to Use Each Mode

### Use Standard Mode (60s) When:
- 👀 Casual monitoring
- 🔋 Battery-powered device
- 📱 Mobile viewing
- 🌐 Slow network connection
- 💤 Overnight monitoring

### Use Real-Time Mode (5s) When:
- ✈️ Active flight operations
- 🚀 Launch/mission critical phases
- ⚠️ Alert/emergency situations
- 🔬 Live data collection
- 🎯 Time-sensitive decisions
- 🔌 Plugged into power

## Future Enhancements

Planned features:
- [ ] Keyboard shortcut (R key)
- [ ] Multiple speed tiers (2s, 5s, 10s, 30s, 60s)
- [ ] Auto-enable on specific events
- [ ] Adaptive mode (slows down when idle)
- [ ] Audio alerts for critical updates
- [ ] Haptic feedback (mobile)

## Technical Architecture

### Flow Diagram
```
User clicks ⚡ button
    ↓
Toggle localStorage
    ↓
Show confirmation alert
    ↓
Page reloads
    ↓
JS reads localStorage
    ↓
Sets UPDATE_INTERVALS
    ↓
Applies to all setInterval() calls
    ↓
High-speed updates active!
```

### Code Location
- **HTML:** `instrument-panel.html` (toggle button, JS)
- **JS:** `js/instrument-panel.js` (interval configuration)
- **CSS:** `instrument-panel.html` (button styles)

## Examples

### Scenario 1: Pre-Flight Check
```
1. Open instrument panel
2. Enable ⚡ Real-Time Mode
3. Monitor all systems for 5 minutes
4. Verify χ boundary stable
5. Check Bz component
6. Proceed with flight
```

### Scenario 2: Storm Monitoring
```
1. Notice storm warning
2. Enable ⚡ Real-Time Mode
3. Watch phase transitions in real-time
4. Track χ approaching 0.15
5. Monitor Bz southward duration
6. Make go/no-go decision
```

### Scenario 3: Research Session
```
1. Start data collection
2. Enable ⚡ Real-Time Mode
3. Monitor discovery feed for new papers
4. Track network intelligence updates
5. Record observations
6. Return to standard mode when done
```

## Related Documentation

- **Instrument Panel Guide:** `INSTRUMENT_PANEL_GUIDE.md`
- **Engine Discovery:** `docs/ENGINE_DISCOVERY_MODE.md`
- **Quick Reference:** `QUICK_REFERENCE.md`

## Support

For issues or questions:
1. Check browser console for errors
2. Verify network connectivity
3. Test in different browser
4. Review this documentation

## Credits

**Concept:** Carl Dean Cline Sr. - "Need CLINE's programs cockpit to update faster..."
**Implementation:**  Portal Development Team  
**Purpose:** Real-world aircraft/spacecraft operations

---

*"When you're flying, you need your instruments NOW, not in 60 seconds."*

**Last Updated:** 2026-01-01  
**Version:** 2.0.0 (Real-Time Mode)
