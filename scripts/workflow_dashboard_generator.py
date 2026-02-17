#!/usr/bin/env python3
"""
LUFT Workflow Dashboard Generator
Generates a live HTML dashboard showing real-time status of all 6 workflows. 

Usage:
  python workflow_dashboard_generator.py

Outputs:
  workflow_dashboard.html (commit this to repo, view in browser or GitHub Pages)
"""

import requests
import json
from datetime import datetime, timedelta

# GitHub API settings
REPO_OWNER = "CarlDeanClineSr"
REPO_NAME = "luft-portal-"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

# Workflow file names (update these to match your actual workflow files)
WORKFLOWS = [
    "dscovr_solar_wind_ingest.yml",
    "cme_heartbeat_logger.yml",
    "solar_wind_audit.yml",
    "vault_narrator.yml",
    "vault_forecast.yml",
    "voyager_audit. yml"
]

# Workflow display names (prettier labels for the dashboard)
WORKFLOW_NAMES = {
    "dscovr_solar_wind_ingest. yml": "DSCOVR Solar Wind Data Ingest",
    "cme_heartbeat_logger.yml": "LUFT CME Heartbeat Logger",
    "solar_wind_audit.yml": "LUFT Solar Wind Audit",
    "vault_narrator.yml": "Vault Narrator - Auto Update",
    "vault_forecast.yml": "Hourly Vault 10-Row Forecast",
    "voyager_audit.yml": "LUFT Voyager Audit Superaction"
}

def fetch_workflow_runs(workflow_file):
    """Fetch the latest runs for a specific workflow."""
    url = f"{API_BASE}/actions/workflows/{workflow_file}/runs"
    params = {"per_page": 5, "page": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("workflow_runs", [])
    except Exception as e:
        print(f"Error fetching {workflow_file}: {e}")
        return []

def generate_dashboard_html(workflow_data):
    """Generate HTML dashboard from workflow data."""
    html = f"""
<! DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LUFT Workflow Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin:  0 auto;
        }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 30px;
            opacity: 0.9;
        }}
        .workflow-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}
        .workflow-card {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .workflow-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size:  0.9em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .status-success {{
            background: #28a745;
            color: #fff;
        }}
        . status-failure {{
            background: #dc3545;
            color: #fff;
        }}
        .status-in-progress {{
            background: #ffc107;
            color:  #000;
        }}
        .workflow-info {{
            font-size: 0.95em;
            line-height: 1.6;
        }}
        .workflow-info strong {{
            color: #ffd700;
        }}
        . footer {{
            text-align: center;
            margin-top: 40px;
            font-size:  0.9em;
            opacity: 0.7;
        }}
        .timestamp {{
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.1em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 LUFT Workflow Dashboard</h1>
        <div class="subtitle">Real-Time Status of Automated Data Pipelines</div>
        <div class="timestamp">Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        
        <div class="workflow-grid">
"""

    for workflow_file, data in workflow_data.items():
        workflow_name = WORKFLOW_NAMES.get(workflow_file, workflow_file)
        if not data:
            html += f"""
            <div class="workflow-card">
                <div class="workflow-title">{workflow_name}</div>
                <span class="status-badge" style="background: #6c757d;">No Data</span>
                <div class="workflow-info">
                    <p>Unable to fetch workflow data. </p>
                </div>
            </div>
"""
            continue

        latest_run = data[0]
        status = latest_run.get("conclusion", "in_progress")
        status_label = "✅ SUCCESS" if status == "success" else "❌ FAILURE" if status == "failure" else "🔄 IN PROGRESS"
        status_class = "status-success" if status == "success" else "status-failure" if status == "failure" else "status-in-progress"
        
        run_time_str = latest_run.get("created_at", "N/A")
        try:
            run_time = datetime.strptime(run_time_str, "%Y-%m-%dT%H:%M:%SZ")
            time_ago = datetime.utcnow() - run_time
            if time_ago.total_seconds() < 3600:
                time_ago_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
            elif time_ago.total_seconds() < 86400:
                time_ago_str = f"{int(time_ago.total_seconds() / 3600)} hours ago"
            else:
                time_ago_str = f"{int(time_ago.total_seconds() / 86400)} days ago"
        except:
            time_ago_str = "N/A"

        html += f"""
            <div class="workflow-card">
                <div class="workflow-title">{workflow_name}</div>
                <span class="status-badge {status_class}">{status_label}</span>
                <div class="workflow-info">
                    <p><strong>Last Run:</strong> {time_ago_str}</p>
                    <p><strong>Branch:</strong> {latest_run. get('head_branch', 'N/A')}</p>
                    <p><strong>Trigger:</strong> {latest_run. get('event', 'N/A')}</p>
                    <p><strong>Run ID:</strong> #{latest_run.get('run_number', 'N/A')}</p>
                </div>
            </div>
"""

    html += """
        </div>
        
        <div class="footer">
            <p>Generated by <strong>workflow_dashboard_generator.py</strong></p>
            <p>Part of the LUFT Portal automated research laboratory</p>
            <p>Maintained by Captain Carl Dean Cline Sr & Arti (AI co-pilot)</p>
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    print("🔐 Generating LUFT Workflow Dashboard...")
    
    workflow_data = {}
    for workflow in WORKFLOWS:
        print(f"  Fetching {workflow}...")
        runs = fetch_workflow_runs(workflow)
        workflow_data[workflow] = runs
    
    html = generate_dashboard_html(workflow_data)
    
    output_file = "workflow_dashboard.html"
    with open(output_file, "w") as f:
        f.write(html)
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"   Open in browser or commit to GitHub Pages for live view.")

if __name__ == "__main__":
    main()
