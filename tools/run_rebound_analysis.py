import pandas as pd
import numpy as np
from datetime import datetime
from scipy.optimize import lsq_linear
import matplotlib.pyplot as plt
import os

# === Config ===
DATA_IN = "data/extended_heartbeat_log_2025.csv"
RESULTS_CSV = f"results/rebound_fit_{datetime.utcnow().strftime('%Y%m%d')}.csv"
REPORT_MD = f"reports/rebound_fit_summary_{datetime.utcnow().strftime('%Y%m%d')}.md"

# === 1. Load Data ===
df = pd.read_csv(DATA_IN)
# Expected columns: ['UTC', 'chi', 'density', 'speed', 'bz_gsm', ... plus OMNI driver columns]

def compute_electric_field(row):
    # E = -V * Bz * 1e-3   [V: km/s, Bz: nT] → [mV/m]
    try:
        return -row['speed'] * row['bz_gsm'] * 1e-3
    except Exception:
        return np.nan

def compute_pressure(row):
    # If possible, use formula with alpha/proton ratio; else use simple form
    try:
        Na_Np = row.get('alpha_proton_ratio', np.nan)
        if not np.isnan(Na_Np):
            return 1.67e-6 * row['density'] * row['speed'] ** 2 * (1 + 4 * Na_Np)
        else:
            return 2e-6 * row['density'] * row['speed'] ** 2
    except Exception:
        return np.nan

df['E_field'] = df.apply(compute_electric_field, axis=1)
df['pressure'] = df.apply(compute_pressure, axis=1)
df['sigma_V'] = df.get('rms_speed', np.nan)  # Use OMNI RMS field, or add logic if column name differs

# === 2. Identify Rebound Events ===
events = []
window_max = 12  # Maximum hours for rebound search
chi_cap = 0.15

for idx in range(len(df)):
    if df.loc[idx, 'chi'] < chi_cap:
        # Find next index where chi >= chi_cap, within window_max hours
        for j in range(1, window_max + 1):
            if idx + j < len(df) and df.loc[idx + j, 'chi'] >= chi_cap:
                t0 = df.loc[idx, 'UTC']
                chi_0 = df.loc[idx, 'chi']
                t_r = df.loc[idx + j, 'UTC']
                chi_r = df.loc[idx + j, 'chi']
                s = (chi_r - chi_0) / j  # Recovery slope
                # Driver metrics over window
                window = df.iloc[idx:idx + j + 1]
                event = {
                    't_nadir': t0,
                    'chi_nadir': chi_0,
                    't_recover': t_r,
                    'slope': s,
                    'E_peak': window['E_field'].abs().max(),
                    'P_mean': window['pressure'].mean(),
                    'sigmaV_mean': window['sigma_V'].mean(),
                }
                events.append(event)
                break

event_df = pd.DataFrame(events)
event_df.to_csv(RESULTS_CSV, index=False)

# === 3. Fit Constrained Linear Model ===
X = event_df[['E_peak', 'P_mean', 'sigmaV_mean']].values
y = event_df['slope'].values
# Enforce s >= 0
bounds = (0, np.inf)
res = lsq_linear(X, y, bounds=bounds)
coef = res.x

# === 4. Generate Plots ===
plt.figure(figsize=(8, 5))
plt.scatter(event_df['E_peak'], event_df['slope'], alpha=0.6, label="Events")
plt.plot(event_df['E_peak'], coef[0] * event_df['E_peak'], color='r', label="Regression")
plt.xlabel('|E_peak| [mV/m]')
plt.ylabel('Recovery Slope')
plt.title('Rebound Slope vs Peak Electric Field')
plt.legend()
plot1_file = f"results/rebound_fit_plot1_{datetime.utcnow().strftime('%Y%m%d')}.png"
plt.savefig(plot1_file)
plt.close()

# === 5. Write Markdown Summary ===
with open(REPORT_MD, "w") as f:
    f.write(f"# Rebound Fit Results – {datetime.utcnow().strftime('%Y-%m-%d')}\n\n")
    f.write(f"**Events analyzed:** {len(event_df)}\n\n")
    f.write(f"**Model coefficients (slope = a|E| + bP + cσV):**\n")
    f.write(f"- a (|E|): {coef[0]:.4g}\n")
    f.write(f"- b (P): {coef[1]:.4g}\n")
    f.write(f"- c (σV): {coef[2]:.4g}\n\n")
    f.write(f"**See plot:** ![]({plot1_file})\n\n")
    f.write("## Event Table\n\n")
    f.write(event_df.to_markdown(index=False))
    f.write("\n")

print(f"Done! Events saved to {RESULTS_CSV}; summary to {REPORT_MD}; plot to {plot1_file}")
