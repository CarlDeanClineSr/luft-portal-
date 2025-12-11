import json, math, statistics, gzip, os
from pathlib import Path

def load_events(path):
    if path.endswith(".gz"):
        opener = gzip.open
    else:
        opener = open
    with opener(path, "rt") as f:
        for line in f:
            yield json.loads(line)

def compute_entropy_bins(event):
    bins = event["energy_flow_bins"]
    total = sum(bins) or 1.0
    p = [b/total for b in bins if b>0]
    return -sum(pi*math.log(pi) for pi in p)

def flag_overflow(event, baselines):
    gf = event["occupancy"]["global_fraction"]
    mu = baselines["global_fraction_mean"]
    sd = baselines["global_fraction_std"]
    return gf > mu + 3*sd

def establish_baseline(events, sample_size=1000):
    gvals=[]
    for i,e in enumerate(events):
        gvals.append(e["occupancy"]["global_fraction"])
        if i>=sample_size: break
    mu = statistics.mean(gvals)
    sd = statistics.pstdev(gvals)
    return {"global_fraction_mean": mu, "global_fraction_std": sd}

def main(infile, outfile):
    evs = list(load_events(infile))
    baseline = establish_baseline(iter(evs))
    for e in evs:
        e["entropy_H"] = compute_entropy_bins(e)
        e["overflow_flag"] = flag_overflow(e, baseline)
    with open(outfile, "w") as f:
        for e in evs:
            f.write(json.dumps(e)+"\n")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    args = ap.parse_args()
    main(args.infile, args.outfile)
