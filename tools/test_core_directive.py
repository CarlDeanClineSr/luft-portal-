import pandas as pd
import numpy as np
from pathlib import Path
import os

log_path = Path("data/cme_heartbeat_log_2025_12.csv")
df = pd.read_csv(log_path, parse_dates=['timestamp_utc'], on_bad_lines='skip').set_index('timestamp_utc')

# Convert chi_amplitude to numeric, coercing errors to NaN
df['chi_amplitude'] = pd.to_numeric(df['chi_amplitude'], errors='coerce')

# Drop rows with NaT index or NaN chi_amplitude
df = df[df.index.notna() & df['chi_amplitude'].notna()]

# Extract rebound events (dip >0.005 below cap, recovery within 2 hours)
cap = 0.15
df['dip'] = (cap - df['chi_amplitude']) > 0.005
rebound_events = df[df['dip'] == True].index

# For each, compute R = Δχ / Δt
results = []
for start in rebound_events:
    recovery = df.loc[start:].query('chi_amplitude > @cap - 0.001')
    if len(recovery.index) == 0:
        continue
    end = recovery.index[0]
    if pd.isna(end):
        continue
    delta_chi = df.at[end, 'chi_amplitude'] - df.at[start, 'chi_amplitude']
    delta_t = (end - start).total_seconds() / 3600  # hours
    if delta_t == 0:
        continue
    R = delta_chi / delta_t
    beta = df.at[end, 'beta'] if 'beta' in df else np.nan
    mach = df.at[end, 'Mach'] if 'Mach' in df else np.nan
    results.append({'start': start, 'end': end, 'R': R, 'beta': beta, 'mach': mach})

df_results = pd.DataFrame(results)

# Ensure results directory exists
os.makedirs("results", exist_ok=True)

# Fit log R = a0 + a1 log beta + a2 log mach (directive H2)
from scipy.stats import linregress
mask = ~df_results[['beta', 'mach']].isna().any(axis=1)
if mask.sum() > 5:
    log_r = np.log(df_results.loc[mask, 'R'])
    log_beta = np.log(df_results.loc[mask, 'beta'])
    log_mach = np.log(df_results.loc[mask, 'mach'])
    # Simple fit (extend for full H2)
    slope_beta, intercept, r_value, _, _ = linregress(log_beta, log_r)
    print(f"Fitted: log R = {slope_beta:.3f} log β + {intercept:.3f} (r² = {r_value**2:.3f})")

df_results.to_csv("results/rebound_test_v1.csv", index=False)
print("Test complete: results/rebound_test_v1.csv")
