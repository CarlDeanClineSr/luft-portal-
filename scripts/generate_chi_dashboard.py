#!/usr/bin/env python3
"""
Generate real-time χ dashboard with multi-station data, Dst comparison, and historical events.
Outputs static HTML to docs/chi_dashboard.html
"""

import pandas as pd
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import glob
import sys

def load_latest_dscovr():
    """Load last 7 days of DSCOVR solar wind data."""
    dscovr_dir = Path('data/dscovr')
    if not dscovr_dir.exists():
        return None
    
    files = sorted(dscovr_dir.glob('*.csv'))[-7:]
    if not files:
        # Try JSON format
        json_files = sorted(dscovr_dir.glob('*.json'))
        if json_files:
            try:
                with open(json_files[-1]) as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'bt' in data:
                        return pd.DataFrame([data])
            except:
                pass
        return None
    
    try:
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return None

def load_latest_usgs_multi():
    """Load last 7 days of multi-station USGS magnetometer data."""
    stations = {}
    usgs_base = Path('data/usgs_magnetometer')
    
    if not usgs_base.exists():
        return stations
    
    # Get top 6 stations for display
    priority_stations = ['BOU', 'FRD', 'HON', 'TUC', 'SIT', 'CMO']
    
    for station in priority_stations:
        station_dir = usgs_base / station
        if not station_dir.exists():
            continue
        
        files = sorted(station_dir.glob('*.json'))[-7:]
        if not files:
            continue
        
        # Parse JSON and extract magnetic field
        data_points = []
        for f in files:
            try:
                with open(f) as fp:
                    d = json.load(fp)
                    times = d.get('times', [])
                    values = d.get('values', [])
                    
                    # Find F (total field) element
                    f_values = None
                    for elem in values:
                        if elem.get('id') == 'F':
                            f_values = elem.get('values', [])
                            break
                    
                    if times and f_values:
                        for i, (t, v) in enumerate(zip(times, f_values)):
                            if v is not None:
                                data_points.append({'time': t, 'F': v})
            except Exception as e:
                continue
        
        if data_points:
            stations[station] = pd.DataFrame(data_points)
    
    return stations

def load_latest_dst():
    """Load last 7 days of Dst index."""
    dst_dir = Path('data/dst_index')
    if not dst_dir.exists():
        return None
    
    files = sorted(dst_dir.glob('*.csv'))[-7:]
    if not files:
        return None
    
    try:
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    except:
        return None

def compute_chi(df, field_col='bt'):
    """Compute χ = |B - B_baseline| / B_baseline."""
    if df is None or len(df) < 100:
        return None
    
    if field_col not in df.columns:
        return None
    
    df = df.copy()
    df[field_col] = pd.to_numeric(df[field_col], errors='coerce')
    df = df.dropna(subset=[field_col])
    
    if len(df) < 100:
        return None
    
    # Compute 24-hour rolling baseline
    if len(df) >= 1440:
        baseline = df[field_col].rolling(window=1440, center=True, min_periods=100).mean()
    else:
        baseline = df[field_col].mean()
    
    df['baseline'] = baseline
    df['chi'] = (df[field_col] - df['baseline']).abs() / df['baseline']
    
    return df

def generate_html():
    """Generate dashboard HTML."""
    dscovr = load_latest_dscovr()
    usgs_multi = load_latest_usgs_multi()
    dst = load_latest_dst()
    
    # Compute χ for DSCOVR
    if dscovr is not None and 'bt' in dscovr.columns:
        dscovr = compute_chi(dscovr, 'bt')
        if dscovr is not None and len(dscovr) > 0:
            dscovr_chi_current = dscovr['chi'].iloc[-1]
            dscovr_chi_max = dscovr['chi'].max()
        else:
            dscovr_chi_current = 0
            dscovr_chi_max = 0
    else:
        dscovr_chi_current = 0
        dscovr_chi_max = 0
    
    # Compute χ for USGS stations
    usgs_chi = {}
    for station, df in usgs_multi.items():
        df_chi = compute_chi(df, 'F')
        if df_chi is not None and len(df_chi) > 0:
            usgs_chi[station] = {
                'current': df_chi['chi'].iloc[-1],
                'max': df_chi['chi'].max()
            }
    
    # Get latest Dst value
    dst_current = None
    dst_level = "Unknown"
    if dst is not None and len(dst) > 0 and 'dst' in dst.columns:
        dst_current = dst['dst'].iloc[-1]
        # Interpret storm level
        if dst_current > -30:
            dst_level = "🟢 Quiet"
        elif dst_current > -50:
            dst_level = "🟡 Minor storm (G1)"
        elif dst_current > -100:
            dst_level = "🟠 Moderate storm (G2-G3)"
        elif dst_current > -200:
            dst_level = "🔴 Strong storm (G4)"
        else:
            dst_level = "🔴 Extreme storm (G5)"
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>χ = 0.15 Plasma Oscillation Boundary Dashboard</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background: #000;
            color: #0f0;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #0ff;
            text-align: center;
            border-bottom: 2px solid #0ff;
            padding-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #0f0;
            margin-bottom: 20px;
        }}
        .monitor {{
            border: 2px solid #0f0;
            padding: 20px;
            margin: 20px 0;
            background: #001100;
        }}
        .monitor h2 {{
            color: #0ff;
            margin-top: 0;
        }}
        .nominal {{ color: #0f0; }}
        .alert {{ color: #ff0; }}
        .critical {{ color: #f00; }}
        .metric {{
            margin: 10px 0;
            padding: 5px;
        }}
        .station-row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #003300;
        }}
        .footer {{
            text-align: center;
            color: #0f0;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 2px solid #0f0;
        }}
        .chi-bar {{
            display: inline-block;
            height: 10px;
            background: #0f0;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰️ LIVE PLASMA OSCILLATION BOUNDARY MONITOR</h1>
        <div class="subtitle">
            <p>χ = |B - B_baseline| / B_baseline</p>
            <p>Critical threshold: χ = 0.15</p>
        </div>
        
        <div class="monitor">
            <h2>SOLAR WIND (DSCOVR Satellite)</h2>
            <div class="metric">Current χ: <strong>{dscovr_chi_current:.4f}</strong> ({dscovr_chi_current/0.15*100:.0f}% of threshold)</div>
            <div class="metric">24h Max χ: <strong>{dscovr_chi_max:.4f}</strong> ({dscovr_chi_max/0.15*100:.0f}% of threshold)</div>
            <div class="metric">
                <span class="{'nominal' if dscovr_chi_max < 0.12 else 'alert' if dscovr_chi_max < 0.15 else 'critical'}">
                    Status: {'🟢 NOMINAL' if dscovr_chi_max < 0.12 else '🟡 ALERT' if dscovr_chi_max < 0.15 else '🔴 CRITICAL'}
                </span>
            </div>
            <div class="chi-bar" style="width: {min(dscovr_chi_max/0.15*300, 300)}px;"></div>
        </div>
        
        <div class="monitor">
            <h2>MAGNETOSPHERE (USGS Multi-Station)</h2>
            {'<p>No station data available yet</p>' if not usgs_chi else ''}
            {''.join([
                f'<div class="station-row">'
                f'<span><strong>{s}</strong>: χ = {d["current"]:.4f} (max {d["max"]:.4f})</span>'
                f'<span class="{"nominal" if d["max"] < 0.12 else "alert" if d["max"] < 0.15 else "critical"}">'
                f'{"🟢 NOMINAL" if d["max"] < 0.12 else "🟡 ALERT" if d["max"] < 0.15 else "🔴 CRITICAL"}'
                f'</span>'
                f'</div>'
                for s, d in sorted(usgs_chi.items())
            ])}
        </div>
        
        <div class="monitor">
            <h2>GEOMAGNETIC STORM INDEX (Dst)</h2>
            <div class="metric">Current Dst: <strong>{dst_current if dst_current is not None else 'N/A'}</strong> nT</div>
            <div class="metric">Storm level: <strong>{dst_level}</strong></div>
            <div class="metric">
                <small>Reference: Dst &gt; -30 = Quiet, -30 to -50 = G1, -50 to -100 = G2-G3, -100 to -200 = G4, &lt; -200 = G5</small>
            </div>
        </div>
        
        <div class="monitor">
            <h2>HISTORICAL STORM ARCHIVE</h2>
            <div class="metric">
                <strong>1989 Quebec Blackout</strong> (Mar 13-14, 1989)<br>
                Station: FRD (Fredericksburg, VA) | Dst: -589 nT
            </div>
            <div class="metric">
                <strong>1972 Apollo-Era Storm</strong> (Aug 4, 1972)<br>
                Station: HON (Honolulu, HI) | Solar maximum event
            </div>
            <div class="metric">
                <strong>2024 May G5 Storm</strong> (May 10-11, 2024)<br>
                Station: BOU (Boulder, CO) | Recent extreme event
            </div>
            <div class="metric">
                <small>Run workflow: Historical Storm χ Analysis to compute χ values</small>
            </div>
        </div>
        
        <div class="footer">
            <p>Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p>LUFT Observatory | Plasma Boundary Research</p>
            <p><a href="https://github.com/CarlDeanClineSr/luft-portal-" style="color: #0ff;">GitHub Repository</a></p>
        </div>
    </div>
</body>
</html>
"""
    
    output_dir = Path('docs')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'chi_dashboard.html'
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✅ χ dashboard generated: {output_path}")
    return True

if __name__ == '__main__':
    success = generate_html()
    sys.exit(0 if success else 1)
