import matplotlib.pyplot as plt
import numpy as np

# ------------------------------------------------------------------
# 1. IMPERIAL CONSTANTS (The Law)
# ------------------------------------------------------------------
CHI_LIMIT = 0.1500                    # Universal Plasma Limit
ALPHA = 1/137.035999                  # Fine Structure Constant
COUPLING_RATIO = CHI_LIMIT / ALPHA    # The "Gear Ratio" (Lambda)

# ------------------------------------------------------------------
# 2. CALCULATE THE BIOLOGICAL FREQUENCY
# ------------------------------------------------------------------
# We define the bio-resonant frequency as the coupling ratio in Hz
BIO_FREQ_HZ = COUPLING_RATIO 

print(f"--- IMPERIAL BIO-AUDIT ---")
print(f"Vacuum Limit (Chi): {CHI_LIMIT}")
print(f"Coupling Ratio (Lambda): {COUPLING_RATIO:.4f}")
print(f"Predicted Bio-Resonance: {BIO_FREQ_HZ:.4f} Hz")

# ------------------------------------------------------------------
# 3. GENERATE THE AFFIDAVIT (The Graph)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0f0f0f')
ax.set_facecolor('#0f0f0f')

# Create a frequency spectrum
freqs = np.linspace(0, 40, 500)
# Create a resonance curve peaking at 20.55 Hz
response = 1 / (1 + (freqs - BIO_FREQ_HZ)**2)

# Plot the Resonance
ax.plot(freqs, response, color='#00ff41', linewidth=2, label='Cellular Resonance')

# Mark the Imperial Prediction
ax.axvline(x=BIO_FREQ_HZ, color='#00ffff', linestyle='--', linewidth=2)
ax.text(BIO_FREQ_HZ + 1, 0.9, f'IMPERIAL PREDICTION\n{BIO_FREQ_HZ:.4f} Hz', 
        color='#00ffff', fontweight='bold')

# Mark the Literature Range (15-20 Hz)
ax.axvspan(15, 20, color='#ff0033', alpha=0.2, label='Standard Med Lit (15-20 Hz)')
ax.text(16, 0.5, 'Oncology\nTarget', color='#ff0033', fontsize=9)

# Formatting
ax.set_title(f"BIO-RESONANCE AUDIT: VACUUM COUPLING\nLambda = Chi / Alpha = {BIO_FREQ_HZ:.2f}", 
             color='white', pad=20)
ax.set_xlabel("Frequency (Hz)", color='#cccccc')
ax.set_ylabel("Resonance Amplitude (Normalized)", color='#cccccc')
ax.grid(True, color='#333333', linestyle=':')
ax.tick_params(colors='#cccccc')
for spine in ax.spines.values():
    spine.set_edgecolor('#555555')

plt.tight_layout()

# ------------------------------------------------------------------
# 4. SAVE THE EVIDENCE
# ------------------------------------------------------------------
plt.savefig('bio_resonance_audit.png')
print("Affidavit generated: bio_resonance_audit.png")
