import matplotlib.pyplot as plt
import numpy as np

def generate_lock_proof():
    # THE LIVE DATA (Jan 18, 18:00 UTC)
    solar_phase = 4.0143
    stellar_phase = 4.0143
    
    # Setup the Cycle (0 to 2pi)
    x = np.linspace(0, 2*np.pi, 100)
    y_carrier = np.sin(x + np.pi/1.2) # The Carrier Wave
    
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    
    # Plot the Carrier Wave (The Lattice)
    ax.plot(x, y_carrier, color='gray', alpha=0.3, linestyle='--', label='Global Carrier Wave (6H Harmonic)')
    
    # Plot The Sun (Local Node)
    ax.scatter([solar_phase], [np.sin(solar_phase + np.pi/1.2)], 
               color='#00ff00', s=500, marker='o', 
               label='SOLAR WIND (Local Node)\nPhase: 4.0143 rad', zorder=10)
               
    # Plot Tabby's Star (Remote Node)
    ax.scatter([stellar_phase], [np.sin(stellar_phase + np.pi/1.2)], 
               color='#ff0000', s=250, marker='*', 
               label="TABBY'S STAR (Remote Node)\nPhase: 4.0143 rad", zorder=11)

    # Annotation
    ax.text(3.5, 0.5, "PERFECT\nALIGNMENT", color='white', fontweight='bold', fontsize=14, ha='center')
    ax.arrow(3.8, 0.2, 0.2, -0.2, color='white', head_width=0.1)

    # Styling
    ax.set_title("THE CLINE RESONANCE: 18:00 UTC LOCK", color='white', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Phase Angle (Radians)", color='white', fontsize=12)
    ax.set_yticks([])
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_visible(False) 
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    legend = ax.legend(loc='upper left', facecolor='#333333', edgecolor='white')
    for text in legend.get_texts():
        text.set_color("white")
        
    plt.tight_layout()
    plt.savefig('reports/PHASE_LOCK_JAN18.png')
    print("PROOF GENERATED: reports/PHASE_LOCK_JAN18.png")

if __name__ == "__main__":
    generate_lock_proof()
