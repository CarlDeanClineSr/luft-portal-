// Vault Navigator Widget
// Reads data/knowledge/org_index.json and renders a searchable cross-repo table
// Uses absolute URL with cache-busting to ensure live data from GitHub Pages.

(function () {
  // Use absolute URL for GitHub Pages, with cache-bust query parameter
  const BASE_URL = "https://carldeanclinesr.github.io/luft-portal-";
  const ORG_INDEX_URL = BASE_URL + "/data/knowledge/org_index.json";

  function $(sel) { return document.querySelector(sel); }
  function $$(sel) { return document.querySelectorAll(sel); }
  
  let allFiles = [];
  let orgData = null;

  function setText(sel, v) {
    const el = $(sel);
    if (el) el.textContent = v;
  }

  function setHTML(sel, v) {
    const el = $(sel);
    if (el) el.innerHTML = v;
  }

  async function fetchJSON(url) {
    // Add cache-bust timestamp to defeat CDN caching
    const cacheBustUrl = url + "?t=" + Date.now();
    const res = await fetch(cacheBustUrl, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function extractFilesFromOrgIndex(data) {
    const files = [];
    
    if (!data.repositories || !Array.isArray(data.repositories)) {
      return files;
    }

    for (const repo of data.repositories) {
      const repoName = repo.name || "unknown";
      const repoUrl = repo.url || "#";
      const teacherSummary = repo.teacher_summary || null;
      
      if (repo.knowledge_index && repo.knowledge_index.files) {
        for (const file of repo.knowledge_index.files) {
          files.push({
            repo: repoName,
            repoUrl: repoUrl,
            path: file.path || "",
            title: file.title || "",
            kind: file.kind || "unknown",
            keywords: file.keywords || [],
            teacherSummary: teacherSummary
          });
        }
      }
    }

    return files;
  }

  function renderFileRow(file) {
    const keywords = Array.isArray(file.keywords) 
      ? file.keywords.slice(0, 5).join(", ") 
      : "";
    
    let teacherBadge = "";
    if (file.teacherSummary) {
      const ts = file.teacherSummary;
      const analyzed = ts.analyzed || 0;
      const total = ts.total_datasets || 0;
      if (total > 0) {
        teacherBadge = `<span class="teacher-badge" title="Teach-The-Engine: ${analyzed}/${total} datasets analyzed">${analyzed}/${total}</span>`;
      }
    }

    return `
      <tr>
        <td>
          <a href="${file.repoUrl}" target="_blank" rel="noopener" class="repo-link">${file.repo}</a>
          ${teacherBadge}
        </td>
        <td><span class="path-mono">${file.path}</span></td>
        <td>${file.title.substring(0, 80)}${file.title.length > 80 ? "..." : ""}</td>
        <td><span class="kind-badge">${file.kind}</span></td>
        <td class="keywords-cell">${keywords}</td>
      </tr>
    `;
  }

  function renderTable(files) {
    const tbody = $("#vault-table-body");
    if (!tbody) return;

    if (files.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 2rem; color: #94a3b8;">
            No files found matching your filters
          </td>
        </tr>
      `;
      return;
    }

    const rows = files.map(renderFileRow).join("");
    tbody.innerHTML = rows;
  }

  function applyFilters() {
    const searchInput = $("#vault-search");
    const kindFilter = $("#vault-kind-filter");
    
    if (!searchInput || !kindFilter) return;

    const searchTerm = searchInput.value.toLowerCase();
    const selectedKind = kindFilter.value;

    let filtered = allFiles;

    // Apply kind filter
    if (selectedKind !== "all") {
      filtered = filtered.filter(f => f.kind === selectedKind);
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(f => {
        const searchableText = [
          f.repo,
          f.path,
          f.title,
          f.kind,
          ...(f.keywords || [])
        ].join(" ").toLowerCase();
        
        return searchableText.includes(searchTerm);
      });
    }

    renderTable(filtered);
    setText("#vault-count", `${filtered.length} files`);
  }

  function renderRepoSummary(data) {
    const container = $("#vault-summary");
    if (!container) return;

    const totalRepos = data.total_repos || 0;
    const reposWithKnowledge = data.repos_with_knowledge || 0;
    const reposWithTeacher = data.repos_with_teacher || 0;
    const totalFiles = data.total_files_indexed || 0;

    container.innerHTML = `
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-label">Total Repositories</div>
          <div class="summary-value">${totalRepos}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">With Knowledge Index</div>
          <div class="summary-value">${reposWithKnowledge}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">With Teacher Analysis</div>
          <div class="summary-value">${reposWithTeacher}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Total Files Indexed</div>
          <div class="summary-value">${totalFiles.toLocaleString()}</div>
        </div>
      </div>
    `;
  }

  function renderTeacherSummaries(data) {
    const container = $("#vault-teacher-summary");
    if (!container) return;

    const reposWithTeacher = data.repositories.filter(r => r.teacher_summary);
    
    if (reposWithTeacher.length === 0) {
      container.innerHTML = "<p style='color: #94a3b8;'>No Teacher Analysis data available</p>";
      return;
    }

    let html = "<div class='teacher-repos-grid'>";
    
    for (const repo of reposWithTeacher) {
      const ts = repo.teacher_summary;
      const analyzed = ts.analyzed || 0;
      const total = ts.total_datasets || 0;
      const pct = total > 0 ? Math.round((analyzed / total) * 100) : 0;

      html += `
        <div class="teacher-repo-card">
          <h4><a href="${repo.url}" target="_blank" rel="noopener">${repo.name}</a></h4>
          <div class="teacher-stat">
            <span class="stat-label">Datasets:</span>
            <span class="stat-value">${analyzed}/${total} (${pct}%)</span>
          </div>
      `;

      if (ts.signatures) {
        html += "<div class='signature-grid'>";
        for (const [sig, stats] of Object.entries(ts.signatures)) {
          const sigTotal = stats.total || 0;
          const sigPass = stats.pass || 0;
          const sigPct = sigTotal > 0 ? Math.round((sigPass / sigTotal) * 100) : 0;
          const passClass = sigPct >= 50 ? "pass" : "fail";
          
          html += `
            <div class="signature-stat ${passClass}">
              <div class="sig-name">${sig.replace(/_/g, " ")}</div>
              <div class="sig-ratio">${sigPass}/${sigTotal}</div>
              <div class="sig-pct">${sigPct}%</div>
            </div>
          `;
        }
        html += "</div>";
      }

      html += "</div>";
    }
    
    html += "</div>";
    container.innerHTML = html;
  }

  async function initVaultNavigator() {
    const root = $("#vault-navigator");
    if (!root) return; // no vault navigator container on this page

    try {
      console.log("Loading organization index...");
      orgData = await fetchJSON(ORG_INDEX_URL);
      
      allFiles = extractFilesFromOrgIndex(orgData);
      console.log(`Loaded ${allFiles.length} files from ${orgData.repositories.length} repositories`);

      // Render summary stats
      renderRepoSummary(orgData);
      
      // Render teacher summaries
      renderTeacherSummaries(orgData);

      // Set generated timestamp
      const timestamp = orgData.generated_at || "unknown";
      setText("#vault-timestamp", new Date(timestamp).toLocaleString());

      // Initial table render
      applyFilters();

      // Attach event listeners
      const searchInput = $("#vault-search");
      const kindFilter = $("#vault-kind-filter");

      if (searchInput) {
        searchInput.addEventListener("input", applyFilters);
      }

      if (kindFilter) {
        kindFilter.addEventListener("change", applyFilters);
      }

      // Populate kind filter options dynamically
      if (kindFilter && allFiles.length > 0) {
        const kinds = [...new Set(allFiles.map(f => f.kind))].sort();
        kinds.forEach(kind => {
          if (kind && kind !== "all") {
            const option = document.createElement("option");
            option.value = kind;
            option.textContent = kind;
            kindFilter.appendChild(option);
          }
        });
      }

    } catch (e) {
      console.error("Vault Navigator error:", e);
      setHTML("#vault-summary", `
        <div style="color: #ff4444; padding: 2rem; text-align: center;">
          <strong>⚠️ Failed to load organization index</strong><br>
          The cross-repo index may not be generated yet. Run the daily workflow or wait for the next scheduled update.
        </div>
      `);
    }
  }

  // Export for optional manual refresh
  window.initVaultNavigator = initVaultNavigator;

  // Late init to ensure DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initVaultNavigator);
  } else {
    initVaultNavigator();
  }
})();
