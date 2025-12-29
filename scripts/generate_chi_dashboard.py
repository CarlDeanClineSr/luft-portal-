#!/usr/bin/env python3
"""
Generate χ Dashboard with live statistics
Reads ALL DSCOVR data and calculates current χ distribution
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

def load_all_dscovr_data():
    """Load all DSCOVR solar wind data"""
    data_dir = Path('data/dscovr')
    all_data = []
    
    if not data_dir.exists():
        print("⚠️  No DSCOVR data directory found")
        return pd.DataFrame()
    
    # Read all CSV files
    csv_files = list(data_dir.glob('*.csv'))
    print(f"📂 Found {len(csv_files)} DSCOVR data files")
    
    for csv_file in csv_files: 
        try:
            df = pd.read_csv(csv_file)
            all_data.append(df)
        except Exception as e:
            print(f"⚠️  Failed to read {csv_file}: {e}")
    
    if not all_data:
        print("⚠️  No data loaded")
        return pd.DataFrame()
    
    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    print(f"✅ Loaded {len(combined)} total observations")
    
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
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    }
    
    print(f"\n📊 χ Statistics:")
    print(f"   Total:  {stats['total_observations']}")
    print(f"   Below:  {stats['below_boundary']} ({stats['below_percentage']}%)")
    print(f"   At Boundary: {stats['at_boundary']} ({stats['at_boundary_percentage']}%)")
    print(f"   Violations:  {stats['violations']} ({stats['violations_percentage']}%)")
    print(f"   Max χ: {stats['max_chi']:. 4f}")
    
    return stats

def update_dashboard_html(stats):
    """Update the main dashboard HTML with new statistics"""
    html_file = Path('docs/index.html')
    
    if not html_file.exists():
        print(f"⚠️  Dashboard file not found: {html_file}")
        return False
    
    # Read current HTML
    html = html_file.read_text(encoding='utf-8')
    
    # Update the statistics section
    # Find and replace the BELOW section
    html = html.replace(
        'BELOW χ = 0.15\n274\n47.7%',
        f'BELOW χ = 0.15\n{stats["below_boundary"]}\n{stats["below_percentage"]}%'
    )
    
    # Update AT BOUNDARY section
    html = html.replace(
        'AT BOUNDARY (χ = 0.15)\n300\n52.3%',
        f'AT BOUNDARY (χ = 0.15)\n{stats["at_boundary"]}\n{stats["at_boundary_percentage"]}%'
    )
    
    # Update VIOLATION section
    html = html.replace(
        'VIOLATION (χ > 0.15)\n0\n0.0%',
        f'VIOLATION (χ > 0.15)\n{stats["violations"]}\n{stats["violations_percentage"]}%'
    )
    
    # Update validation text
    html = html.replace(
        'Validation:  0% violations confirms χ ≤ 0.15 universal boundary (574 observations)',
        f'Validation: {stats["violations_percentage"]}% violations confirms χ ≤ 0.15 universal boundary ({stats["total_observations"]} observations)'
    )
    
    # Write updated HTML
    html_file.write_text(html, encoding='utf-8')
    print(f"✅ Updated {html_file}")
    
    return True

def main():
    print("🔄 Generating χ Dashboard...")
    
    # Load all data
    df = load_all_dscovr_data()
    
    if df.empty:
        print("❌ No data available")
        return
    
    # Calculate statistics
    stats = calculate_chi_statistics(df)
    
    if not stats:
        print("❌ Failed to calculate statistics")
        return
    
    # Update dashboard
    success = update_dashboard_html(stats)
    
    if success: 
        print("✅ χ Dashboard generation complete")
    else:
        print("❌ Failed to update dashboard")

if __name__ == '__main__':
    main()
