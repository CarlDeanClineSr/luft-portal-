import os
import datetime

# Simple template
template = """
<!DOCTYPE html>
<html>
<head><title>LUFT Dashboard</title></head>
<body style="background: #000; color: #fff;">
<h1>LUFT Portal Dashboard - {timestamp}</h1>
<h2>χ Amplitude History</h2>
<img src="{chi_chart}" alt="χ Chart" width="800">
<h2>G vs χ Comparison</h2>
<img src="{g_chart}" alt="G Chart" width="800">
<!-- Add more embeds -->
<p>DOI: <a href="https://doi.org/10.17605/OSF.IO/X5M2T" style="color: #0ff;">OSF Project</a></p>
</body>
</html>
"""

output_dir = "./results/"
dashboard_path = "dashboard.html"

chi_chart = os.path.join(output_dir, "chi_timeseries_latest.png")
g_chart = os.path.join(output_dir, "g_vs_chi_comparison.png")

html = template.format(
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    chi_chart=chi_chart if os.path.exists(chi_chart) else "No chart",
    g_chart=g_chart if os.path.exists(g_chart) else "No chart"
)

with open(dashboard_path, "w") as f:
    f.write(html)

print(f"Dashboard updated: {dashboard_path}")
