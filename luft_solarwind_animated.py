import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.animation import FuncAnimation

# Mock example: Replace data with real NOAA/ledger feed
data = [
    ["2025-11-27 19:01:00.000", -4.86, 1.02, -3.35, 168.15, -33.98, 5.99],
    ["2025-11-27 19:02:00.000", 1.13, 649.1, 28813, None, None, None],
    # add more rows for a longer animation...
]
df = pd.DataFrame(data, columns=["Time", "Bz", "Density", "Speed", "Temp", "Bx", "By"])

fig, ax1 = plt.subplots()
line_speed, = ax1.plot([], [], label="Speed", color='b')
line_density, = ax1.plot([], [], label="Density", color='g')
ax1.set_xlim(df["Time"][0], df["Time"].iloc[-1])
ax1.set_ylim(0, max(df["Speed"].max(), df["Density"].max()) * 1.1)
ax1.legend(); ax1.set_title("Animated Solar Wind Audit")

def animate(i):
    line_speed.set_data(df["Time"][:i+1], df["Speed"][:i+1])
    line_density.set_data(df["Time"][:i+1], df["Density"][:i+1])
    return line_speed, line_density

ani = FuncAnimation(fig, animate, frames=len(df), interval=1000, blit=True)
plt.tight_layout()
plt.show()

# To save the animation as GIF or MP4:
# ani.save('solarwind_audit.gif', writer='imagemagick')
# ani.save('solarwind_audit.mp4', writer='ffmpeg')
