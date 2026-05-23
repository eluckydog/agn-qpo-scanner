# -*- coding: utf-8 -*-
"""TESS AGN QPO: extract light curve from TPF and analyze."""
import sys, os
sys.path.insert(0, os.path.abspath("."))
import numpy as np
from astropy.io import fits
from scipy import stats
from agn_qpo_analyzer import analyze_light_curve, phase_coherence

fpath = "data/tess_lc/1ES1927_s0015.fits"
hdul = fits.open(fpath)
tp = hdul[1].data
quality = tp["QUALITY"]

# Find AGN in median image
median_img = np.median(tp["FLUX"], axis=0)
yp, xp = np.unravel_index(np.argmax(median_img), median_img.shape)
print("AGN at pixel ({}, {})".format(yp, xp))

# Aperture: 3x3 around AGN
ap_pix = [(yp+dy, xp+dx) for dy in range(-1,2) for dx in range(-1,2)]
# Sky: annulus 5-8 pixels, exclude 4x4 center
sky_pix = []
for dy in range(-8, 9):
    for dx in range(-8, 9):
        r = np.sqrt(dy**2 + dx**2)
        if 5 <= r <= 8 and (abs(dy) > 2 or abs(dx) > 2):
            sy, sx = yp+dy, xp+dx
            if 0 <= sy < 30 and 0 <= sx < 30:
                sky_pix.append((sy, sx))

time = tp["TIME"]
n = len(time)
src = np.array([np.mean([tp["FLUX"][i][y,x] for y,x in ap_pix]) for i in range(n)])
sky = np.array([np.mean([tp["FLUX"][i][y,x] for y,x in sky_pix]) for i in range(n)])
net = src - sky

good = (quality < 256) & np.isfinite(net) & (net > 5)
t, f = time[good], net[good]
mag = -2.5 * np.log10(f / np.median(f))

# Remove 3-sigma outliers
z = np.abs(stats.zscore(mag))
t, mag = t[z < 3], mag[z < 3]

print("Good: {} pts, {:.1f}h, mag std={:.4f}".format(
    len(t), (t[-1]-t[0])*24, np.std(mag)))

# Full QPO analysis
results = analyze_light_curve(t, mag, target_period=1900/86400, mc_sims=500)
print()
for k, v in sorted(results.items()):
    if k not in ("ls_periods", "ls_power_curve"):
        print("  {}: {}".format(k, v))

# Detailed period scan (2 min - 4 hours)
from agn_qpo_analyzer import lomb_scargle
from scipy import signal as sg
print()
mag_det = sg.detrend(mag)
periods, power, _, _ = lomb_scargle(t, mag_det, min_period=1e-4, max_period=0.17)

top5 = np.argsort(power)[-5:][::-1]
print("Top 5 periods:")
for idx in top5:
    p_min = periods[idx] * 1440
    p_s = periods[idx] * 86400
    print("  {:.1f} min ({:.0f}s): power={:.1f}".format(p_min, p_s, power[idx]))

# Check at known periods
print()
for ps in [1800, 1900, 2000, 2100, 2200, 2400, 2600, 3000, 3600, 7200]:
    p_d = ps / 86400.0
    nearest = np.argmin(np.abs(1.0/periods - 1.0/p_d)) if len(periods) > 0 else -1
    p_val = 1.0
    z_val = 0.0
    if nearest >= 0:
        phase = np.mod(t / p_d, 1.0) * 2 * np.pi
        R, z_val, p_val = phase_coherence(phase)
    m = " <-- REPORTED 1900s QPO" if ps == 1900 else ""
    print("  {}s ({:.1f}min): power={:.1f}, Rayleigh Z={:.1f}, p={:.6f}{}".format(
        ps, ps/60, power[nearest] if nearest >= 0 else 0, z_val, p_val, m))

hdul.close()
