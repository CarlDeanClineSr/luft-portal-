This folder contains example chart SVGs generated on branch data-normalize.

Files: 
- chart_example_chi.svg: Example χ amplitude plot (placeholder image).
- chart_cycle_1.svg: Example cycle chart frame (placeholder image).

These are placeholders generated to preview the output of scripts/make_example_chart.py and scripts/save_cycle_charts.py. To regenerate real charts from data, run: 

python3 scripts/compute_pdyn_chi.py
python3 scripts/make_example_chart.py
python3 scripts/save_cycle_charts.py --cycle 1

If you want a true PNG or GIF, run the scripts in an environment with matplotlib and imageio installed; then copy the generated charts into this folder and commit them.