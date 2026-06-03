import os
import numpy as np
from astropy.io import fits

ROOT_DIR = os.getcwd()
DATA_PATH = os.path.join(ROOT_DIR, "data", "science_segment.fits")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Pipeline failure: File not found at {DATA_PATH}")

with fits.open(DATA_PATH, memmap=False) as hdul:
    data = hdul['SCI'].data
    # 2D Median collapse (Integrations, Groups, Y, X) -> (Y, X)
    s_data = np.nanmedian(data, axis=(0, 1))

hdu = fits.PrimaryHDU(s_data)
hdu.writeto(os.path.join(OUTPUT_DIR, "residual_map.fits"), overwrite=True)

print(f"Calibration complete. Residual map written to {OUTPUT_DIR}")
