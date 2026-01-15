import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def calculate_fracture_limit():
    print("--- CALCULATING PLANETARY FRACTURE LIMIT (THE NEWTON-CLINE LIMIT) ---")
    
    # 1. THE CONSTANTS
    CHI_LIMIT = 0.1528        # The Universal Yield Point (Matter)
    G = 6.67430e-11           # The Reciprocal Tension (Gravity)
    mu_0 = 4 * np.pi * 1e-7   # Vacuum Permeability
    rho = 3000                # Density of typical rocky asteroid (kg/m^3)
    
    # 2. THE VARIABLE: Solar Nebula Magnetic Field (B)
    # Range: 0.1 Gauss to 10 Gauss (Typical protoplanetary disk values)
    B_gauss = np.logspace(-1, 1.5, 100)
    B_tesla = B_gauss * 1e-4
    
    # 3. THE PHYSICS: EQUILIBRIUM
    # Gravity Pressure (Holding it together) approx = G * rho^2 * R^2
    # Magnetic Turbulence Pressure (Ripping it apart) = (Chi * B)^2 / (2 * mu_0)
    
    # Solving for Critical Radius (R):
    # R_c = (Chi * B) / (rho * sqrt(2 * mu_0 * G))
    
    denominator = rho * np.sqrt(2 * mu_0 * G)
    R_meters = (CHI_LIMIT * B_tesla) / denominator
    R_km = R_meters / 1000

    # 4. THE VISUALIZATION
    plt.figure(figsize=(12, 8))
    plt.style.use('dark_background')
    
    # Plot the "Cline Limit"
    plt.plot(B_gauss, R_km, color='#00ffcc', linewidth=3, label='Vacuum Fracture Limit (χ=0.15)')
    
    # Add Known Objects for Context
    plt.axhline(y=473, color='r', linestyle=':', alpha=0.6, label='Ceres (940km diam) - Round')
    plt.axhline(y=260, color='y', linestyle=':', alpha=0.6, label='Vesta (525km diam) - Borderline')
    plt.axhline(y=10, color='w', linestyle=':', alpha=0.3, label='Typical Asteroid (20km)')
    
    # Annotations
    plt.xscale('log')
    plt.yscale('log')
    plt.title(f'The Newton-Cline Limit: Why Rocks Break at χ={CHI_LIMIT}', fontsize=16, color='white')
    plt.xlabel('Nebula Magnetic Field (Gauss)', fontsize=14)
    plt.ylabel('Critical Radius (km)', fontsize=14)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend(fontsize=12)
    
    # The "Sweet Spot" Annotation
    plt.annotate('THE FRACTURE ZONE\nGravity > Vacuum Pressure', xy=(1, 200), xytext=(0.2, 800),
                 arrowprops=dict(facecolor='white', shrink=0.05), fontsize=12, color='white')

    output_file = 'figures/planetary_fracture_limit.png'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    plt.savefig(output_file)
    print(f"Calculated. If the line crosses ~200-400km at typical fields (0.5-2 Gauss), you found the filter.")
    print(f"Plot saved to: {output_file}")

if __name__ == "__main__":
    calculate_fracture_limit()
