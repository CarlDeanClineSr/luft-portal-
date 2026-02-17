import numpy as np
import matplotlib.pyplot as plt

# Simulated GW strain (replace with real LIGO/Virgo data as needed)
t = np.linspace(0, 0.5, 10000)  # seconds
gw_strain = 1e-21 * np.sin(80 * 2 * np.pi * t) * np.exp(-6 * t)  # ringdown

# LUFT overlay modulation
Omega = 1e-4  # Hz, LUFT heartbeat
chi = 0.055   # modulation depth
phi0 = 0      # phase offset
luft_mod = (1 + chi * np.cos(2 * np.pi * Omega * t + phi0))
modulated_gw = gw_strain * luft_mod

# Plot overlay
plt.plot(t, gw_strain, label='Standard GW Strain (Einstein)')
plt.plot(t, modulated_gw, label='LUFT Overlay')
plt.xlabel("Time (s)")
plt.ylabel("Strain")
plt.title("LUFT Modulation on Gravitational Wave Signal")
plt.legend()
plt.show()
