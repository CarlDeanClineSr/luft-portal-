"""
Flare/Flux → LUFT state pipeline
- Ingests GOES proton flux JSON (1-day) or a CSV (timestamp, Phi_pfu)
- Computes f(t), f_h(t), Gamma amplification, v_d gain, epsilon_coh estimate
- Flags storm phases and optionally calls PLW (positron_lattice_writer) to estimate impulse retention

Usage examples:
  # From a local CSV
  python3 flare_pipeline.py --input flux.csv --output sft_states.csv

  # Pull live GOES JSON (1-day integral protons)
  python3 flare_pipeline.py --from-goes --output sft_states.csv

  # Include positron impulse (if positron_lattice_writer.py is in path)
  python3 flare_pipeline.py --input flux.csv --with-plw --plw-E_dep 1e-15 --plw-V_cell 1e-6 --output sft_states.csv
"""
import argparse, csv, math, json, sys, datetime, urllib.request
from typing import List, Tuple

def parse_time(ts: str) -> datetime.datetime | None:
    # Accept ISO8601 or epoch seconds
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.datetime.utcfromtimestamp(float(ts))
        except Exception:
            return None

def load_csv(path: str) -> List[Tuple[datetime.datetime, float]]:
    series = []
    with open(path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = parse_time(r["timestamp"])
            if t is None:
                continue
            phi = float(r["Phi_pfu"])
            series.append((t, phi))
    series.sort(key=lambda x: x[0])
    return series

def fetch_goes_1day_json() -> List[Tuple[datetime.datetime, float]]:
    # NOAA SWPC example feed: integral protons (primary) — may change over time
    url = "https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    series: List[Tuple[datetime.datetime, float]] = []
    # Try common keys; if schema changes, adapt mapping
    # Typical keys seen: "time_tag", "energy", "flux"
    for row in data:
        ts = row.get("time_tag") or row.get("time") or row.get("timestamp")
        phi = row.get("flux") or row.get("proton_flux") or row.get("value")
        if ts is None or phi is None:
            continue
        t = parse_time(ts)
        try:
            flux = float(phi)
        except Exception:
            continue
        if t:
            series.append((t, flux))
    series.sort(key=lambda x: x[0])
    return series

def alpha_modulated(alpha0: float, delta: float, omega: float, phi0: float, t0: float, t: float) -> float:
    # alpha(t) = alpha0 + delta sin(2π ω (t - t0) + φ0)
    return alpha0 + delta * math.sin(2 * math.pi * omega * (t - t0) + phi0)

def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="CSV with columns: timestamp, Phi_pfu")
    src.add_argument("--from-goes", action="store_true", help="Fetch GOES integral protons 1-day JSON")
    ap.add_argument("--output", required=True, help="Output CSV")
    # Foam + hierarchy params
    ap.add_argument("--beta", type=float, default=0.05)
    ap.add_argument("--gamma_exp", type=float, default=1.0)
    ap.add_argument("--phi_ref", type=float, default=100.0)
    ap.add_argument("--tau_decay", type=float, default=10000.0)
    ap.add_argument("--S", type=float, default=18.5)
    ap.add_argument("--alpha0", type=float, default=0.1)
    ap.add_argument("--delta", type=float, default=0.02)
    ap.add_argument("--omega", type=float, default=1e-4)  # Hz (rough storm-band)
    ap.add_argument("--phi0", type=float, default=0.0)
    # ε_coh simple estimator
    ap.add_argument("--mu", type=float, default=0.01)
    ap.add_argument("--nu", type=float, default=0.0005)
    ap.add_argument("--epsilon0", type=float, default=0.0)
    # Peak handling
    ap.add_argument("--peak_time", type=str, default=None, help="ISO time of flux peak; if omitted uses max Φ")
    # Optional PLW coupling
    ap.add_argument("--with-plw", action="store_true", help="Estimate positron-like impulse retention via PLW simulate()")
    ap.add_argument("--plw-module", default="positron_lattice_writer", help="Module name to import simulate from")
    ap.add_argument("--plw-E_dep", type=float, default=1e-15)
    ap.add_argument("--plw-V_cell", type=float, default=1e-6)
    ap.add_argument("--plw-sigma_f", type=float, default=0.02)
    ap.add_argument("--plw-sgn", type=int, default=-1)
    ap.add_argument("--plw-u0", type=float, default=4.79e-10)
    ap.add_argument("--plw-lambda", dest="plw_lambda", type=float, default=0.05)
    ap.add_argument("--plw-eta", type=float, default=0.003)
    ap.add_argument("--plw-sigma", type=float, default=1e-4)
    ap.add_argument("--plw-steps", type=int, default=5000)
    ap.add_argument("--plw-dt", type=float, default=0.1)
    ap.add_argument("--plw-f0", type=float, default=0.0)
    ap.add_argument("--plw-target_band", type=float, default=0.05)
    ap.add_argument("--plw-seed", type=int, default=42)
    args = ap.parse_args()

    # Load series
    if args.from_goes:
        series = fetch_goes_1day_json()
    else:
        series = load_csv(args.input)
    if not series:
        print("No flux data found.")
        sys.exit(1)

    # Peak time
    if args.peak_time:
        t_peak = parse_time(args.peak_time)
    else:
        t_peak = max(series, key=lambda x: x[1])[0]
    t0 = series[0][0]
    t0_sec = 0.0

    # Try to import PLW simulate if requested
    plw_sim = None
    if args.with_plw:
        try:
            mod = __import__(args.plw_module)
            plw_sim = getattr(mod, "simulate")
        except Exception as e:
            print(f"[warn] Could not import simulate() from {args.plw_module}: {e}")
            plw_sim = None

    # Output
    fields = [
        "timestamp","Phi_pfu","dt_s","f","f_h","Gamma_amp","v_d_gain","epsilon_coh_est","state_flag"
    ]
    if plw_sim:
        fields += ["plw_f_imp","plw_retention_s"]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for (t, phi) in series:
            dt_peak = (t - t_peak).total_seconds()
            dt = (t - t0).total_seconds()

            # Foam trigger mapping (negative f during & after peak)
            f_val = -args.beta * (phi/args.phi_ref)**args.gamma_exp * math.exp(-max(0, dt_peak)/args.tau_decay)

            # Hierarchy modulation
            alpha_t = alpha_modulated(args.alpha0, args.delta, args.omega, args.phi0, t0_sec, dt)
            X_ratio = math.e  # demonstrator constant; can be parameterized
            f_h = math.exp(alpha_t * math.log(X_ratio)) * f_val

            # Amplification and drift
            Gamma_amp = math.exp(-args.S * f_val)     # f negative -> Γ>1
            v_d_gain = (1 + 0.1 * f_val)

            # Coherence estimator
            epsilon_coh_est = args.epsilon0 + args.mu * phi + args.nu * (f_val ** 2)

            # State flag
            if dt_peak < 0:
                flag = "pre-peak"
            elif abs(dt_peak) < 600:
                flag = "trigger_peak"
            elif f_val > -0.01:
                flag = "decay"
            else:
                flag = "sustain"

            row = [t.isoformat().replace("+00:00","Z"), phi, dt, f_val, f_h, Gamma_amp, v_d_gain, epsilon_coh_est, flag]

            if plw_sim:
                # Use PLW to emulate a local impulse under current params (one-shot estimate)
                stats, _series = plw_sim(
                    E_dep=args.plw_E_dep,
                    V_cell=args.plw_V_cell,
                    sigma_f=args.plw_sigma_f,
                    sgn=args.plw_sgn,
                    u0=args.plw_u0,
                    lam=args.plw_lambda,
                    eta=args.plw_eta,
                    sigma=args.plw_sigma,
                    steps=args.plw_steps,
                    dt=args.plw_dt,
                    f0=args.plw_f0,
                    target_band=args.plw_target_band,
                    rng_seed=args.plw_seed,
                )
                row += [stats.get("f_imp"), stats.get("retention_time_s")]

            w.writerow(row)

    print("Wrote", args.output)

if __name__ == "__main__":
    main()
