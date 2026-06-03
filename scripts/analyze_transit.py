import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import yaml

with open("config/constants.yaml", "r") as f:
    cfg = yaml.safe_load(f)

with fits.open("data/science_segment.fits", memmap=cfg['processing']['memmap']) as hdul:
    # Sum all pixels to get total flux
    total_flux = np.nansum(hdul['SCI'].data, axis=(1, 2, 3))

norm_flux = total_flux / np.nanmedian(total_flux)
# Detrending via polynomial fit
t = np.arange(len(norm_flux))
coeffs = np.polyfit(t, norm_flux, 2)
flattened = norm_flux / np.polyval(coeffs, t)

# Plotting
plt.figure(figsize=(10, 5))
plt.plot(flattened, color='cyan', alpha=0.5)
plt.title(f"Automated Transit Signal: {cfg['processing']['target']}")
plt.savefig("output/transit_signal.png")
print("Analysis complete: Transit signal plot generated.")
