<!-- DARK THEME -->
<style>
body { background: #0a0a0a; color: #e0e0e0; font-family: Arial, sans-serif; line-height: 1.6; }
a { color: #4da3ff; }
.nav { background: #111; padding: 12px; display: flex; gap: 20px; border-bottom: 2px solid #222; }
.nav a { color: #4da3ff; text-decoration: none; font-weight: bold; }
.badge { padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: bold; margin-left: 6px; }
.green { background:#0f0; color:#000; } .yellow { background:#ff0; color:#000; } .red { background:#f33; color:#000; }
.section { background:#111; padding:20px; margin:20px 0; border-radius:10px; border:1px solid #222; }
.logo-box { width:120px; height:120px; border:3px solid #4da3ff; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:3em; margin-bottom:20px; color:#4da3ff; font-weight:bold; }
summary { cursor:pointer; font-size:1.2em; color:#4da3ff; }
</style>

<!-- NAVIGATION BAR -->
<div class="nav">
<a href="#status">📡 Status</a> 
<a href="#chi">🧠 χ Learning</a> 
<a href="#wind">🌬️ Solar Wind</a> 
<a href="#forecast">🔮 Forecast</a> 
<a href="#data">📁 Data</a> 
<a href="#capsules">📘 Capsules</a>
</div>

<!-- LUFT LOGO BOX -->
<div class="logo-box"> χ </div>

# 🌌 **LUFT Portal — Live Space Weather Dashboard**
Welcome to the LUFT Project's Data Engine. This dashboard updates automatically as LUFT workflows run.

---

## ✅ **LIVE STATUS TICKER**
<div style="background:#000; color:#0f0; padding:12px; font-family:monospace; font-size:1.1em; border:1px solid #0f0;">
<b>χ:</b> 0.1500 <b>Density:</b> 2.32 p/cm³ <b>Speed:</b> 528.5 km/s <b>Bz:</b> +4 nT <b>Status:</b> Active (2 locks)
</div>

---

# 📡 **Vault Status**
<a name="status"></a>
<div class="section">
### Latest Vault Indicator
**Status:** <span class="badge green">ACTIVE</span>  
👉 <a href="LATEST_VAULT_STATUS.md">Open Latest Vault Status</a>
</div>

---

# 🧠 **χ Learning Loop v2 (Forecast‑Aware)**
<a name="chi"></a>
<div class="section">
<details>
<summary>📘 View χ Learning Summary</summary>
<br>
👉 <a href="reports/">Open Reports Directory</a><br><br>
👉 <a href="results/">Open Results CSVs</a>
</details>
</div>

---

# 🌬️ **Solar Wind Mini‑Charts**
<a name="wind"></a>
<div class="section">
<details>
<summary>📊 Show Charts</summary>
<br>

### Density
<img src="reports/charts/density_latest.png" width="100%">

### Speed
<img src="reports/charts/speed_latest.png" width="100%">

### Bz
<img src="reports/charts/bz_latest.png" width="100%">

</details>
</div>

---

# 🎇 **Waterfall / GIF Visualizations**
<div class="section">
<details>
<summary>🎞️ Show Waterfall</summary>
<br>
<img src="reports/charts/waterfall_latest.gif" width="100%">
</details>
</div>

---

# 🔮 **Forecast Indicators**
<a name="forecast"></a>
<div class="section">
👉 <a href="reports/latest_srs.md">Latest SRS Report</a><br>
👉 <a href="reports/latest_f107.md">Latest F10.7 Report</a><br>
👉 <a href="data/noaa_text/">NOAA Text Forecasts</a>
</div>

---

# 📁 **Data Directory**
<a name="data"></a>
<div class="section">
👉 <a href="data/noaa_text/">NOAA Text Feeds</a><br>
👉 <a href="data/noaa_solarwind/">NOAA Solar Wind</a><br>
👉 <a href="data/na_tec_total_electron_content/">TEC Maps</a><br>
👉 <a href="data/ovation_latest_aurora_n/">Aurora Power</a><br>
👉 <a href="data/solar_radio_flux/">Solar Radio Flux</a><br>
👉 <a href="data/ace_epam/">GOES/ACE Proton & Electron Flux</a>
</div>

---

# 📘 **Science Capsules**
<a name="capsules"></a>
<div class="section">
👉 <a href="capsules/">Open Capsules</a>
</div>

---

<div style="text-align:center; color:#666; margin-top:40px;">
Page auto-updates as workflows run. Last updated: <span id="live-time"></span>
</div>

<script>
document.getElementById('live-time').innerHTML = new Date().toUTCString();
</script>
