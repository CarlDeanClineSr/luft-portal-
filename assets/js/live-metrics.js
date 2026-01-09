// Lightweight homepage counters sourced from repo CSVs
// Usage: include this script in index.html and add elements with IDs below.
// Uses absolute URL with cache-busting to ensure live data from GitHub Pages.

// Use absolute URL for GitHub Pages
const BASE_URL = "https://carldeanclinesr.github.io/luft-portal-";

async function fetchCSV(relativeUrl) {
  try {
    // Add cache-bust timestamp to defeat CDN caching
    const url = BASE_URL + "/" + relativeUrl + "?t=" + Date.now();
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    return text.trim().split("\n").map(line => line.split(","));
  } catch (e) {
    console.warn(`Failed to fetch ${relativeUrl}:`, e);
    return [];
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

(async function updateKPIs() {
  try {
    // Fetch latest heartbeat data - try 2026_01 first, fall back to 2025_12
    let rows = await fetchCSV("data/cme_heartbeat_log_2026_01.csv");
    if (rows.length < 2) {
      rows = await fetchCSV("data/cme_heartbeat_log_2025_12.csv");
    }
    
    if (rows.length < 2) {
      console.warn("No valid CSV data found");
      return;
    }

    // Get last row (most recent data)
    const last = rows[rows.length - 1];
    const chi = parseFloat(last[1]);
    
    // Count total observations across all data rows (skip header)
    const totalObservations = rows.length - 1;
    
    // Calculate violations (χ > 0.15)
    let violations = 0;
    for (let i = 1; i < rows.length; i++) {
      const rowChi = parseFloat(rows[i][1]);
      if (!isNaN(rowChi) && rowChi > 0.15) violations++;
    }

    // Update KPI elements
    setText("kpi-observations", totalObservations >= 1000000 
      ? `${(totalObservations / 1000000).toFixed(2)}M+` 
      : `${totalObservations.toLocaleString()}+`);
    setText("kpi-violations", violations.toString());
    setText("kpi-domains", "7");
    setText("kpi-fieldspan", "5 nT → 50,000 nT");
    setText("kpi-timescales", "10⁻²³ s → 10⁴ s");
    setText("kpi-chi-current", isNaN(chi) ? "N/A" : chi.toFixed(4));
    setText("kpi-peak-mode", "24h (≈212k)");
    setText("kpi-attractor", "56.1%");
    setText("kpi-correlations", "2,100,000+");
    setText("kpi-chi-max", "0.1500");
    setText("kpi-modes", "13");
    setText("kpi-fundamental", "0.9h");
    
    // Color code chi value based on proximity to boundary
    const chiEl = document.getElementById("kpi-chi-current");
    if (chiEl && !isNaN(chi)) {
      if (chi > 0.14) {
        chiEl.style.color = "#ffaa00"; // Warning color
      } else if (chi > 0.12) {
        chiEl.style.color = "#4ade80"; // Medium green
      } else {
        chiEl.style.color = "#00ff88"; // Bright green
      }
    }
    
    console.log("KPI metrics updated successfully");
  } catch (e) {
    console.warn("KPI update failed:", e);
  }
})();
