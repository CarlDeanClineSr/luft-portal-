def test_harmonic_clustering(chi_series, harmonic_levels=[0.15, 0.30, 0.45],
                              window=0.02):
    """
    The real test: do chi values CLUSTER at harmonic levels,
    or just pass through them?
    
    Computes occupation fraction within ±window of each harmonic level.
    Compare to the expected fraction if chi were uniformly distributed.
    
    If chi is uniform over [0, 0.45]:
      Expected fraction within ±0.02 of any level = 0.04/0.45 = 8.9%
    
    Your 0.15 result showed 52-53% — a 6× excess.
    If 0.30 and 0.45 are true harmonics, they should show similar excess.
    """
    results = {}
    n = len(chi_series)
    
    # Baseline: expected fraction if uniform
    chi_range = max(chi_series) - min(chi_series)
    expected_frac = (2 * window) / chi_range
    
    for level in harmonic_levels:
        in_window = np.sum(
            (chi_series >= level - window) & 
            (chi_series <= level + window)
        )
        observed_frac = in_window / n
        excess_ratio  = observed_frac / expected_frac
        
        results[level] = {
            'count':         int(in_window),
            'observed_pct':  round(100 * observed_frac, 2),
            'expected_pct':  round(100 * expected_frac, 2),
            'excess_ratio':  round(excess_ratio, 2),
            'attractor':     excess_ratio > 3.0   # ← 3× excess = real clustering
        }
        
        print(f"  χ = {level}:  {observed_frac*100:.1f}% observed vs "
              f"{expected_frac*100:.1f}% expected  "
              f"(ratio: {excess_ratio:.1f}×)  "
              f"{'✅ ATTRACTOR' if excess_ratio > 3.0 else '— no clustering'}")
    
    return results
