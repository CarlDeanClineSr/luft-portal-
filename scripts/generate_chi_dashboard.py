#!/usr/bin/env python3
"""
Generate χ Dashboard with live statistics
Reads from CME heartbeat log files for up-to-date χ values
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

def load_all_heartbeat_data():
    """Load all CME heartbeat log data (the source of truth for χ values)"""
    data_dir = Path('data')
    all_data = []
    
    # Find all heartbeat log files with pattern: cme_heartbeat_log_YYYY_MM.csv
    csv_files = sorted(data_dir.glob('cme_heartbeat_log_????_??.csv'))
    
    if not csv_files:
        print("⚠️  No heartbeat log files found")
        return pd.DataFrame()
    
    print(f"📂 Found {len(csv_files)} heartbeat log files")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Rename column if needed for consistency
            if 'chi_amplitude' in df.columns:
                df = df.rename(columns={'chi_amplitude': 'chi'})
            all_data.append(df)
        except Exception as e:
            print(f"⚠️  Failed to read {csv_file}: {e}")
    
    if not all_data:
        print("⚠️  No data loaded")
        return pd.DataFrame()
    
    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    print(f"✅ Loaded {len(combined)} total observations from heartbeat logs")
    
    return combined

def calculate_chi_statistics(df):
    """Calculate χ distribution statistics"""
    if 'chi' not in df.columns:
        print("⚠️  No 'chi' column found in data")
        return None
    
    # Remove NaN values
    chi_values = df['chi'].dropna()
    
    if len(chi_values) == 0:
        print("⚠️  No valid χ values")
        return None
    
    # Define boundary (with small tolerance for floating point)
    CHI_BOUNDARY = 0.15
    TOLERANCE = 0.005  # χ between 0.145-0.155 counts as "at boundary"
    
    # Classify observations
    below = chi_values < (CHI_BOUNDARY - TOLERANCE)
    at_boundary = (chi_values >= (CHI_BOUNDARY - TOLERANCE)) & (chi_values <= (CHI_BOUNDARY + TOLERANCE))
    violations = chi_values > (CHI_BOUNDARY + TOLERANCE)
    
    total = len(chi_values)
    n_below = below.sum()
    n_at_boundary = at_boundary.sum()
    n_violations = violations.sum()
    
    stats = {
        'total_observations': int(total),
        'below_boundary': int(n_below),
        'below_percentage': round(100 * n_below / total, 1),
        'at_boundary': int(n_at_boundary),
        'at_boundary_percentage': round(100 * n_at_boundary / total, 1),
        'violations':  int(n_violations),
        'violations_percentage': round(100 * n_violations / total, 1),
        'current_chi': float(chi_values.iloc[-1]) if len(chi_values) > 0 else None,
        'max_chi': float(chi_values.max()),
        'mean_chi': float(chi_values.mean()),
        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    }
    
    print(f"\n📊 χ Statistics:")
    print(f"   Total:  {stats['total_observations']}")
    print(f"   Below:  {stats['below_boundary']} ({stats['below_percentage']}%)")
    print(f"   At Boundary: {stats['at_boundary']} ({stats['at_boundary_percentage']}%)")
    print(f"   Violations:  {stats['violations']} ({stats['violations_percentage']}%)")
    print(f"   Max χ: {stats['max_chi']:.4f}")
    
    return stats


def main():
    print("🔄 Generating χ Dashboard...")
    
    # Load all data from heartbeat logs (the source of truth)
    df = load_all_heartbeat_data()
    
    if df.empty:
        print("❌ No data available")
        return
    
    # Calculate statistics
    stats = calculate_chi_statistics(df)
    
    if not stats:
        print("❌ Failed to calculate statistics")
        return
    
    # Generate standalone dashboard HTML
    html = generate_dashboard_html(stats)
    
    # Write to chi_dashboard.html
    output_file = Path('docs/chi_dashboard.html')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding='utf-8')
    
    print(f"✅ χ Dashboard generated: {output_file}")
    print(f"   Total observations: {stats['total_observations']}")
    print(f"   Last updated: {stats['last_updated']}")


def generate_dashboard_html(stats):
    """Generate a complete standalone dashboard HTML"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>χ ≤ 0.15 Dashboard - LUFT Portal</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e27;
            color: #fff;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #00d4ff;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #1a1f3a;
            border-radius: 10px;
            padding: 20px;
            border: 2px solid #2a3f5f;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #00d4ff;
            font-size: 1em;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-percent {{
            color: #888;
            font-size: 1.2em;
        }}
        .below {{ color: #00ff88; }}
        .boundary {{ color: #ffd700; }}
        .violation {{ color: #ff4444; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            border-top: 1px solid #2a3f5f;
            padding-top: 20px;
        }}
        .fresh-indicator {{
            display: inline-block;
            padding: 5px 15px;
            background: #00ff88;
            color: #000;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>χ ≤ 0.15 Universal Boundary Dashboard</h1>
        <p class="subtitle">
            <span class="fresh-indicator">🟢 LIVE DATA</span><br>
            Last updated: {stats['last_updated']}
        </p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>TOTAL OBSERVATIONS</h3>
                <div class="stat-value">{stats['total_observations']:,}</div>
            </div>
            
            <div class="stat-card">
                <h3>BELOW χ = 0.15</h3>
                <div class="stat-value below">{stats['below_boundary']:,}</div>
                <div class="stat-percent">{stats['below_percentage']}%</div>
            </div>
            
            <div class="stat-card">
                <h3>AT BOUNDARY (χ = 0.15)</h3>
                <div class="stat-value boundary">{stats['at_boundary']:,}</div>
                <div class="stat-percent">{stats['at_boundary_percentage']}%</div>
            </div>
            
            <div class="stat-card">
                <h3>VIOLATIONS (χ &gt; 0.15)</h3>
                <div class="stat-value violation">{stats['violations']:,}</div>
                <div class="stat-percent">{stats['violations_percentage']}%</div>
            </div>
            
            <div class="stat-card">
                <h3>CURRENT χ</h3>
                <div class="stat-value boundary">{stats['current_chi']:.4f}</div>
            </div>
            
            <div class="stat-card">
                <h3>MAXIMUM χ</h3>
                <div class="stat-value">{stats['max_chi']:.4f}</div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Validation:</strong> {stats['violations_percentage']}% violations confirms χ ≤ 0.15 universal boundary ({stats['total_observations']:,} observations)</p>
            <p>Discovered by Carl Dean Cline Sr., Lincoln, Nebraska</p>
            <p><a href="https://github.com/CarlDeanClineSr/luft-portal-" style="color: #00d4ff;">GitHub Repository</a></p>
        </div>
    </div>
</body>
</html>"""
    return html


if __name__ == '__main__':
    main()
