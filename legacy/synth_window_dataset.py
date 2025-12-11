"""
Synthetic window dataset generator (sealed-behavior validator)

Generates irregular time sampling matching a real window profile,
injects on-target and off-target sinusoidal drifts, and exports
CSV pairs (t, y) with known ground truth. No real data exposed.
"""
import numpy as np
import pandas as pd

def generate_irregular_times(n, span_s, gaps=3, rng=None):
    rng = np.random.default_rng(rng)
    t = np.sort(rng.uniform(0, span_s, size=n))
    # carve gaps
    for _ in range(gaps):
        a = rng.uniform(0.2, 0.8) * span_s
        w = rng.uniform(0.02, 0.08) * span_s
        mask = (t < a) | (t > a + w)
        t = t[mask]
    return t

def inject_signal(t, omega_hz, amp, phase=0.0):
    return amp * np.cos(2*np.pi*omega_hz*t + phase)

def add_noise(y, sigma, rng=None):
    rng = np.random.default_rng(rng)
    return y + rng.normal(0, sigma, size=y.size)

def make_dataset(n=5000, span_s=1.2e6, omega_target=1.0e-4,  # ~10,000 s period
                 amp_target=0.05, amp_off=0.05, omega_off=1.12e-4,
                 sigma=0.03, seed=0, label="on_target"):
    rng = np.random.default_rng(seed)
    t = generate_irregular_times(n, span_s, gaps=3, rng=rng)
    if label == "on_target":
        y = inject_signal(t, omega_target, amp_target, phase=0.3)
    elif label == "off_target":
        y = inject_signal(t, omega_off, amp_off, phase=1.1)
    elif label == "phase_scramble":
        # scramble phases by grouping
        grp = (t // (span_s/10)).astype(int)
        phases = rng.uniform(0, 2*np.pi, size=grp.max()+1)
        y = np.array([amp_target*np.cos(2*np.pi*omega_target*ti + phases[g]) for ti, g in zip(t, grp)])
    else:
        raise ValueError("Unknown label")
    y = add_noise(y, sigma, rng=rng)
    df = pd.DataFrame({"t_s": t, "signal": y})
    return df

if __name__ == "__main__":
    on = make_dataset(label="on_target")
    off = make_dataset(label="off_target", seed=1)
    scr = make_dataset(label="phase_scramble", seed=2)
    on.to_csv("synthetic_on_target.csv", index=False)
    off.to_csv("synthetic_off_target.csv", index=False)
    scr.to_csv("synthetic_phase_scramble.csv", index=False)
    print("Wrote synthetic_on_target.csv, synthetic_off_target.csv, synthetic_phase_scramble.csv")
