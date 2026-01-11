from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "results" / "historical_chi" / "historical_chi_1975_1985.csv"
OUTPUT_DIR = BASE_DIR / "historical_validation"
OUTPUT_DIR.mkdir(exist_ok=True)
TOP_CANDIDATES = 100
# Treat baselines below this nT threshold as invalid to avoid dividing by (near) zero.
BASELINE_EPSILON = 1e-6


def load_data() -> pd.DataFrame:
    """Load historical chi data, computing chi if needed."""
    print(f"--- HISTORICAL RECOVERY VERIFICATION (1975-1985) ---")
    print(f"Loading {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

    if "chi" not in df.columns:
        if {"B_total_nT", "B_baseline_nT"}.issubset(df.columns):
            print("Computing chi from B_total_nT and B_baseline_nT...")
            baseline = df["B_baseline_nT"].mask(
                (df["B_baseline_nT"] == 0) | (df["B_baseline_nT"].abs() < BASELINE_EPSILON),
                np.nan,
            )
            valid = baseline.notna()
            df = df.loc[valid].copy()
            df["B_baseline_nT"] = baseline[valid]
            df["chi"] = np.abs(df["B_total_nT"] - df["B_baseline_nT"]) / df["B_baseline_nT"]
        else:
            raise ValueError("Expected chi or B_total_nT/B_baseline_nT columns in dataset.")

    df = df.dropna(subset=["timestamp", "chi"]).sort_values("timestamp")
    return df


def find_top_events(df: pd.DataFrame, limit: int = 3, min_separation_hours: int = 48) -> list[pd.Series]:
    """Return top chi events separated by at least min_separation_hours."""
    top_violations = df.nlargest(TOP_CANDIDATES, "chi")
    unique_events: list[pd.Series] = []
    threshold = pd.Timedelta(hours=min_separation_hours)

    for _, row in top_violations.iterrows():
        t = row["timestamp"]
        if any(abs(e["timestamp"] - t) < threshold for e in unique_events):
            continue
        unique_events.append(row)
        if len(unique_events) >= limit:
            break

    print(f"Top Events Found: {[e['timestamp'] for e in unique_events]}")
    return unique_events


def plot_recovery(df: pd.DataFrame, events: list[pd.Series]) -> None:
    sns.set_theme(style="whitegrid")

    for i, event in enumerate(events):
        event_time = event["timestamp"]
        start_plot = event_time - pd.Timedelta(hours=12)
        end_plot = event_time + pd.Timedelta(hours=48)

        mask = (df["timestamp"] >= start_plot) & (df["timestamp"] <= end_plot)
        storm_data = df.loc[mask]

        plt.figure(figsize=(12, 6))
        plt.plot(storm_data["timestamp"], storm_data["chi"], color="#333333", linewidth=1.5, label=r"Historical $\chi$")
        plt.axhline(y=0.1528, color="#d9534f", linestyle="--", linewidth=2, label=r"Limit $(m_e/m_p)^{1/4}$")

        date_str = event_time.strftime("%Y-%m-%d")
        plt.title(f"Historical Validation: Storm Recovery {date_str} (Max chi={event['chi']:.2f})")
        plt.ylabel(r"$\chi$")
        plt.xlabel("Time")
        plt.legend()
        plt.tight_layout()

        fname = OUTPUT_DIR / f"storm_recovery_{i + 1}_{date_str}.png"
        plt.savefig(fname)
        plt.close()
        print(f"Saved plot: {fname}")


def main() -> None:
    df = load_data()
    events = find_top_events(df)
    plot_recovery(df, events)
    print("\n--- VERIFICATION COMPLETE ---")
    print("Check 'historical_validation'. If the curve drops and stays near the red line (e.g., last 12h median <= 0.1528), it supports the theoretical prediction.")


if __name__ == "__main__":
    main()
