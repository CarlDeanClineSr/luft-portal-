// Teach-The-Engine widget
// Reads results/teacher/aggregate_index.json and docs/Teacher_Report.md
// Renders signature pass rates and recent items into containers on the page.
// Uses absolute URL with cache-busting to ensure live data from GitHub Pages.

(function () {
  // Use absolute URL for GitHub Pages, with cache-bust query parameter
  const BASE_URL = "https://carldeanclinesr.github.io/luft-portal-";
  const AGG_URL = BASE_URL + "/results/teacher/aggregate_index.json";
  const REPORT_URL = BASE_URL + "/docs/Teacher_Report.md";

  function $(sel) { return document.querySelector(sel); }
  function setText(sel, v) { const el = $(sel); if (el) el.textContent = v; }
  function setHTML(sel, v) { const el = $(sel); if (el) el.innerHTML = v; }

  function ratioStr(pass, total) {
    if (total === 0 || !total) return "0 / 0 (0%)";
    const pct = Math.round((pass / total) * 100);
    return `${pass} / ${total} (${pct}%)`;
  }

  function badge(text, ok) {
    const cls = ok ? "badge-pass" : "badge-fail";
    return `<span class="badge ${cls}">${text}</span>`;
  }

  async function fetchJSON(url) {
    // Add cache-bust timestamp to defeat CDN caching
    const cacheBustUrl = url + "?t=" + Date.now();
    const res = await fetch(cacheBustUrl, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function fetchText(url) {
    // Add cache-bust timestamp to defeat CDN caching
    const cacheBustUrl = url + "?t=" + Date.now();
    const res = await fetch(cacheBustUrl, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.text();
  }

  function computeSignatureStats(items) {
    const sigs = ["chi_boundary", "fractal_regulator", "binary_harmonics", "electroweak_bridge", "whistler_gaps"];
    const stats = {};
    for (const s of sigs) stats[s] = { pass: 0, total: 0 };
    let analyzed = 0;

    for (const it of items) {
      if (it.status === "analyzed") analyzed += 1;
      for (const s of sigs) {
        if (it[s]) {
          stats[s].total += 1;
          if (it[s].pass) stats[s].pass += 1;
        }
      }
    }
    return { stats, analyzed };
  }

  function renderList(items, maxRows = 6) {
    const rows = [];
    const slice = items.slice(0, maxRows);
    for (const it of slice) {
      const ok = it.status === "analyzed";
      let fn = "(unknown)";
      if (it.file) {
        const parts = it.file.split("/");
        fn = parts.length >= 2 ? parts.slice(-2).join("/") : parts[0] || "(unknown)";
      }
      rows.push(`<tr>
        <td class="mono">${fn}</td>
        <td>${badge(it.status || "unknown", ok)}</td>
        <td class="mono small">${it.reason || it.error || ""}</td>
      </tr>`);
    }
    return rows.join("");
  }

  async function initTeacherWidget() {
    const root = $("#teacher-widget");
    if (!root) return; // no widget container on this page

    try {
      const agg = await fetchJSON(AGG_URL);
      const items = Array.isArray(agg.items) ? agg.items : [];
      const { stats, analyzed } = computeSignatureStats(items);
      const total = agg.count || items.length || 0;

      setText("#teacher-total", String(total));
      setText("#teacher-analyzed", String(analyzed));

      setText("#teacher-pass-chi", ratioStr(stats.chi_boundary.pass, stats.chi_boundary.total));
      setText("#teacher-pass-fractal", ratioStr(stats.fractal_regulator.pass, stats.fractal_regulator.total));
      setText("#teacher-pass-binary", ratioStr(stats.binary_harmonics.pass, stats.binary_harmonics.total));
      setText("#teacher-pass-ew", ratioStr(stats.electroweak_bridge.pass, stats.electroweak_bridge.total));
      setText("#teacher-pass-whistler", ratioStr(stats.whistler_gaps.pass, stats.whistler_gaps.total));

      setHTML("#teacher-recent-tbody", renderList(items));

      // Try to fetch the report header
      try {
        const rpt = await fetchText(REPORT_URL);
        const firstLine = (rpt.split("\n").find(l => l.trim().length > 0) || "").trim();
        setText("#teacher-report-headline", firstLine || "Teacher Report");
      } catch {
        setText("#teacher-report-headline", "Teacher Report");
      }
    } catch (e) {
      setText("#teacher-report-headline", "Teach-The-Engine has no data yet. The panel updates after the next daily run.");
      console.warn("Teacher widget error:", e);
    }
  }

  // Export for optional auto-refresh
  window.initTeacherWidget = initTeacherWidget;

  // Late init to ensure DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTeacherWidget);
  } else {
    initTeacherWidget();
  }
})();
