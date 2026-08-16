import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def process_goes_telemetry(raw_json_data):
    """
    Parses GOES-18 X-ray flux telemetry, computes the perturbation index chi(t),
    and filters for boundary lock events.
    """
    df = pd.DataFrame(raw_json_data)
    
    # Isolate long-wave channel (0.1-0.8nm)
    df_long = df[df['energy'] == '0.1-0.8nm'].copy()
    df_long['time_tag'] = pd.to_datetime(df_long['time_tag'])
    df_long = df_long.sort_values('time_tag').reset_index(drop=True)
    
    # Establish quiet-sun baseline from earliest entries
    baseline = df_long['flux'].iloc[:10].mean()
    
    # Calculate normalized perturbation chi
    df_long['chi'] = np.abs(df_long['flux'] - baseline) / baseline
    
    # Identify boundary crossings and attractor states
    chi_cap = 0.15
    df_long['near_boundary'] = np.abs(df_long['chi'] - chi_cap) <= 0.02
    
    return df_long, baseline

# Example usage with telemetry dataframe:
# df_processed, base_val = process_goes_telemetry(goes_json_data)

# Print summary metrics
print(f"GOES-18 Telemetry Analysis:")
print(f"- Established Baseline Flux: {base_val:.4e} W/m^2")
print(f"- Max Flare Perturbation: {df_processed['chi'].max():.2f}")
print(f"- Post-Impulse Attractor Events (chi ~ 0.15): {df_processed['near_boundary'].sum()}")
