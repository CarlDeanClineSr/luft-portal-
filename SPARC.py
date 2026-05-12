import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse_sparc_file(filepath):
    """
    Bypasses the SPARC header bug by dynamically ignoring all commented lines
    and handling irregular whitespace delimiters.
    """
    # SPARC standard columns: Rad, Vobs, errV, Vgas, Vdisk, Vbulge, SBdisk, SBbulge
    columns = ['Rad', 'Vobs', 'errV', 'Vgas', 'Vdisk', 'Vbulge', 'SBdisk', 'SBbulge']
    
    try:
        # engine ignores lines starting with '#' and treats multi-spaces as delimiters
        df = pd.read_csv(filepath, sep=r'\s+', comment='#', names=columns, engine='python')
        return df
    except Exception as e:
        print(f"[!] Engine failure on {filepath}: {e}")
        return None

def calculate_chi_histogram(data_dir):
    """
    Calculates the normalized lattice tension (χ) across all galactic rotation curves.
    """
    chi_values = []
    
    # Iterate through all SPARC .dat files in the directory
    for filename in os.listdir(data_dir):
        if not filename.endswith('.dat'):
            continue
            
        filepath = os.path.join(data_dir, filename)
        df = parse_sparc_file(filepath)
        
        if df is not None and not df.empty:
            # V_bar is the expected velocity from visible baryonic mass (gas + disk + bulge)
            # The squares of the velocities add linearly for gravitational potential
            V_bar_sq = df['Vgas']**2 + df['Vdisk']**2 + df['Vbulge']**2
            V_obs_sq = df['Vobs']**2
            
            # Prevent division by zero at the galactic core
            valid_mask = (V_obs_sq > 0) & (V_bar_sq > 0)
            
            # In the Imperial Framework, the discrepancy is the lattice tension (χ)
            # representing the substrate pressure (P_l) holding the outer rim.
            # chi = (V_obs^2 - V_bar_sq) / V_obs^2 
            chi_local = (V_obs_sq[valid_mask] - V_bar_sq[valid_mask]) / V_obs_sq[valid_mask]
            
            # Drop negative values (where baryonic mass alone accounts for rotation)
            chi_local = chi_local[chi_local > 0]
            chi_values.extend(chi_local.tolist())
            
    # Generate the Histogram
    plt.figure(figsize=(10, 6))
    plt.hist(chi_values, bins=100, color='darkred', edgecolor='black', alpha=0.8)
    plt.axvline(x=0.15, color='cyan', linestyle='dashed', linewidth=2, label='χ = 0.15 Yield Limit')
    
    plt.title('SPARC Galactic Rotation Curves: Normalized Substrate Tension (χ)', fontsize=14)
    plt.xlabel('Tension Metric (χ)', fontsize=12)
    plt.ylabel('Observation Count', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save the output for the LUFT portal
    plt.savefig('SPARC_Chi_Histogram.png')
    print(f"[⚙️] Processed {len(chi_values)} valid data points. Histogram generated.")

# Example Execution in Colab:
# calculate_chi_histogram('/content/SPARC_data_folder')
