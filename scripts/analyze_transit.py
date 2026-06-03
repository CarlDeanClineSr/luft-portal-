import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

ROOT_DIR = os.getcwd()
DATA_PATH = os.path.join(ROOT_DIR, "data", "science_segment.fits")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Pipeline failure: File not found at {DATA_PATH}")

with fits.open(DATA_PATH, memmap=False) as hdul:
    total_flux = np.nansum(hdul['SCI'].data, axis=(1, 2, 3))

norm_flux = total_flux / np.nanmedian(total_flux)
t = np.arange(len(norm_flux))
coeffs = np.polyfit(t, norm_flux, 2)
flattened = norm_flux / np.polyval(coeffs, t)

plt.figure(figsize=(10, 5))
plt.plot(flattened, color='cyan', alpha=0.5)
plt.title("Automated Transit Signal")
plt.savefig(os.path.join(OUTPUT_DIR, "transit_signal.png"))

print("Transit analysis complete.")
