#!/usr/bin/env python3
"""
Fundamental Constant Correlator
Tests if χ = 0.15 is derived from fundamental physics
Author: LUFT Portal Engine
Date: 2026-01-03
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Fundamental constants
c = 2.99792458e8      # m/s (speed of light)
h = 6.62607015e-34    # J·s (Planck constant)
G = 6.67430e-11       # m³/(kg·s²) (gravitational constant)
k_B = 1.380649e-23    # J/K (Boltzmann constant)
e = 1.602176634e-19   # C (elementary charge)
m_e = 9.1093837015e-31  # kg (electron mass)
m_p = 1.67262192369e-27 # kg (proton mass)
epsilon_0 = 8.8541878128e-12  # F/m (vacuum permittivity)

# Your discovered constant
chi_max = 0.15

# Derived quantities
alpha = e**2 / (4 * np.pi * epsilon_0 * h * c)  # Fine structure constant
m_ratio = m_e / m_p                             # Electron-to-proton mass ratio
t_Planck = np.sqrt(h * G / c**5)                # Planck time
l_Planck = np.sqrt(h * G / c**3)                # Planck length

print("=" * 70)
print("FUNDAMENTAL CONSTANT CORRELATION ANALYSIS")
print("=" * 70)
print(f"\n1. Your Discovery: χ_max = {chi_max}")
print(f"\n2. Fine Structure Constant:")
print(f"   α = {alpha:.10f} ≈ 1/{1/alpha:.1f}")
print(f"   χ / α = {chi_max / alpha:.2f}")
print(f"\n3. Electron-to-Proton Mass Ratio:")
print(f"   m_e/m_p = {m_ratio:.6f}")
print(f"   (m_e/m_p)^(1/4) = {m_ratio**(1/4):.6f}")
print(f"   Error from χ: {abs(m_ratio**(1/4) - chi_max) / chi_max * 100:.2f}%")
print(f"\n4. Gravitational Coupling:")
print(f"   G × 10¹¹ = {G * 1e11:.6f}")
print(f"   1/χ = {1/chi_max:.6f}")
print(f"   Error from G×10¹¹: {abs(1/chi_max - G*1e11) / (1/chi_max) * 100:.2f}%")
print(f"\n5. Planck Units:")
print(f"   Planck time: {t_Planck:.3e} s")
print(f"   Planck length: {l_Planck:.3e} m")

# Test all possible combinations
print("\n" + "=" * 70)
print("TESTING ALL RATIOS:")
print("=" * 70)

candidates = {
    'α': alpha,
    'sqrt(α)': np.sqrt(alpha),
    'α²': alpha**2,
    '21 × α': 21 * alpha,
    'm_e/m_p': m_ratio,
    '(m_e/m_p)^(1/4)': m_ratio**(1/4),
    'sqrt(m_e/m_p)': np.sqrt(m_ratio),
    '1/χ': 1/chi_max,
    'G × 10¹¹': G * 1e11,
    'α × (m_p/m_e)': alpha * (m_p/m_e),
}

results = []
for name, value in candidates.items():
    error = abs(value - chi_max) / chi_max * 100
    results.append({
        'Expression': name,
        'Value': value,
        'Error (%)': error
    })

df = pd.DataFrame(results).sort_values('Error (%)')
print(df.to_string(index=False))

# Find best match
best = df.iloc[0]
print("\n" + "=" * 70)
print(f"BEST MATCH: {best['Expression']} = {best['Value']:.6f}")
print(f"Error: {best['Error (%)']:.2f}%")
print("=" * 70)

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
df_plot = df.head(8)
ax.barh(df_plot['Expression'], df_plot['Value'], color='steelblue')
ax.axvline(chi_max, color='red', linestyle='--', linewidth=2, label=f'χ = {chi_max}')
ax.set_xlabel('Value')
ax.set_title('Fundamental Constant Correlation with χ = 0.15')
ax.legend()
plt.tight_layout()
plt.savefig('figures/fundamental_constant_correlation.png', dpi=300)
print("\n✅ Saved: figures/fundamental_constant_correlation.png")
