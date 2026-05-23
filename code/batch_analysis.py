# -*- coding: utf-8 -*-
"""Batch QPO analysis: all TESS sectors for 1ES 1927+654."""
import sys, os, json, glob, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from astropy.io import fits
from scipy import stats, signal
from agn_qpo_analyzer import analyze_light_curve, phase_coherence, lomb_scargle

DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "tess_lc"))

def extract_lc(fpath):
    """Extract clean light curve from TESS TPF."""
    hdul = fits.open(fpath)
    tp = hdul[1].data
    quality = tp["QUALITY"]
    
    # Find AGN in median image
    median_img = np.median(tp["FLUX"], axis=0)
    yp, xp = np.unravel_index(np.argmax(median_img), median_img.shape)
    
    # Aperture: 3x3 around AGN (clip to image boundary)
    h, w = 30, 30
    ap_pix = []
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            sy, sx = yp+dy, xp+dx
            if 0 <= sy < h and 0 <= sx < w:
                ap_pix.append((sy, sx))
    # Sky: annulus 5-8 pix, exclude 4x4 center
    sky_pix = []
    for dy in range(-8, 9):
        for dx in range(-8, 9):
            r = np.sqrt(dy**2 + dx**2)
            if 5 <= r <= 8 and (abs(dy) > 2 or abs(dx) > 2):
                sy, sx = yp+dy, xp+dx
                if 0 <= sy < h and 0 <= sx < w:
                    sky_pix.append((sy, sx))
    
    n = len(tp)
    src = np.array([np.mean([tp["FLUX"][i][y,x] for y,x in ap_pix]) for i in range(n)])
    sky = np.array([np.mean([tp["FLUX"][i][y,x] for y,x in sky_pix]) for i in range(n)])
    net = src - sky
    
    time = tp["TIME"]
    good = (quality < 256) & np.isfinite(net) & (net > 5)
    t, f = time[good], net[good]
    
    # Check for enough aperture pixels and >= 20 valid points
    if len(ap_pix) < 5 or len(t) < 20:
        hdul.close()
        return None, None, None, 0
    
    # Remove 3-sigma outliers iteratively
    for _ in range(3):
        z = np.abs(stats.zscore(f))
        if np.max(z) < 3:
            break
        t, f = t[z < 3], f[z < 3]
        if len(t) < 20:
            hdul.close()
            return None, None, None, 0
    
    # Convert to normalized mag
    mag = -2.5 * np.log10(f / np.median(f))
    
    hdul.close()
    return t, mag, f, yp

def analyze_sector(step, total, sector, t, mag):
    """Run full QPO analysis on one sector."""
    result = {"sector": str(sector), "n_pts": len(t), "baseline_days": float(t[-1]-t[0])}
    
    if len(t) < 50:
        result["verdict"] = "INSUFFICIENT DATA"
        return result
    
    baseline = t[-1] - t[0]
    mag_det = signal.detrend(mag)
    
    # 1. Full pipeline (target period = 1900s)
    pl = analyze_light_curve(t, mag, target_period=1900/86400, mc_sims=300)
    result.update({
        "ls_period_days": float(pl.get("ls_period", -1)),
        "ls_power": float(pl.get("ls_power", -1)),
        "mc_p": float(pl.get("mc_p_value", -1)),
        "sig_95": bool(pl.get("significant_95", False)),
        "sig_99": bool(pl.get("significant_99", False)),
        "verdict": pl.get("verdict", "ERROR"),
    })
    
    # 2. Target QPO check (1900s)
    phase = np.mod(t / (1900/86400), 1.0) * 2 * np.pi
    R, z, pv = phase_coherence(phase)
    result.update({"target_1900s_Z": float(z), "target_1900s_p": float(pv)})
    
    # 3. Period scan (1.4 min - 6 hours)
    try:
        periods, power, _, _ = lomb_scargle(t, mag_det, min_period=1e-4, max_period=0.25)
        top5 = np.argsort(power)[-5:][::-1]
        result["ls_periods_min"] = [round(float(periods[i])*1440, 1) for i in top5]
        result["ls_powers"] = [round(float(power[i]), 3) for i in top5]
    except Exception:
        result["ls_periods_min"] = []
        result["ls_powers"] = []
    
    # 4. Scan a range of candidate periods
    candidate_ps = [1500, 1800, 1900, 2000, 2100, 2200, 2400, 2600, 
                    3000, 3600, 7200, 14400, 21600, 43200, 86400]
    cand_results = {}
    for ps in candidate_ps:
        p_d = ps / 86400.0
        phase = np.mod(t / p_d, 1.0) * 2 * np.pi
        R, z, pv = phase_coherence(phase)
        cand_results[ps] = {"Z": float(z), "p": float(pv)}
    result["candidates"] = cand_results
    
    return result


# Main
files = sorted(glob.glob(os.path.join(DATA, "1ES1927_s*.fits")))
print("Found {} TESS files in {}".format(len(files), DATA))
print()

results = []
n_ok = 0
n_skip = 0

for i, fpath in enumerate(files):
    sector = os.path.basename(fpath).split("_s")[1].split(".")[0]
    
    t, mag, raw_flux, yp = extract_lc(fpath)
    if t is None:
        print("  [{:2d}/{}] Sector {}: FAIL (extraction)".format(i+1, len(files), sector))
        n_skip += 1
        continue
    
    result = analyze_sector(i+1, len(files), sector, t, mag)
    results.append(result)
    
    # Print summary
    std = np.std(mag)
    print("  [{:2d}/{}] Sector {}: {} pts, {:.1f}h, mag std={:.4f}, Z(1900s)={:.1f}, p={:.4f}, verdict={}".format(
        i+1, len(files), sector, result["n_pts"], 
        result["baseline_days"]*24, std,
        result["target_1900s_Z"], result["target_1900s_p"],
        result["verdict"]))
    
    n_ok += 1

# Summary
print()
print("=" * 60)
print("  BATCH COMPLETE: {} OK, {} skipped/empty".format(n_ok, n_skip))
print("=" * 60)

# Sector statistics for 1900s QPO
z_vals = [r["target_1900s_Z"] for r in results]
p_vals = [r["target_1900s_p"] for r in results]
sig_1900 = sum(1 for p in p_vals if p < 0.01)
print()
print("  1900s QPO detection across {} sectors:".format(len(results)))
print("    Z range: {:.2f} - {:.2f}".format(min(z_vals), max(z_vals)))
print("    p range: {:.6f} - {:.4f}".format(min(p_vals), max(p_vals)))
print("    Sectors with p<0.01: {} / {}".format(sig_1900, len(results)))

# Best candidate across all sectors
all_cand_z = {}
for r in results:
    for ps, cd in r.get("candidates", {}).items():
        all_cand_z.setdefault(ps, []).append(cd["Z"])

print()
print("  Mean Rayleigh Z by candidate period:")
for ps in sorted(all_cand_z.keys()):
    mean_z = np.mean(all_cand_z[ps])
    max_z = np.max(all_cand_z[ps])
    print("    {:5d}s ({:.0f}min): mean Z={:.2f}, max Z={:.2f}".format(
        ps, ps/60, mean_z, max_z))

# Save
out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results", "tess_batch_results.json"))
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
print()
print("Results saved to: {}".format(out))
