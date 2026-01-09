/**
 * Knowledge Widget - Repository Knowledge Browser
 * Loads and displays data/knowledge/index.json
 * Uses absolute URL with cache-busting to ensure live data from GitHub Pages.
 */

(function() {
    'use strict';

    // Use absolute URL for GitHub Pages, with cache-bust query parameter
    const BASE_URL = "https://carldeanclinesr.github.io/luft-portal-";
    const INDEX_URL = BASE_URL + "/data/knowledge/index.json";

    let knowledgeData = null;
    let filteredFiles = [];
    let currentFilter = 'all';
    let searchTerm = '';

    /**
     * Load knowledge index from JSON
     */
    async function loadKnowledgeIndex() {
        try {
            // Add cache-bust timestamp to defeat CDN caching
            const cacheBustUrl = INDEX_URL + "?t=" + Date.now();
            const response = await fetch(cacheBustUrl, { cache: "no-store" });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            knowledgeData = await response.json();
            
            // Update header info
            updateHeader();
            
            // Initialize filtered list
            filteredFiles = knowledgeData.files || [];
            
            // Render the table
            renderTable();
            
        } catch (error) {
            console.error('Failed to load knowledge index:', error);
            showError('Failed to load knowledge index. Please try again later.');
        }
    }

    /**
     * Update header statistics
     */
    function updateHeader() {
        const totalEl = document.getElementById('knowledge-total-files');
        const timestampEl = document.getElementById('knowledge-timestamp');
        
        if (totalEl && knowledgeData) {
            totalEl.textContent = knowledgeData.total_files || 0;
        }
        
        if (timestampEl && knowledgeData) {
            const timestamp = knowledgeData.generated_at || '';
            if (timestamp) {
                const date = new Date(timestamp);
                timestampEl.textContent = date.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZoneName: 'short'
                });
            }
        }
    }

    /**
     * Filter files by kind
     */
    function filterByKind(kind) {
        currentFilter = kind;
        applyFilters();
        
        // Update active button state
        const buttons = document.querySelectorAll('.knowledge-filter-btn');
        buttons.forEach(btn => {
            if (btn.dataset.filter === kind) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    /**
     * Search files by term
     */
    function searchFiles(term) {
        searchTerm = term.toLowerCase();
        applyFilters();
    }

    /**
     * Apply both filter and search
     */
    function applyFilters() {
        if (!knowledgeData || !knowledgeData.files) {
            return;
        }

        filteredFiles = knowledgeData.files.filter(file => {
            // Filter by kind
            if (currentFilter !== 'all' && file.kind !== currentFilter) {
                return false;
            }

            // Filter by search term
            if (searchTerm) {
                const searchable = [
                    file.path || '',
                    file.name || '',
                    file.title || '',
                    (file.keywords || []).join(' '),
                    (file.headers || []).join(' ')
                ].join(' ').toLowerCase();

                if (!searchable.includes(searchTerm)) {
                    return false;
                }
            }

            return true;
        });

        renderTable();
    }

    /**
     * Render the knowledge table
     */
    function renderTable() {
        const tbody = document.getElementById('knowledge-table-body');
        const countEl = document.getElementById('knowledge-filtered-count');
        
        if (!tbody) return;

        // Update count
        if (countEl) {
            countEl.textContent = `${filteredFiles.length} files`;
        }

        // Clear existing rows
        tbody.innerHTML = '';

        // Show message if no results
        if (filteredFiles.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 2rem; color: #94a3b8;">
                        No files found matching your criteria.
                    </td>
                </tr>
            `;
            return;
        }

        // Render each file
        filteredFiles.forEach(file => {
            const row = document.createElement('tr');
            
            // Path column with link
            const pathCell = document.createElement('td');
            const pathLink = document.createElement('a');
            pathLink.href = file.path;
            pathLink.textContent = file.path;
            pathLink.style.color = '#4ade80';
            pathLink.style.textDecoration = 'none';
            pathLink.addEventListener('mouseover', () => pathLink.style.textDecoration = 'underline');
            pathLink.addEventListener('mouseout', () => pathLink.style.textDecoration = 'none');
            pathCell.appendChild(pathLink);
            row.appendChild(pathCell);

            // Title column
            const titleCell = document.createElement('td');
            titleCell.textContent = file.title || file.name || '-';
            titleCell.title = file.preview || '';
            row.appendChild(titleCell);

            // Kind column with badge
            const kindCell = document.createElement('td');
            const kindBadge = document.createElement('span');
            kindBadge.className = 'knowledge-kind-badge';
            kindBadge.dataset.kind = file.kind;
            kindBadge.textContent = file.kind.toUpperCase();
            kindCell.appendChild(kindBadge);
            row.appendChild(kindCell);

            // Keywords/Headers column
            const metaCell = document.createElement('td');
            if (file.kind === 'csv' && file.headers) {
                const preview = file.headers.slice(0, 3).join(', ');
                metaCell.textContent = preview;
                if (file.headers.length > 3) {
                    metaCell.textContent += ` (+${file.headers.length - 3} more)`;
                }
            } else if (file.keywords) {
                metaCell.textContent = file.keywords.join(', ');
            } else {
                metaCell.textContent = '-';
            }
            metaCell.style.fontSize = '0.85rem';
            metaCell.style.color = '#94a3b8';
            row.appendChild(metaCell);

            tbody.appendChild(row);
        });
    }

    /**
     * Show error message
     */
    function showError(message) {
        const tbody = document.getElementById('knowledge-table-body');
        if (tbody) {
            tbody.innerHTML = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 4;
            cell.style.textAlign = 'center';
            cell.style.padding = '2rem';
            cell.style.color = '#ef4444';
            cell.textContent = message;  // Safe: use textContent instead of innerHTML
            row.appendChild(cell);
            tbody.appendChild(row);
        }
    }

    /**
     * Initialize the widget
     */
    function init() {
        // Set up filter buttons
        const filterButtons = document.querySelectorAll('.knowledge-filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                filterByKind(btn.dataset.filter);
            });
        });

        // Set up search input
        const searchInput = document.getElementById('knowledge-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchFiles(e.target.value);
            });
        }

        // Load the data
        loadKnowledgeIndex();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose functions globally if needed
    window.KnowledgeWidget = {
        reload: loadKnowledgeIndex,
        filter: filterByKind,
        search: searchFiles
    };

})();
