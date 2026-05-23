# -*- coding: utf-8 -*-
"""
ZTF Window Function Diagnostic

Our scan of 7 AGN candidates found a consistent ~1363d (3.7yr) pseudo-period
in ALL sources 鈥?independent of object type, location, or physical properties.
This tool formalizes that discovery: given a ZTF light curve, it:

1. Computes the window function (LS periodogram of time stamps alone)
2. Compares against multiple AGN to confirm window origin
3. Flags periods that are likely window artifacts

Usage:
    python window_diagnostic.py                 # run on all cached LCs
    python window_diagnostic.py --source all    # same
    python window_diagnostic.py --source 1ES_1959p650
"""
import sys, csv, os, glob
import numpy as np
from scipy import signal

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "lc")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(REPORT_DIR, exist_ok=True)


def window_function(t, min_period=10, max_period=None):
    """
    Compute the spectral window function: LS periodogram of uniform weights
    at the observed sampling times.
    
    Returns periods corresponding to strong sampling artifacts.
    """
    n = len(t)
    y_window = np.ones(n)  # flat signal
    baseline = t[-1] - t[0]
    if max_period is None:
        max_period = baseline * 0.9
    
    n_freq = min(int(baseline / min_period * 3), 5000)
    freqs = np.linspace(1.0/max_period, 1.0/min_period, n_freq)
    power = signal.lombscargle(t, y_window, freqs)
    periods = 1.0 / freqs
    
    return periods, power


def find_window_peaks(periods, power, n_peaks=5):
    """Find the n_peaks most significant window function peaks."""
    # Normalize to [0, 1]
    power_norm = power / np.max(power) if np.max(power) > 0 else power
    
    # Find peaks
    peak_mask = (power_norm[:-2] < power_norm[1:-1]) & (power_norm[1:-1] > power_norm[2:])
    peak_periods = periods[1:-1][peak_mask]
    peak_heights = power_norm[1:-1][peak_mask]
    
    # Sort by height
    top_idx = np.argsort(peak_heights)[-n_peaks:][::-1]
    return list(zip(peak_periods[top_idx], peak_heights[top_idx]))


def load_lc(csv_path):
    """Load a ZTF light curve, return (t, mag) or (None, None)."""
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                jd = float(r["hjd"])
                mag = float(r["mag"])
                rows.append((jd, mag))
            except:
                continue
    if not rows:
        return None, None
    rows.sort(key=lambda x: x[0])
    t = np.array([r[0] for r in rows])
    mag = np.array([r[1] for r in rows])
    return t, mag


def main():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        print("No data files found in", DATA_DIR)
        return
    
    window_results = {}
    
    for csv_path in sorted(csv_files):
        name = os.path.splitext(os.path.basename(csv_path))[0]
        name_display = name.replace("_", " ").replace("star", "*")
        
        t, mag = load_lc(csv_path)
        if t is None or len(t) < 5:
            continue
        
        # Window function
        periods, power = window_function(t)
        peaks = find_window_peaks(periods, power, n_peaks=5)
        
        window_results[name_display] = {
            "n_points": len(t),
            "baseline_days": float(t[-1] - t[0]),
            "baseline_years": float((t[-1] - t[0]) / 365.25),
            "window_peaks": [{"period_days": float(p), "strength": float(s)} for p, s in peaks],
            "strongest_peak_days": float(peaks[0][0]) if peaks else None,
        }
        
        print("\n" + "=" * 60)
        print("  {}: {} pts, {:.1f} yr baseline".format(name_display, len(t), (t[-1]-t[0])/365.25))
        print("=" * 60)
        print("  Window function peaks:")
        for p, s in peaks:
            marker = " <-- ARTIFACT BAND" if 1300 < p < 1450 else ""
            print("    {:.0f} d ({:.1f} yr)  strength={:.3f}{}".format(p, p/365.25, s, marker))
        
        # Check if strongest peak is in the artifact band
        if peaks and 1300 < peaks[0][0] < 1450:
            print("  鈿? Dominant peak in ZTF window artifact band (1300-1450d)")
        elif peaks:
            print("  鉁?Peak outside artifact band")
        else:
            print("  No significant window peaks")
    
    # Cross-source consistency
    print("\n" + "=" * 60)
    print("  CROSS-SOURCE WINDOW COMPARISON")
    print("=" * 60)
    print("  {:<25} {:>10} {:>10} {:>10}".format("Source", "Baseline", "N pts", "Win peak"))
    print("  " + "-" * 25 + " " + "-" * 10 + " " + "-" * 10 + " " + "-" * 10)
    for name, wr in sorted(window_results.items()):
        wp = "{:.0f}".format(wr["strongest_peak_days"]) if wr["strongest_peak_days"] else "-"
        print("  {:<25} {:>8.1f}yr {:>8} {:>10}d".format(
            name, wr["baseline_years"], wr["n_points"], wp))
    
    # Extract all window peaks for comparison
    all_main_peaks = [wr["strongest_peak_days"] for wr in window_results.values()
                      if wr["strongest_peak_days"]]
    if all_main_peaks:
        print("\n  Strongest peak statistics:")
        print("    Mean: {:.0f} d".format(np.mean(all_main_peaks)))
        print("    Std:  {:.0f} d".format(np.std(all_main_peaks)))
        print("    Range: {:.0f} - {:.0f} d".format(min(all_main_peaks), max(all_main_peaks)))
    
    # Save
    import json
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer, np.floating, np.bool_)):
                return obj.item()
            return super().default(obj)
    
    rpt_path = os.path.join(REPORT_DIR, "window_diagnostic.json")
    with open(rpt_path, "w") as f:
        json.dump(window_results, f, indent=2, cls=NpEncoder)
    print("\n  Saved: {}".format(rpt_path))


if __name__ == "__main__":
    main()

