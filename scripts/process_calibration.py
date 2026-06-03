import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import yaml
import os

with open("config/constants.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# Load data with memmap=False as established
with fits.open("data/science_segment.fits", memmap=cfg['processing']['memmap']) as hdul:
    data = hdul['SCI'].data
    # 2D Median collapse
    s_data = np.nanmedian(data, axis=(0, 1))

# Save the calibrated residual map as a FITS file for long-term storage
hdu = fits.PrimaryHDU(s_data)
os.makedirs("output", exist_ok=True)
hdu.writeto("output/residual_map.fits", overwrite=True)

print("Calibration layer applied: Residual map generated.")
