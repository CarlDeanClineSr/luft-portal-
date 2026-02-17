import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression

# Load your CSV
df = pd.read_csv("cme_heartbeat_log_2025_12.csv")

# Compute dynamic pressure (nPa)
P_dyn = df['density_p_cm3'] * (df['speed_km_s']**2) * 1.6726e-6
chi = df['chi_amplitude']

# Figure 1: Saturation Law Fit
def saturation(P_dyn, chi_max, k, chi0):
    return chi_max * (1 - np.exp(-k * P_dyn)) + chi0

params, _ = curve_fit(saturation, P_dyn, chi, p0=[0.15, 0.003, 0.055])
chi_max, k, chi0 = params

plt.figure(figsize=(8,6))
plt.scatter(P_dyn, chi, color='blue', label='Observed χ')
P_fit = np.linspace(min(P_dyn), max(P_dyn), 200)
plt.plot(P_fit, saturation(P_fit, chi_max, k, chi0), color='red', label='Saturation fit')
plt.xlabel('Dynamic Pressure (proxy)')
plt.ylabel('χ Amplitude')
plt.title('Figure 1 — Saturation Law Fit')
plt.legend()
plt.savefig('figure1_saturation.png', dpi=300)
plt.close()

# Figure 2: Hysteresis Term Fit
df['chi_next'] = df['chi_amplitude'].shift(-1)
valid = df.dropna()
X = np.column_stack([valid['chi_amplitude'], P_dyn.loc[valid.index]])
y = valid['chi_next']
model = LinearRegression().fit(X, y)
alpha, k_lin = model.coef_

plt.figure(figsize=(8,6))
plt.scatter(valid['chi_amplitude'], valid['chi_next'], color='blue', label='Observed χ(t+1)')
plt.plot(valid['chi_amplitude'], model.predict(X), color='green', label=f'Hysteresis fit (α={alpha:.2f})')
plt.xlabel('χ(t)')
plt.ylabel('χ(t+1)')
plt.title('Figure 2 — Hysteresis Term Fit')
plt.legend()
plt.savefig('figure2_hysteresis.png', dpi=300)
plt.close()

# Figure 3: Magnetic Gain Term Fit
P_star = P_dyn * (1 + (-df['bz_nT'])/(1+np.abs(df['bz_nT'])))
model_mag = LinearRegression().fit(P_star.values.reshape(-1,1), chi)

plt.figure(figsize=(8,6))
plt.scatter(P_star, chi, color='blue', label='Observed χ')
plt.plot(P_star, model_mag.predict(P_star.values.reshape(-1,1)), color='orange', label='Magnetic gain fit')
plt.xlabel('Effective Pressure P*')
plt.ylabel('χ Amplitude')
plt.title('Figure 3 — Magnetic Gain Term Fit')
plt.legend()
plt.savefig('figure3_magnetic.png', dpi=300)
plt.close()

# Figure 4: Phase Coherence Plot
plt.figure(figsize=(10,6))
plt.scatter(pd.to_datetime(df['timestamp_utc']), df['phase_radians'], color='blue')
plt.xlabel('Timestamp UTC')
plt.ylabel('Phase (radians)')
plt.title('Figure 4 — Phase Coherence Plot')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('figure4_phase.png', dpi=300)
plt.close()

print("Figures generated: figure1_saturation.png, figure2_hysteresis.png, figure3_magnetic.png, figure4_phase.png")
