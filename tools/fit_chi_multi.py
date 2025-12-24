import pandas as pd
from pathlib import Path
from scipy.stats import linregress

LOG = Path("data/cme_heartbeat_log_2025_12.csv")
df = pd.read_csv(LOG)

# Normalize χ (0-1)
df['chi_norm'] = (df['chi_amplitude'] - df['chi_amplitude'].min()) / (df['chi_amplitude'].max() - df['chi_amplitude'].min())

# Drivers (example)
drivers = ['density', 'speed', 'P_dyn', 'beta', 'Mach', 'Bz', 'Kp']

results = {}
for driver in drivers:
    if driver in df.columns:
        slope, intercept, r, p, se = linregress(df[driver], df['chi_norm'])
        results[driver] = {'slope': slope, 'intercept': intercept, 'r2': r**2}

print("χ Multi-Driver Fits:")
for d, v in results.items():
    print(f"{d}: χ = {v['slope']:.4f} * {d} + {v['intercept']:.4f} (r² = {v['r2']:.3f})")
