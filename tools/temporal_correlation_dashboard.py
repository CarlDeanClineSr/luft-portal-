#!/usr/bin/env python3
"""
Temporal Correlation Dashboard Generator

Creates an interactive dashboard showing real-time predictions
based on the 13 temporal correlation modes.

Author: Carl Dean Cline Sr.
Date: January 1, 2026
"""

import json
from datetime import datetime, timedelta
import sys
import os

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

try:
    from chi_predictor import (
        predict_chi_response, 
        validate_dec28_event,
        get_discovery_summary,
        CORRELATION_MODES,
        TOTAL_MATCHES
    )
except ImportError:
    print("Error: Could not import chi_predictor. Make sure tools/chi_predictor.py exists.")
    sys.exit(1)


def generate_html_dashboard(output_path="/home/runner/work/luft-portal-/luft-portal-/temporal_correlation_dashboard.html"):
    """Generate an HTML dashboard for temporal correlations."""
    
    # Get current predictions for "now"
    current_time = datetime.utcnow()
    predictions = predict_chi_response(current_time.strftime("%Y-%m-%d %H:%M:%S UTC"))
    
    # Get discovery summary
    summary = get_discovery_summary()
    
    # Get validation
    validation = validate_dec28_event()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Temporal Correlation Dashboard - LUFT Portal</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #e0e0e0;
            padding: 2rem;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, #1a0a0a 0%, #0a1a1a 100%);
            border: 3px solid #fbbf24;
            border-radius: 16px;
        }}
        
        .header h1 {{
            color: #fbbf24;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            color: #4da3ff;
            font-size: 1.2rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: #1a1a1a;
            border: 2px solid #4da3ff;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #fbbf24;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #b0b0b0;
            font-size: 1rem;
        }}
        
        .correlation-table {{
            width: 100%;
            background: #1a1a1a;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 2rem;
        }}
        
        .correlation-table table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .correlation-table th {{
            background: #2a2a2a;
            color: #4da3ff;
            padding: 1rem;
            text-align: left;
            font-weight: bold;
        }}
        
        .correlation-table td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .correlation-table tr:hover {{
            background: #2a2a2a;
        }}
        
        .phase-immediate {{ background: rgba(77, 163, 255, 0.1); }}
        .phase-rising {{ background: rgba(77, 163, 255, 0.1); }}
        .phase-peak {{ background: rgba(248, 113, 113, 0.2); font-weight: bold; }}
        .phase-storm {{ background: rgba(251, 191, 36, 0.1); }}
        .phase-recovery {{ background: rgba(74, 222, 128, 0.1); }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
        }}
        
        .badge-high {{ background: #f87171; color: white; }}
        .badge-moderate {{ background: #fbbf24; color: black; }}
        .badge-low {{ background: #4ade80; color: black; }}
        
        .validation-box {{
            background: #001a1a;
            border: 3px solid #4ade80;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .validation-box h2 {{
            color: #4ade80;
            margin-bottom: 1rem;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }}
        
        .chart-container {{
            background: #1a1a1a;
            border: 2px solid #4da3ff;
            border-radius: 12px;
            padding: 1rem;
        }}
        
        .chart-container img {{
            width: 100%;
            border-radius: 8px;
        }}
        
        .chart-title {{
            color: #4da3ff;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 Temporal Correlation Dashboard</h1>
        <div class="subtitle">13 Response Modes • 1.47M Matches • 95% Confidence</div>
        <div style="color: #9ca3af; margin-top: 0.5rem;">Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{TOTAL_MATCHES:,}</div>
            <div class="stat-label">Total Correlation Matches</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">13</div>
            <div class="stat-label">Temporal Response Modes</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">24h</div>
            <div class="stat-label">Peak Correlation (144K matches)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">95%</div>
            <div class="stat-label">Confidence Level</div>
        </div>
    </div>
    
    <div class="validation-box">
        <h2>✅ December 28, 2025 Event Validation</h2>
        <p><strong>NOAA Detection:</strong> {validation['noaa_detection']}</p>
        <p><strong>χ Response:</strong> {validation['chi_response']}</p>
        <p><strong>Actual Delay:</strong> {validation['actual_delay_hours']} hours</p>
        <p><strong>Matched Correlation:</strong> #{validation['matching_correlation']}h delay ({validation['historical_matches']:,} historical matches)</p>
        <p><strong>Status:</strong> <span style="color: #4ade80; font-weight: bold;">{validation['validation_status']}</span></p>
        <p style="margin-top: 1rem;"><em>{validation['description']}</em></p>
    </div>
    
    <div class="correlation-table">
        <h2 style="color: #4da3ff; padding: 1rem; background: #2a2a2a;">13 Temporal Correlation Modes</h2>
        <table>
            <thead>
                <tr>
                    <th>Delay</th>
                    <th>Description</th>
                    <th>Storm Phase</th>
                    <th>Matches</th>
                    <th>Confidence</th>
                    <th>Warning Level</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add table rows for each correlation mode
    for pred in predictions:
        delay = pred['delay_hours']
        
        # Determine phase class
        if delay <= 6:
            phase_class = 'phase-immediate'
        elif delay <= 18:
            phase_class = 'phase-rising'
        elif delay == 24:
            phase_class = 'phase-peak'
        elif delay <= 48:
            phase_class = 'phase-storm'
        else:
            phase_class = 'phase-recovery'
        
        # Warning badge
        warning_level = pred['warning_level']
        badge_class = f'badge-{warning_level.lower()}'
        
        html_content += f"""
                <tr class="{phase_class}">
                    <td><strong>{delay}h</strong></td>
                    <td>{pred['description']}</td>
                    <td>{pred['storm_phase']}</td>
                    <td>{pred['historical_matches']:,}</td>
                    <td>{pred['confidence']:.1%}</td>
                    <td><span class="badge {badge_class}">{warning_level}</span></td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
    </div>
    
    <h2 style="color: #4da3ff; margin-bottom: 1rem; font-size: 1.8rem;">📊 Visualizations</h2>
    
    <div class="charts-grid">
        <div class="chart-container">
            <div class="chart-title">Correlation Modes Bar Chart</div>
            <img src="charts/temporal_correlations/correlation_modes_barchart.png" alt="Correlation Modes">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Response Timeline</div>
            <img src="charts/temporal_correlations/correlation_timeline.png" alt="Timeline">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Phase Distribution</div>
            <img src="charts/temporal_correlations/phase_distribution.png" alt="Phase Distribution">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">December 28 Validation</div>
            <img src="charts/temporal_correlations/dec28_validation.png" alt="Validation">
        </div>
    </div>
    
    <div style="background: #1a1a1a; border: 2px solid #4da3ff; border-radius: 12px; padding: 2rem; margin-top: 2rem; text-align: center;">
        <h3 style="color: #4da3ff; margin-bottom: 1rem;">🔗 Resources</h3>
        <p>
            <a href="index.html" style="color: #4da3ff; margin: 0 1rem;">Main Portal</a> |
            <a href="instrument-panel.html" style="color: #4da3ff; margin: 0 1rem;">Cockpit View</a> |
            <a href="TEMPORAL_CORRELATION_DISCOVERY.md" style="color: #4da3ff; margin: 0 1rem;">Full Report</a>
        </p>
        <p style="margin-top: 1rem; color: #9ca3af;">
            LUFT Portal • Carl Dean Cline Sr. • Lincoln, Nebraska
        </p>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated: {output_path}")
    return output_path


def main():
    """Main function."""
    print("=" * 70)
    print("TEMPORAL CORRELATION DASHBOARD GENERATOR")
    print("=" * 70)
    print()
    
    output_path = generate_html_dashboard()
    
    print()
    print("✅ Dashboard ready!")
    print(f"   Open: {output_path}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
