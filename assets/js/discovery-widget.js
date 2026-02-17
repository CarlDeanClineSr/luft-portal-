// Discovery Findings Widget
// Reads results/teacher/discovery_findings.json and displays findings on the dashboard
// Supports memory/advancement by tracking historical discoveries
// Uses absolute URL with cache-busting to ensure live data from GitHub Pages.

(function () {
  // Use absolute URL for GitHub Pages, with cache-bust query parameter
  const BASE_URL = "https://carldeanclinesr.github.io/luft-portal-";
  const FINDINGS_URL = BASE_URL + "/results/teacher/discovery_findings.json";

  function $(sel) { return document.querySelector(sel); }
  function setText(sel, v) { const el = $(sel); if (el) el.textContent = v; }
  function setHTML(sel, v) { const el = $(sel); if (el) el.innerHTML = v; }

  function formatDate(isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return isoStr;
    }
  }

  function formatPercent(val) {
    if (typeof val !== 'number' || isNaN(val)) return '—';
    return `${(val * 100).toFixed(1)}%`;
  }

  function renderDiscoveryCard(disc) {
    const metricsHtml = disc.metrics ? Object.entries(disc.metrics).map(([k, v]) => {
      const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      const value = typeof v === 'number' ? (v < 1 && v > 0 ? formatPercent(v) : v.toLocaleString()) : v;
      return `<div class="discovery-metric"><span class="metric-label">${label}:</span> <span class="metric-value">${value}</span></div>`;
    }).join('') : '';

    return `
      <div class="discovery-card">
        <h4 class="discovery-title">${disc.title}</h4>
        <p class="discovery-desc">${disc.description}</p>
        <p class="discovery-sig"><strong>Significance:</strong> ${disc.significance}</p>
        ${metricsHtml ? `<div class="discovery-metrics">${metricsHtml}</div>` : ''}
      </div>
    `;
  }

  function renderSignatureTable(signatures) {
    if (!signatures) return '';
    
    const rows = Object.entries(signatures).map(([name, stats]) => {
      const passRate = formatPercent(stats.pass_rate);
      const statusClass = stats.pass_rate >= 0.9 ? 'pass' : (stats.pass_rate >= 0.5 ? 'warn' : 'fail');
      const displayName = name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      return `<tr>
        <td>${displayName}</td>
        <td class="centered">${stats.pass}</td>
        <td class="centered">${stats.total}</td>
        <td class="centered ${statusClass}">${passRate}</td>
      </tr>`;
    }).join('');

    return `
      <table class="signature-table">
        <thead>
          <tr>
            <th>Signature</th>
            <th>Pass</th>
            <th>Total</th>
            <th>Rate</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  function renderHistory(history) {
    if (!history || history.length === 0) return '<p class="no-history">No history available yet.</p>';
    
    const recent = history.slice(-7).reverse();  // Last 7 days, most recent first
    const items = recent.map(h => `
      <div class="history-item">
        <span class="history-date">${h.date}</span>
        <span class="history-stat">${h.files_analyzed} files / ${h.discoveries_count} discoveries</span>
      </div>
    `).join('');
    
    return `<div class="history-list">${items}</div>`;
  }

  async function loadFindings() {
    const root = $("#discovery-widget");
    if (!root) return;

    try {
      // Add cache-bust timestamp to defeat CDN caching
      const cacheBustUrl = FINDINGS_URL + "?t=" + Date.now();
      const res = await fetch(cacheBustUrl, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const findings = await res.json();

      // Update summary stats
      setText("#discovery-total-files", String(findings.stats?.total_files || 0));
      setText("#discovery-analyzed", String(findings.stats?.analyzed || 0));
      setText("#discovery-timestamp", formatDate(findings.generated));

      // Render discoveries
      const discoveriesHtml = (findings.discoveries || []).map(renderDiscoveryCard).join('');
      setHTML("#discovery-list", discoveriesHtml || '<p>No discoveries in this run.</p>');

      // Render signature scorecard
      setHTML("#discovery-signatures", renderSignatureTable(findings.signatures));

      // Render history
      setHTML("#discovery-history", renderHistory(findings.history));

    } catch (e) {
      console.warn("Discovery widget error:", e);
      setHTML("#discovery-list", '<p style="color:#94a3b8;">No discovery data available yet. Run the teacher suite first.</p>');
    }
  }

  // Export for manual refresh
  window.loadDiscoveryFindings = loadFindings;

  // Init when DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadFindings);
  } else {
    loadFindings();
  }
})();
