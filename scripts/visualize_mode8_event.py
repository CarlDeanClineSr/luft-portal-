import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import io

# ------------------------------------------------------------------
# CONFIGURATION: THE IMPERIAL CONSTANTS
# ------------------------------------------------------------------
CHI_LIMIT = 0.1500
HARMONIC_1 = 0.3000  # Mode 2
HARMONIC_2 = 0.4500  # Mode 3
CRITICAL_CHI = 0.822 # The Mode 8 Peak

# ------------------------------------------------------------------
# 1. LOAD THE FLIGHT RECORDER DATA
# ------------------------------------------------------------------
data_stream = """
timestamp,chi,mode
2026-01-22 23:03,0.138,1
2026-01-23 02:39,0.283,2
2026-01-23 09:06,0.822,8
2026-01-23 20:04,0.193,1
2026-01-24 05:04,0.548,4
2026-01-24 14:03,0.393,2
2026-01-25 05:09,0.433,4
2026-01-25 23:52,0.110,1
"""

# Convert to DataFrame
df = pd.read_csv(io.StringIO(data_stream))
df['timestamp'] = pd.to_datetime(df['timestamp'])

# ------------------------------------------------------------------
# 2. CONSTRUCT THE LATTICE VISUALIZATION
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 7), facecolor='#0f0f0f')
ax.set_facecolor('#0f0f0f')

# Plot the Data Stream (The "Heartbeat")
ax.plot(df['timestamp'], df['chi'], color='#00ff41', linewidth=2, marker='o', 
        markersize=6, label='Vacuum Tension ($\chi$)')

# ------------------------------------------------------------------
# 3. DRAW THE IMPERIAL BOUNDARIES
# ------------------------------------------------------------------
# The Vacuum Limit (Mode 1 Ceiling)
ax.axhline(y=CHI_LIMIT, color='#00ffff', linestyle='--', linewidth=1.5, alpha=0.8)
ax.text(df['timestamp'].iloc[0], CHI_LIMIT + 0.02, '  TARGET VACUUM STATE ($\chi \leq 0.15$)', 
        color='#00ffff', fontsize=10, fontweight='bold')

# The Harmonic Ladder (Mode 2 & Mode 3)
ax.axhline(y=HARMONIC_1, color='#ffcc00', linestyle=':', linewidth=1, alpha=0.6)
ax.text(df['timestamp'].iloc[0], HARMONIC_1 + 0.02, '  HARMONIC MODE 2 (0.30)', 
        color='#ffcc00', fontsize=8)

ax.axhline(y=HARMONIC_2, color='#ff6600', linestyle=':', linewidth=1, alpha=0.6)

# The Critical Failure Line (Mode 8 Peak)
ax.axhline(y=CRITICAL_CHI, color='#ff0033', linestyle='-', linewidth=2, alpha=0.5)
ax.text(df['timestamp'].iloc[0], CRITICAL_CHI + 0.02, '  CRITICAL FAILURE (MODE 8 EVENT)', 
        color='#ff0033', fontsize=10, fontweight='bold')

# ------------------------------------------------------------------
# 4. FORMATTING & IMPERIAL AESTHETICS
# ------------------------------------------------------------------
ax.grid(True, which='both', color='#333333', linestyle='-', linewidth=0.5)
ax.set_title(f"LUFT ENGINE STATUS: POST-INCIDENT RECOVERY\nBinary Temporal Scaling Verification", 
             color='white', fontsize=14, pad=20)
ax.set_ylabel("Vacuum Modulation ($\chi$)", color='#cccccc', fontsize=12)
ax.set_xlabel("Time (UTC)", color='#cccccc', fontsize=12)

# Date Formatting
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
plt.xticks(rotation=45, color='#cccccc')
plt.yticks(color='#cccccc')

# Spines (The Frame)
for spine in ax.spines.values():
    spine.set_edgecolor('#555555')

plt.tight_layout()

# ------------------------------------------------------------------
# 5. EXECUTE VISUAL PROTOCOL (THE FIX)
# ------------------------------------------------------------------
print("Generatng Visual Affidavit...")

# CHANGED FROM plt.show() TO plt.savefig()
plt.savefig('mode8_event.png')

print("Process Complete. Visual Affidavit saved as 'mode8_event.png'.")
