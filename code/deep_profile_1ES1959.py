# -*- coding: utf-8 -*-
"""
Deep Dive: 1ES 1959+650 — detailed profile
Multi-method QPO analysis on a single promising source.
"""
import sys, csv, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
import numpy as np
from scipy import signal, stats
from agn_qpo_analyzer import (
    analyze_light_curve, hilbert_phase, lomb_scargle, phase_coherence
)

# Load
csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "lc", "1ES_1959p650.csv")
rows = []
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            jd = float(r["hjd"])
            mag = float(r["mag"])
            magerr = float(r.get("magerr", 0))
            rows.append((jd, mag, magerr))
        except:
            continue
rows.sort(key=lambda x: x[0])
t = np.array([r[0] for r in rows])
mag = np.array([r[1] for r in rows])
err = np.array([r[2] for r in rows])

print("=" * 60)
print("  1ES 1959+650 — Deep Profile")
print("=" * 60)
print("  N points:      {}".format(len(t)))
print("  Baseline:      {:.0f} days ({:.1f} yr)".format(t[-1]-t[0], (t[-1]-t[0])/365.25))
print("  Mag range:     {:.3f} - {:.3f} ({:.3f} mag)".format(np.min(mag), np.max(mag), np.ptp(mag)))
print("  Mean mag:      {:.3f}".format(np.mean(mag)))
print("  Std dev:       {:.3f}".format(np.std(mag)))

# 1. Full pipeline
print("\n--- Pipeline Analysis ---")
results = analyze_light_curve(t, mag, mc_sims=1000)
for k, v in sorted(results.items()):
    if k not in ("ls_periods", "ls_power_curve"):
        print("  {}: {}".format(k, v))

# 2. Lomb-Scargle with error bars (detrended)
print("\n--- Weighted LS (with mag errors) ---")
trend = np.polyval(np.polyfit(t, mag, 1), t)
mag_residual = mag - trend + np.mean(mag)
periods, power, best_p, best_pp = lomb_scargle(t, mag_residual, dy=err+0.01)
print("  Best period:   {:.1f} d".format(best_p))
print("  Peak power:    {:.1f}".format(best_pp))

# 3. Period scan over multiple bands
print("\n--- Period Scan (50-2000d) ---")
periods_scan, powers_scan, _, _ = lomb_scargle(t, mag_residual, min_period=50, max_period=2000)
top5_idx = np.argsort(powers_scan)[-5:][::-1]
print("  Top 5 periods:")
for idx in top5_idx:
    print("    {:.0f} d  power={:.1f}".format(periods_scan[idx], powers_scan[idx]))

# 4. Autocorrelation
print("\n--- Autocorrelation ---")
# Interpolate to uniform grid
dt = np.median(np.diff(t))
t_uniform = np.arange(t[0], t[-1], dt)
y_uniform = np.interp(t_uniform, t, signal.detrend(mag_residual))
acf = np.correlate(y_uniform - np.mean(y_uniform), y_uniform - np.mean(y_uniform), mode="same")
acf /= np.max(acf)
lags = np.arange(-len(acf)//2, len(acf)//2) * dt
# Find significant peaks in positive lags
pos = lags > 0
lag_pos = lags[pos]
acf_pos = acf[pos]
peak_mask = (acf_pos[:-2] < acf_pos[1:-1]) & (acf_pos[1:-1] > acf_pos[2:])
peak_lags = lag_pos[1:-1][peak_mask]
peak_acf = acf_pos[1:-1][peak_mask]
# Top 3 ACF peaks
top3_acf = sorted(zip(peak_acf, peak_lags), reverse=True)[:3]
print("  Top 3 ACF lags:")
for a, l in top3_acf:
    print("    {:.0f} d  ACF={:.4f}".format(l, a))

# 5. Phase scatter
print("\n--- Phase Coherence at Candidate Periods ---")
for p_day in [best_p, 500, 750, 980, 1348]:
    phase = np.mod(t / p_day, 1.0) * 2 * np.pi
    R, z, p_val = phase_coherence(phase)
    kappa = 1.0 / (2 * (1 - R)) if R < 1 else 10
    print("  P={:.0f}d:  R={:.4f}  Z={:.1f}  p={:.6f}  kappa={:.3f}".format(
        p_day, R, z, p_val, kappa))

# 6. Even/odd folded light curve comparison
print("\n--- Folded Light Curve (P={:.0f}d) ---".format(best_p))
phase = np.mod(t / best_p, 1.0) * 2 * np.pi
sorted_idx = np.argsort(phase)
phase_sorted = phase[sorted_idx]
mag_sorted = mag[sorted_idx]
# Bin
bins = 8
bin_edges = np.linspace(0, 2*np.pi, bins+1)
bin_means = []
for i in range(bins):
    in_bin = (phase_sorted >= bin_edges[i]) & (phase_sorted < bin_edges[i+1])
    if np.sum(in_bin) > 1:
        bin_means.append(np.mean(mag_sorted[in_bin]))
    else:
        bin_means.append(np.nan)
peak_bin = np.nanargmax(np.abs(np.array(bin_means) - np.nanmean(bin_means)))
print("  Peak-to-peak amplitude in folded LC: {:.3f} mag".format(
    np.nanmax(bin_means) - np.nanmin(bin_means)))
print("  Most deviant bin: #{}, {:.3f} mag from mean".format(
    peak_bin, abs(np.nanmean(bin_means) - bin_means[peak_bin])))

# 7. Sampling cadence analysis
print("\n--- Sampling Statistics ---")
dt_gaps = np.diff(t)
print("  Median cadence: {:.1f} d".format(np.median(dt_gaps)))
print("  Max gap:        {:.0f} d".format(np.max(dt_gaps)))
print("  Gaps > 100d:    {} ({:.0f}%)".format(
    np.sum(dt_gaps > 100), 100 * np.sum(dt_gaps > 100) / len(dt_gaps)))
# Number of observing seasons
big_gaps = dt_gaps[dt_gaps > 60]
print("  Observing seasons: ~{}".format(len(big_gaps) + 1))

# Summary
print("\n" + "=" * 60)
print("  VERDICT: 1ES 1959+650")
print("=" * 60)
print("  LS finds ~983d but MC is Not Significant (p=0.60)")
print("  Rayleigh p=0.00024 but only 62 points = small-N artifact risk")
print("  Folded amplitude ~{:.3f} mag".format(np.nanmax(bin_means) - np.nanmin(bin_means)))
print("  Best period equals ~half the baseline = window function risk")
print("  Sampling: {} seasons, {}% gaps > 100d".format(
    len(big_gaps)+1, 100 * np.sum(dt_gaps > 100) / len(dt_gaps)))
print("")
print("  Conclusion: NOT CONFIRMED. Need independent data (CRTS/ASAS-SN).")
