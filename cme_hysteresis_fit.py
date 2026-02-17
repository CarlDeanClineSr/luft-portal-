import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

# Load your CSV
df = pd.read_csv("cme_heartbeat_log_2025_12.csv")

# Define saturation model
def saturation(P_dyn, chi_max, k, chi0):
    return chi_max * (1 - np.exp(-k * P_dyn)) + chi0

# Fit saturation law
P_dyn = df['density_p_cm3'] * (df['speed_km_s']**2) * 1.6726e-6
chi = df['chi_amplitude']

params, cov = curve_fit(saturation, P_dyn, chi, p0=[0.15, 0.003, 0.055])
chi_max, k, chi0 = params
print("Saturation fit:", chi_max, k, chi0)

# Fit hysteresis (simple regression)
df['chi_next'] = df['chi_amplitude'].shift(-1)
valid = df.dropna()

from sklearn.linear_model import LinearRegression
X = np.column_stack([valid['chi_amplitude'], P_dyn.loc[valid.index]])
y = valid['chi_next']

model = LinearRegression().fit(X, y)
alpha = model.coef_[0]
k_lin = model.coef_[1]
print("Hysteresis fit: alpha =", alpha, "k =", k_lin)

# Fit magnetic gain term
X_mag = P_dyn * (1 + (-df['bz_nT'])/(1+np.abs(df['bz_nT'])))
model_mag = LinearRegression().fit(X_mag.values.reshape(-1,1), chi)
beta = model_mag.coef_[0]
print("Magnetic gain fit: beta =", beta)
