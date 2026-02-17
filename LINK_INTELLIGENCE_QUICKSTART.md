#  Link Intelligence Network - Quick Start Guide

**🚀 Get started with the  Link Harvesting & Intelligence System in 5 minutes!**

---

## What This System Does

The  Link Intelligence Network discovers, maps, and visualizes **all connections** between your repository and the global scientific data ecosystem. It:

- 🔍 **Scans** 3,000+ files for URLs
- 📊 **Extracts** 50,000+ links to scientific data sources
- 🌐 **Maps** connections to NASA, NOAA, CERN, ESA, and more
- 📈 **Analyzes** network relationships and patterns
- 🎨 **Visualizes** interactive knowledge graphs
- 🤖 **Automates** daily monitoring via GitHub Actions

---

## 🎯 Three Ways to Use It

### Option 1: Quick Summary (30 seconds)

Get an instant overview of all links in your repository:

```bash
python link_harvester_core.py --scan-repo
```

**Output:**
```
Files scanned: 3,179
Total links found: 58,257
Unique domains: 156

Links by Category:
  NASA                :   72 links
  NOAA                :  510 links
  CERN                :   30 links
  arXiv               : 3,479 links
  GitHub              :  580 links
  ...
```

### Option 2: Export Data for Analysis (2 minutes)

Generate structured data files for deeper analysis:

```bash
# Create data directory
mkdir -p data/link_intelligence

# Harvest and export
python link_harvester_core.py \
  --output-json data/link_intelligence/links.json \
  --output-csv data/link_intelligence/links.csv

# Build network graph
python link_graph_analyzer.py \
  --input data/link_intelligence/links.json \
  --output data/link_intelligence/link_network.json
```

**Outputs:**
- `links.json` - All links with metadata (15 MB)
- `links.csv` - Spreadsheet format for manual analysis (7 MB)
- `link_network.json` - Network graph data (8 MB)

### Option 3: Interactive Visualization (5 minutes)

Explore connections visually in your web browser:

```bash
# Generate data (if not already done)
python link_harvester_core.py --output-json data/link_intelligence/links.json
python link_graph_analyzer.py --input data/link_intelligence/links.json --output data/link_intelligence/link_network.json

# Open dashboard
open link_intelligence_dashboard.html
```

Then:
1. Click **"Load Network Data"**
2. Explore the interactive graph
3. Search for specific nodes
4. Click nodes to see details

---

## 📚 Key Files Explained

| File | Purpose | When to Use |
|------|---------|-------------|
| `link_harvester_core.py` | Extract links from repository | Start here - run first |
| `link_graph_analyzer.py` | Build network graphs | After harvesting, for analysis |
| `link_intelligence_dashboard.html` | Interactive visualization | For exploring connections visually |
| `external_data_sources_registry.yaml` | Catalog of 43+ data sources | Reference for integration planning |
| `LINK_INTELLIGENCE_REPORT.md` | Complete documentation | When you need details |

---

## 🎓 Common Use Cases

### Use Case 1: "What external sources does  use?"

```bash
python link_harvester_core.py --scan-repo
```

Look at the **"Links by Category"** section to see NASA, NOAA, CERN, etc.

### Use Case 2: "Which files reference the most external sources?"

```bash
python link_harvester_core.py --output-csv links.csv
```

Open `links.csv` in Excel/Google Sheets and create a pivot table on the **File** column.

### Use Case 3: "How are different data sources connected?"

```bash
python link_graph_analyzer.py --input links.json --type domain-only --visualize
```

Open the generated HTML to see domain co-occurrence patterns.

### Use Case 4: "Find all NASA data sources"

```bash
# Generate CSV
python link_harvester_core.py --output-csv links.csv

# Filter with grep (Linux/Mac)
grep -i "nasa" links.csv

# Or open in spreadsheet and filter by "Category" = "NASA"
```

### Use Case 5: "Track link changes over time"

The GitHub Actions workflow runs daily and saves timestamped files:
```
data/link_intelligence/links_20250101.json
data/link_intelligence/links_20250102.json
...
```

Compare files to see what changed.

---

## 🤖 Automated Daily Harvesting

The system includes a GitHub Actions workflow that runs automatically every day at 3:00 AM UTC.

**What it does:**
1. Scans entire repository
2. Extracts all links
3. Builds network graphs
4. Commits results to `data/link_intelligence/`
5. Creates timestamped files + `current` symlinks

**Manual trigger:**
1. Go to GitHub repository
2. Click **Actions** tab
3. Select ** Link Harvest Daily**
4. Click **Run workflow**

**View results:**
- Files: `data/link_intelligence/`
- Latest: `data/link_intelligence/link_network.json`
- Report: `data/link_intelligence/LATEST_HARVEST_REPORT.md`

---

## 💡 Pro Tips

### Tip 1: Focus on Specific Categories

Edit `link_harvester_core.py` and modify the `DOMAIN_CATEGORIES` dictionary to customize categorization.

### Tip 2: Exclude Large Files

If harvesting is slow, skip large data files by adding to `SKIP_EXTENSIONS`:
```python
SKIP_EXTENSIONS = {
    '.h5', '.wav', '.mp4',
    # Add your extensions here
}
```

### Tip 3: Compare with External Registry

Cross-reference harvested links with `external_data_sources_registry.yaml` to find:
- ✅ Sources already integrated
- ❌ Sources not yet used
- 🆕 Opportunities for new data

### Tip 4: Export for Gephi

Network graph JSON can be converted to formats for tools like Gephi, Cytoscape, or NetworkX:

```python
import json
import networkx as nx

with open('link_network.json') as f:
    data = json.load(f)

G = nx.DiGraph()
for focal point in data['nodes']:
    G.add_node(focal point['id'], **focal point)
for edge in data['edges']:
    G.add_edge(edge['source'], edge['target'], **edge)

nx.write_gml(G, 'network.gml')  # For Gephi
```

### Tip 5: Search Network Efficiently

In the dashboard, use the search box to find:
- Specific domains: `nasa.gov`
- File types: `.md`, `.yaml`
- Categories: `CERN`, `NOAA`

---

## 🐛 Troubleshooting

### Problem: "No links found"
**Solution:** Check that you're in the repository root directory.

### Problem: "Dashboard shows 'Error loading data'"
**Solution:** 
1. Ensure `link_network.json` exists in same directory as HTML
2. Check browser console (F12) for specific error
3. Verify JSON is valid: `python -m json.tool link_network.json`

### Problem: "Harvester is slow"
**Solution:** 
- Skip binary files (they're already excluded)
- Exclude large JSON files from scanning
- Run on subset: `python link_harvester_core.py --repo-path ./specific_dir`

### Problem: "Graph is too cluttered"
**Solution:**
- Use `--type domain-only` for simpler view
- Filter CSV by category before analyzing
- Adjust physics settings in dashboard JavaScript

---

## 📖 Next Steps

1. ✅ **Run basic harvest** - Get familiar with output
2. ✅ **Explore dashboard** - See the network visually
3. ✅ **Review registry** - Check `external_data_sources_registry.yaml`
4. ✅ **Read full docs** - See `LINK_INTELLIGENCE_REPORT.md`
5. ✅ **Enable automation** - Let GitHub Actions run daily

---

## 🎉 What You've Built

By using this system, you now have:

✅ **Complete link inventory** of your repository  
✅ **Network map** showing scientific connections  
✅ **Automated monitoring** via GitHub Actions  
✅ **Interactive dashboard** for exploration  
✅ **Export formats** for any analysis tool  
✅ **Registry** of 43+ external data sources  

**You've built the meta-intelligence layer for the  Portal!**

---

## 📞 Need Help?

- **Full Documentation:** [LINK_INTELLIGENCE_REPORT.md](LINK_INTELLIGENCE_REPORT.md)
- **External Sources:** [external_data_sources_registry.yaml](external_data_sources_registry.yaml)
- **Main README:** [README.md](README.md)
- **Contact:** CARLDCLINE@GMAIL.COM

---

**"Mapping the connections that power discovery."**  
—  Link Intelligence Network

*Part of the  Portal by Carl Dean Cline Sr., Lincoln, Nebraska*
