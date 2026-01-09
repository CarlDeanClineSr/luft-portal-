// Live refresh for top metric cards and key panels (30–60s)
(function() {
  const endpoints = {
    // Adjust these to your actual JSON outputs if different
    // Top metrics (create a small JSON in your workflow or reuse existing)
    status: "./results/live_status.json",
    teacher: "https://carldeanclinesr.github.io/luft-portal-/results/teacher/aggregate_index.json",
    // Optional: meta-intel summary, correlations etc.
    correlations: "./data/link_intelligence/correlation_stats.json"
  };

  const $ = sel => document.querySelector(sel);
  const set = (sel, val) => { const el = $(sel); if (el) el.textContent = val; };

  // HTML escape function to prevent XSS
  function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  async function fetchJSON(url) {
    try {
      const res = await fetch(url + "?t=" + Date.now());
      if (!res.ok) throw new Error(res.statusText);
      return await res.json();
    } catch (_) { return null; }
  }

  async function refreshTopMetrics() {
    // Fallback values if your workflow hasn't built live_status.json yet
    const s = await fetchJSON(endpoints.status);
    if (s) {
      set("#metric-current-chi", String(s.current_chi ?? "--"));
      set("#metric-violations", String(s.violations ?? "--"));
      set("#metric-domains", String(s.domains_validated ?? "--"));
      set("#metric-correlations", String(s.correlations ?? "--"));
    }
  }

  async function refreshTeacherSummary() {
    const data = await fetchJSON(endpoints.teacher);
    const errEl = $("#teacher-report-headline");
    if (!data || !Array.isArray(data.items)) {
      if (errEl) errEl.textContent = "Teach‑The‑Engine has no data yet.";
      return;
    }
    if (errEl) errEl.textContent = "Live signature checks from workflow data";

    const items = data.items;
    // Update using existing page IDs
    set("#teacher-total", String(items.length));
    const analyzed = items.filter(it => it.status === "analyzed").length;
    set("#teacher-analyzed", String(analyzed));

    function passTotal(key) {
      let p=0, t=0;
      for (const it of items) {
        const v = it[key];
        if (v && typeof v.pass !== "undefined") {
          t++;
          if (v.pass) p++;
        }
      }
      return `${p} / ${t}`;
    }
    // Use existing page IDs for pass counts
    set("#teacher-pass-chi", passTotal("chi_boundary"));
    set("#teacher-pass-fractal", passTotal("fractal_regulator"));
    set("#teacher-pass-binary", passTotal("binary_harmonics"));
    set("#teacher-pass-ew", passTotal("electroweak_bridge"));
    set("#teacher-pass-whistler", passTotal("whistler_gaps"));

    // Recent table - use existing tbody ID
    const tbody = $("#teacher-recent-tbody");
    if (tbody) {
      const rows = [];
      for (const it of items.slice(0, 50)) {
        const notes = [];
        for (const k of ["chi_boundary","fractal_regulator","binary_harmonics","electroweak_bridge","whistler_gaps"]) {
          if (it[k]) notes.push(`${k}:${it[k].pass ? "pass" : "fail"}`);
        }
        // Escape user data to prevent XSS
        const safeFile = escapeHtml(it.file || "(unknown)");
        const safeStatus = escapeHtml(it.status || "unknown");
        const safeNotes = escapeHtml(notes.join(", "));
        rows.push(`<tr>
          <td class="mono" style="padding: 0.75rem;">${safeFile}</td>
          <td style="padding: 0.75rem;">${safeStatus}</td>
          <td class="mono small" style="padding: 0.75rem;">${safeNotes}</td>
        </tr>`);
      }
      tbody.innerHTML = rows.join("");
    }
  }

  async function refreshCorrelations() {
    const c = await fetchJSON(endpoints.correlations);
    if (c && typeof c.total_matches !== "undefined") {
      set("#metric-correlations", String(c.total_matches));
    }
  }

  function start() {
    // Initial load
    refreshTopMetrics();
    refreshTeacherSummary();
    refreshCorrelations();
    // 45s cadence
    setInterval(refreshTopMetrics, 45000);
    setInterval(refreshTeacherSummary, 45000);
    setInterval(refreshCorrelations, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
