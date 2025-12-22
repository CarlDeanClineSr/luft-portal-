#!/usr/bin/env python3
"""
dashboard_builder.py — Unified χ Dashboard Generator

Outputs:
  reports/dashboard_summary.md
  reports/plots/dashboard_overview.png
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")
PLOTS_DIR = REPORTS_DIR / "plots"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

CHI_COL = "chi_amplitude_extended"
TIME_COL = "datetime"


def load_latest
