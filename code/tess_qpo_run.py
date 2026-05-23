# -*- coding: utf-8 -*-
"""Extract TESS light curve from TPF and run QPO analysis."""
import sys, os, json
sys.path.insert(0, ".")
import numpy as np
from astropy.io import fits
from agn_qpo_analyzer import analyze_light_curve

# 1. Load TPF
fpath = "data/tess_lc/1ES1927_s0015.fits"
hdul = fits.open(fpath)
tp_data = hdul[1].data
aperture = hdul[2].data

# 2. Extract light curve (sum flux over aperture, subtract background)
time = tp_data["TIME"]  # BTJD days
flux = np.array([np.sum(tp_data["FLUX"][i] * (aperture > 0)) for i in range(len(tp_data))])
flux_bkg = np.array([np.sum(tp_data["FLUX_BKG"][i] * (aperture > 0)) for i in range(len(tp_data))])
flux_err = np.sqrt(np.array([np.sum(tp_data["FLUX_ERR"][i]**2 * (aperture > 0)) for i in range(len(tp_data))]))

# Quality flag mask
quality = tp_data["QUALITY"]
good = quality < 256  # allow minor flags

# Remove NaN/Inf
good &= np.isfinite(time) & np.isfinite(flux) & np.isfinite(flux_bkg)
good &= (flux > 0)

t = time[good]
f = flux[good]  # background already subtracted by SPOC pipeline
fe = flux_err[good]
# Clip negative flux
f = np.clip(f, 1e-6, None)

print("=" * 60)
print("  1ES 1927+654 — TESS Sector 15")
print("=" * 60)
print("  Cadences: {} total, {} good".format(len(time), np.sum(good)))
print("  Baseline: {:.4f} days ({:.1f} hours)".format(t[-1]-t[0], (t[-1]-t[0])*24))
print("  Median cadence: {:.1f} min".format(np.median(np.diff(t))*24*60))
print("  Flux range: {:.1f} - {:.1f} e-/s".format(np.min(f), np.max(f)))
print("  S/N: {:.1f}".format(np.mean(f) / np.mean(fe)))

# 3. Convert to magnitude
mag = -2.5 * np.log10(f / np.median(f))
print("  Mag range: {:.3f} - {:.3f}".format(np.min(mag), np.max(mag)))
print("  Mag std: {:.4f}".format(np.std(mag)))

# 4. Run QPO analysis
# TESS cadence is ~2 min, so search for QPO in 0.001-5 day range
print("\n--- QPO Analysis ---")
results = analyze_light_curve(t, mag, target_period=0.022, mc_sims=500)  # 1900s = 0.022d

for k, v in sorted(results.items()):
    if k not in ("ls_periods", "ls_power_curve"):
        print("  {}: {}".format(k, v))

# Period scan in the QPO band (0.01 - 0.1 days = ~14 min to 2.4 hours)
from scipy import signal
baseline = t[-1] - t[0]
# Remove linear trend first
from scipy import signal as sg
mag_detrended = sg.detrend(mag)
freqs = np.linspace(10, 1000, 500)  # 10/day to 1000/day = ~1.4 min to 2.4 hours
power = sg.lombscargle(t, mag_detrended, freqs)
periods_hr = 24.0 / freqs  # hours
periods_min = periods_hr * 60  # minutes

print("\n--- Periodogram (minutes) ---")
top3 = np.argsort(power)[-3:][::-1]
for idx in top3:
    print("  Period: {:.1f} min, Power: {:.1f}".format(periods_min[idx], power[idx]))

# Check 1900s specifically
p_1900s = 1900 / 86400  # days
p_1900s_hr = p_1900s * 24
p_1900s_min = p_1900s * 1440
# Power at nearest frequency
f_1900s = 1.0 / p_1900s
nearest = np.argmin(np.abs(freqs - f_1900s))
print("\n--- Known QPO Period: {} min (1900s) ---".format(round(p_1900s_min, 1)))
print("  Power at {:.0f}s: {:.1f}".format(1900, power[nearest]))
print("  Rank among all frequencies: #{}/{}".format(
    len(power) - np.where(np.argsort(power) == nearest)[0][0], len(power)))

# Phase folding at 1900s
phase = np.mod(t / p_1900s, 1.0) * 2 * np.pi
from agn_qpo_analyzer import phase_coherence, fit_von_mises
R, z, p_val = phase_coherence(phase)
mu, kappa, r2 = fit_von_mises(phase)
print("  Rayleigh R={:.4f}, Z={:.1f}, p={:.6f}".format(R, z, p_val))
print("  von Mises mu={:.1f} deg, kappa={:.3f}, R2={:.3f}".format(
    np.degrees(mu), kappa, r2))

hdul.close()
