def test_harmonic_clustering(chi_series, harmonic_levels=[0.15, 0.30, 0.45], window=0.02):
    """
    LUFT HARMONIC CLUSTERING TEST
    -----------------------------
    The real test: Do chi values physically lock (CLUSTER) at the mechanical 
    harmonic levels (0.15, 0.30, 0.45), or just randomly pass through them?
    
    Calculates the actual occupation fraction within ±window of each harmonic 
    and compares it to a completely uniform (random) distribution baseline.
    
    A >3.0x excess ratio indicates a physical attractor state (geometric lock).
    """
    results = {}
    n = len(chi_series)
    
    # Fail-safe for empty data
    if n == 0:
        return results
        
    chi_min = min(chi_series)
    chi_max = max(chi_series)
    chi_range = chi_max - chi_min
    
    # Baseline: Expected probability of landing in the window randomly.
    # The if-statement prevents a divide-by-zero crash if a file has a flat 0.0 range.
    if chi_range > 0:
        expected_frac = (2 * window) / chi_range
    else:
        expected_frac = 0.0
        
    for level in harmonic_levels:
        # Count how many data points structurally locked into this harmonic window
        in_window = np.sum(
            (chi_series >= level - window) & 
            (chi_series <= level + window)
        )
        
        observed_frac = in_window / n
        
        # Calculate the mechanical excess (signal above random chance)
        if expected_frac > 0:
            excess_ratio = observed_frac / expected_frac
        else:
            excess_ratio = 0.0
            
        # 3x excess = undeniable physical clustering
        is_attractor = excess_ratio > 3.0  
        
        results[level] = {
            'count':         int(in_window),
            'observed_pct':  round(100 * observed_frac, 2),
            'expected_pct':  round(100 * expected_frac, 2),
            'excess_ratio':  round(excess_ratio, 2),
            'attractor':     is_attractor
        }
        
        # Clean, aligned terminal readout
        status_flag = "✅ ATTRACTOR CONFIRMED" if is_attractor else "— no clustering"
        print(f"  χ = {level:.2f}:  {observed_frac*100:5.1f}% observed vs "
              f"{expected_frac*100:5.1f}% expected  "
              f"(ratio: {excess_ratio:5.1f}x)  {status_flag}")
              
    return results
