#!/usr/bin/env python3
"""
Generate Dashboard - Manifest Dashboard HTML Generator
Parses manifest_master_index.yaml and renders a color-coded HTML dashboard
for fast status viewing of all capsules.

Requirements:
- Read docs/manifest_master_index.yaml
- Parse capsule data
- Generate color-coded HTML table (green=active, yellow=draft, red=deprecated, etc.)
- Output to docs/manifest_dashboard.html

Usage:
    python scripts/generate_dashboard.py
"""

import os
import sys
import yaml
from datetime import datetime, timezone
from typing import Dict, List, Any

# Configuration
INPUT_FILE = "docs/manifest_master_index.yaml"
OUTPUT_FILE = "docs/manifest_dashboard.html"

# Status color mapping (Bootstrap-style colors)
STATUS_COLORS = {
    "active": {"bg": "#d4edda", "border": "#c3e6cb", "text": "#155724", "label": "Active"},
    "adopted": {"bg": "#d1f2eb", "border": "#c3e6cb", "text": "#0d6832", "label": "Adopted"},
    "final": {"bg": "#cfe2ff", "border": "#b6d4fe", "text": "#084298", "label": "Final"},
    "draft": {"bg": "#fff3cd", "border": "#ffeaa7", "text": "#856404", "label": "Draft"},
    "archived": {"bg": "#d1ecf1", "border": "#bee5eb", "text": "#0c5460", "label": "Archived"},
    "deprecated": {"bg": "#f8d7da", "border": "#f5c6cb", "text": "#721c24", "label": "Deprecated"},
    "experimental": {"bg": "#e2e3e5", "border": "#d6d8db", "text": "#383d41", "label": "Experimental"},
    "template": {"bg": "#f3e5f5", "border": "#e1bee7", "text": "#6a1b9a", "label": "Template"},
    "unknown": {"bg": "#f8f9fa", "border": "#dee2e6", "text": "#6c757d", "label": "Unknown"},
}


def load_master_index(filepath: str) -> Dict[str, Any]:
    """Load the manifest master index YAML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except FileNotFoundError:
        print(f"ERROR: Index file not found: {filepath}")
        print("Please run capsule_index_job.py first to generate the index.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read index file: {e}")
        sys.exit(1)


def get_status_color(status: str) -> Dict[str, str]:
    """Get color scheme for a given status"""
    return STATUS_COLORS.get(status.lower(), STATUS_COLORS["unknown"])


def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def generate_html_dashboard(index_data: Dict[str, Any]) -> str:
    """Generate HTML dashboard from index data"""
    
    metadata = index_data.get("metadata", {})
    statistics = index_data.get("statistics", {})
    capsules = index_data.get("capsules", [])
    
    # Sort capsules by status priority, then date (newest first)
    status_priority = {"active": 0, "final": 1, "adopted": 2, "experimental": 3, "draft": 4, "template": 5, "archived": 6, "deprecated": 7}
    
    def sort_key(c):
        priority = status_priority.get(c.get("status", "unknown"), 999)
        date_val = c.get("date", "") or ""
        # Parse date for proper sorting
        try:
            date_obj = datetime.strptime(date_val, "%Y-%m-%d")
            date_sort = -date_obj.timestamp()  # Negative for descending order
        except (ValueError, AttributeError):
            date_sort = 0
        return (priority, date_sort, c.get("id", ""))
    
    sorted_capsules = sorted(capsules, key=sort_key)
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LUFT Portal - Capsule Manifest Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f7fafc;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-card .label {{
            font-size: 0.9em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 25px;
            padding: 20px;
            background: #f7fafc;
            border-radius: 8px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-badge {{
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            border: 1px solid;
        }}
        
        .table-container {{
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #2d3748;
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        tbody tr {{
            border-bottom: 1px solid #e2e8f0;
            transition: background-color 0.2s;
        }}
        
        tbody tr:hover {{
            background: #f7fafc;
        }}
        
        td {{
            padding: 15px;
            font-size: 0.95em;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            border: 1px solid;
        }}
        
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .tag {{
            display: inline-block;
            padding: 4px 8px;
            background: #e2e8f0;
            color: #2d3748;
            border-radius: 3px;
            font-size: 0.8em;
        }}
        
        .footer {{
            padding: 20px 30px;
            background: #f7fafc;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #718096;
            font-size: 0.9em;
        }}
        
        .capsule-id {{
            font-family: "Courier New", monospace;
            font-weight: 600;
            color: #2d3748;
        }}
        
        .filepath {{
            font-family: "Courier New", monospace;
            font-size: 0.85em;
            color: #718096;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .stats {{
                grid-template-columns: 1fr;
            }}
            
            th, td {{
                padding: 10px;
                font-size: 0.85em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 LUFT Portal</h1>
            <p>Capsule Manifest Dashboard — Live Status View</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="number">{metadata.get('total_capsules', 0)}</div>
                <div class="label">Total Capsules</div>
            </div>
            <div class="stat-card">
                <div class="number">{statistics.get('by_status', {}).get('active', 0)}</div>
                <div class="label">Active</div>
            </div>
            <div class="stat-card">
                <div class="number">{statistics.get('by_status', {}).get('draft', 0)}</div>
                <div class="label">Draft</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(statistics.get('by_author', {}))}</div>
                <div class="label">Authors</div>
            </div>
            <div class="stat-card">
                <div class="number">{statistics.get('total_tags', 0)}</div>
                <div class="label">Total Tags</div>
            </div>
        </div>
        
        <div class="content">
            <div class="legend">
                <strong style="margin-right: 10px;">Legend:</strong>
"""
    
    # Add legend items
    for status, colors in STATUS_COLORS.items():
        if status != "unknown":
            html += f"""                <div class="legend-item">
                    <span class="legend-badge" style="background-color: {colors['bg']}; border-color: {colors['border']}; color: {colors['text']};">
                        {colors['label']}
                    </span>
                </div>
"""
    
    html += """            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Version</th>
                            <th>Date</th>
                            <th>Author</th>
                            <th>Tags</th>
                            <th>Source</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Add table rows - use list for better performance than string concatenation
    table_rows = []
    for capsule in sorted_capsules:
        status = capsule.get("status", "unknown")
        colors = get_status_color(status)
        
        capsule_id = escape_html(capsule.get("id", "N/A"))
        title = escape_html(capsule.get("title", "N/A"))
        version = escape_html(capsule.get("version", "1.0.0"))
        date = escape_html(capsule.get("date", "N/A"))
        author = escape_html(capsule.get("author", "N/A"))
        tags = capsule.get("tags", [])
        filepath = escape_html(capsule.get("filepath", "N/A"))
        
        # Build tag HTML efficiently using list comprehension
        tag_html_parts = [
            f'                                    <span class="tag">{escape_html(str(tag))}</span>\n' 
            for tag in tags[:5]
        ]
        if len(tags) > 5:
            tag_html_parts.append(f'                                    <span class="tag">+{len(tags) - 5} more</span>\n')
        
        tag_html = ''.join(tag_html_parts)
        
        # Build complete row
        row_html = f"""                        <tr>
                            <td>
                                <span class="status-badge" style="background-color: {colors['bg']}; border-color: {colors['border']}; color: {colors['text']};">
                                    {colors['label']}
                                </span>
                            </td>
                            <td><span class="capsule-id">{capsule_id}</span></td>
                            <td><strong>{title}</strong></td>
                            <td>{version}</td>
                            <td>{date}</td>
                            <td>{author}</td>
                            <td>
                                <div class="tags">
{tag_html}                                </div>
                            </td>
                            <td><span class="filepath">{filepath}</span></td>
                        </tr>
"""
        table_rows.append(row_html)
    
    # Join all rows at once for better performance
    html += ''.join(table_rows)
    
    # If no capsules
    if not sorted_capsules:
        # Count table columns dynamically
        num_columns = 8  # Status, ID, Title, Version, Date, Author, Tags, Source
        html += f"""                        <tr>
                            <td colspan="{num_columns}" style="text-align: center; padding: 40px; color: #718096;">
                                No capsules found. Run capsule_index_job.py to generate the index.
                            </td>
                        </tr>
"""
    
    # Close HTML
    generated_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html += f"""                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated at {generated_time} by LUFT Portal Dashboard Generator</p>
            <p>Source: {INPUT_FILE} | Total Capsules: {len(sorted_capsules)}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def main():
    """Main execution function"""
    print("=" * 70)
    print("LUFT Portal — Dashboard Generator")
    print("=" * 70)
    print()
    
    # Load master index
    print(f"Loading master index from {INPUT_FILE}...")
    index_data = load_master_index(INPUT_FILE)
    print(f"  Total capsules: {index_data.get('metadata', {}).get('total_capsules', 0)}")
    
    # Generate HTML
    print("\nGenerating HTML dashboard...")
    html = generate_html_dashboard(index_data)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write output file
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Successfully generated dashboard")
    print(f"   Output file: {OUTPUT_FILE}")
    print(f"   File size: {len(html)} bytes")
    
    print("\n" + "=" * 70)
    print("Dashboard generation complete!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
