<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>LUFT Portal — Live Space Weather Observatory</title>
  <style>
    :root {
      --bg: #0a0a0a;
      --text: #e0e0e0;
      --accent: #4da3ff;
      --section-bg: #111;
      --border: #222;
      --green: #0f0;
      --yellow: #ff0;
      --red: #f33;
    }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', Arial, sans-serif;
      line-height: 1.6;
      margin: 0;
      padding: 0;
    }
    .nav {
      background: #000;
      padding: 1rem;
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
      justify-content: center;
      border-bottom: 2px solid var(--border);
    }
    .nav a {
      color: var(--accent);
      text-decoration: none;
      font-weight: bold;
      transition: color 0.3s;
    }
    .nav a:hover { color: #80bfff; }
    .container {
      max-width: 1400px;
      margin: 2rem auto;
      padding: 0 1rem;
    }
    .logo-box {
      width: 140px;
      height: 140px;
      margin: 2rem auto;
      border: 4px solid var(--accent);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 4.5rem;
      font-weight: bold;
      color: var(--accent);
      box-shadow: 0 0 20px rgba(77, 163, 255, 0.3);
    }
    .ticker {
      background: #000;
      border: 2px solid #0f0;
      padding: 1.2rem;
      font-family: 'Courier New', monospace;
      font-size: 1.2rem;
      text-align: center;
      margin-bottom: 2rem;
      border-radius: 8px;
    }
    .section {
      background: var(--section-bg);
      padding: 1.8rem;
      margin: 1.5rem 0;
      border-radius: 10px;
      border: 1px solid var(--border);
      box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    summary {
      cursor: pointer;
      font-size: 1.3rem;
      color: var(--accent);
      margin-bottom: 1rem;
    }
    img {
      max-width: 100%;
      border-radius: 8px;
      margin: 1rem 0;
    }
    .badge {
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      font-weight: bold;
      margin-left: 0.5rem;
    }
    .green { background: var(--green); color: #000; }
    .yellow { background: var(--yellow); color: #000; }
    .red { background: var(--red); color: #fff; }
    footer {
      text-align: center;
      color: #666;
      padding: 2rem 0;
      font-size: 0.9rem;
    }
  </style>
</head>
<body>
  <!-- NAVIGATION -->
  <div class="nav">
    <a href="#status">📡 Status</a>
    <a href="#chi">🧠 χ Learning</a>
    <a href="#wind">🌬️ Solar Wind</a>
    <a href="#forecast">🔮 Forecast</a>
    <a href="#data">📁 Data</a>
    <a href="#capsules">📘 Capsules</a>
  </div>

  <!-- LOGO -->
  <div class="logo-box">χ</div>

  <div class="container">
    <h1>🌌 LUFT Portal — Live Space Weather Observatory</h1>
    <p>Welcome to the LUFT Project's automated data engine. Real-time solar wind analysis, coherence boundary detection, and cosmic heartbeat monitoring — updated every hour.</p>

    <!-- LIVE TICKER -->
    <div class="ticker" id="ticker">
      Loading live status...
    </div>

    <!-- VAULT STATUS -->
    <div class="section" id="status">
      <h2>📡 Vault Status</h2>
      <p><strong>Latest Indicator:</strong> <span class="badge green">ACTIVE</span> | Density: MODERATE | Speed: FAST | Bz: NORTHWARD</p>
      <a href="LATEST_VAULT_STATUS.md">→ Open Latest Vault Status</a>
    </div>

    <!-- χ LEARNING -->
    <div class="section" id="chi">
      <h2>🧠 χ Learning Loop v2</h2>
      <p>Tracks coherence amplitude χ across CME events, NOAA forecasts, GOES radiation, and F10.7 flux.</p>
      <details>
        <summary>View χ Learning Summary</summary>
        <p><a href="reports/">Reports Directory</a></p>
        <p><a href="results/">Results CSVs</a></p>
      </details>
    </div>

    <!-- SOLAR WIND CHARTS -->
    <div class="section" id="wind">
      <h2>🌬️ Solar Wind Mini-Charts</h2>
      <details>
        <summary>Show Charts</summary>
        <img src="reports/charts/density_latest.png" alt="Density" />
        <img src="reports/charts/speed_latest.png" alt="Speed" />
        <img src="reports/charts/bz_latest.png" alt="Bz" />
      </details>
    </div>

    <!-- WATERFALL / GIF -->
    <div class="section">
      <h2>🎇 Waterfall / GIF Visualizations</h2>
      <details>
        <summary>Show Waterfall</summary>
        <img src="reports/charts/waterfall_latest.gif" alt="Waterfall" />
      </details>
    </div>

    <!-- FORECAST -->
    <div class="section" id="forecast">
      <h2>🔮 Forecast Indicators</h2>
      <p><a href="reports/latest_srs.md">Latest SRS Report</a></p>
      <p><a href="reports/latest_f107.md">Latest F10.7 Report</a></p>
      <p><a href="data/noaa_text/">NOAA Text Forecasts</a></p>
    </div>

    <!-- DATA DIRECTORY -->
    <div class="section" id="data">
      <h2>📁 Data Directory</h2>
      <p><a href="data/noaa_text/">NOAA Text Feeds</a></p>
      <p><a href="data/noaa_solarwind/">NOAA Solar Wind</a></p>
      <p><a href="data/na_tec_total_electron_content/">TEC Maps</a></p>
      <p><a href="data/ovation_latest_aurora_n/">Aurora Power</a></p>
      <p><a href="data/solar_radio_flux/">Solar Radio Flux</a></p>
      <p><a href="data/ace_epam/">GOES/ACE Proton & Electron Flux</a></p>
    </div>

    <!-- CAPSULES -->
    <div class="section" id="capsules">
      <h2>📘 Science Capsules</h2>
      <p><a href="capsules/">Open Capsules</a></p>
    </div>

    <!-- FOOTER -->
    <footer>
      Page auto-updates hourly. Last updated: <span id="live-time"></span><br>
      Open source — <a href="https://github.com/CarlDeanClineSr/luft-portal-">Improve this page</a>
    </footer>
  </div>

  <!-- LIVE TIME & TICKER FETCH -->
  <script>
    // Live UTC time
    document.getElementById('live-time').innerHTML = new Date().toUTCString();

    // Fetch live ticker from LATEST_VAULT_STATUS.md
    fetch('LATEST_VAULT_STATUS.md')
      .then(response => response.text())
      .then(text => {
        const chiMatch = text.match(/Latest χ Amplitude:\s*([\d.]+)/);
        const densityMatch = text.match(/Density:\s*([\d.]+)/);
        const speedMatch = text.match(/Speed:\s*([\d.]+)/);
        const bzMatch = text.match(/Bz:\s*([+-][\d.]+)/);
        const statusMatch = text.match(/Status:\s*(\w+)/);

        const ticker = document.getElementById('ticker');
        ticker.innerHTML = `
          <b>χ:</b> ${chiMatch ? chiMatch[1] : 'N/A'}  
          <b>Density:</b> ${densityMatch ? densityMatch[1] + ' p/cm³' : 'N/A'}  
          <b>Speed:</b> ${speedMatch ? speedMatch[1] + ' km/s' : 'N/A'}  
          <b>Bz:</b> ${bzMatch ? bzMatch[1] + ' nT' : 'N/A'}  
          <b>Status:</b> ${statusMatch ? statusMatch[1] : 'N/A'}
        `;
      })
      .catch(() => {
        document.getElementById('ticker').innerHTML = 'Live status unavailable';
      });

    // Optional: Auto-refresh every 5 minutes
    setInterval(() => location.reload(), 300000);
  </script>
</body>
</html>
