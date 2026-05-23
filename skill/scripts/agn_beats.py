# -*- coding: utf-8 -*-
"""AGN Beats CLI — 活动星系核准周期振荡检测"""
import sys, os, json, glob, argparse
import numpy as np

# Resolve paths
SKILL_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SKILL_DIR, "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_DIR, "code"))

HELP_TEXT = """
AGN Beats — 活动星系核准周期振荡检测

Commands:
  search    搜索一个 AGN 的 QPO（一键）
  download  下载 TESS 光变数据
  analyze   分析单个 TESS sector
  batch     批次分析所有 sector
  window    窗口函数诊断
  list      列出已知候选源
"""


def cmd_search(args):
    """Search for QPO in a target."""
    from astropy.io import fits
    from scipy import stats, signal
    from agn_qpo_analyzer import analyze_light_curve, phase_coherence

    # Show what data exists
    tess_dir = os.path.join(PROJECT_DIR, "data", "tess_lc")
    ztf_dir = os.path.join(PROJECT_DIR, "data", "lc")
    
    source = args.source or "tess"
    target = args.target or ""
    
    print("AGN Beats QPO Search")
    print("=" * 50)
    print("Target: {}".format(target or "unknown"))
    print("Source: {}".format(source))
    
    if source == "tess" and target:
        files = sorted(glob.glob(os.path.join(tess_dir, "*{}*".format(target.replace("+", "").replace("-", "").replace(" ", "")) + "*.fits")))
        print("TESS files found: {}".format(len(files)))
        
        if files:
            # Quick analysis of first file
            hdul = fits.open(files[0])
            tp = hdul[1].data
            median_img = np.median(tp["FLUX"], axis=0)
            yp, xp = np.unravel_index(np.argmax(median_img), median_img.shape)
            
            ap_pix = [(yp+dy, xp+dx) for dy in range(-1,2) for dx in range(-1,2) 
                      if 0 <= yp+dy < 30 and 0 <= xp+dx < 30]
            sky_pix = []
            for dy in range(-8, 9):
                for dx in range(-8, 9):
                    r = np.sqrt(dy**2 + dx**2)
                    if 5 <= r <= 8 and (abs(dy) > 2 or abs(dx) > 2):
                        sy, sx = yp+dy, xp+dx
                        if 0 <= sy < 30 and 0 <= sx < 30:
                            sky_pix.append((sy, sx))
            
            n = len(tp)
            src = np.array([np.mean([tp["FLUX"][i][y,x] for y,x in ap_pix]) for i in range(n)])
            sky = np.array([np.mean([tp["FLUX"][i][y,x] for y,x in sky_pix]) for i in range(n)])
            net = src - sky
            time = tp["TIME"]
            good = (tp["QUALITY"] < 256) & np.isfinite(net) & (net > 5)
            t, f = time[good], net[good]
            
            z = np.abs(stats.zscore(f))
            t, f = t[z < 3], f[z < 3]
            mag = -2.5 * np.log10(f / np.median(f))
            
            print("  Points: {}, Baseline: {:.1f}h, Mag std: {:.4f}".format(
                len(t), (t[-1]-t[0])*24, np.std(mag)))
            
            results = analyze_light_curve(t, mag, target_period=1900/86400, mc_sims=300)
            print("  LS Period: {:.2f} d".format(results.get("ls_period", 0)))
            print("  MC p-value: {:.4f}".format(results.get("mc_p_value", 1)))
            print("  1900s QPO Z: {:.2f}, p: {:.4f}".format(
                results.get("target_rayleigh_z", 0), results.get("target_rayleigh_p", 1)))
            print("  Verdict: {}".format(results.get("verdict", "ERROR")))
            
            hdul.close()
    else:
        print("No data found. Use 'download' first.")


def cmd_download(args):
    """Download TESS data for a target."""
    import urllib.request, time as tm
    import json as js
    
    ra, dec = args.ra, args.dec
    name = args.name or "target_{}_{}".format(ra, dec)
    outdir = os.path.join(PROJECT_DIR, "data", "tess_lc")
    os.makedirs(outdir, exist_ok=True)
    
    # Get sector list
    url = "https://mast.stsci.edu/tesscut/api/v0.1/sector?ra={}&dec={}".format(ra, dec)
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = js.loads(resp.read().decode())
    
    sectors = sorted(set(s["sector"] for s in data["results"]))
    print("Found {} sectors for {} ({:.2f}, {:.2f})".format(len(sectors), name, ra, dec))
    
    dl_count = 0
    for s in sectors:
        clean_name = name.replace(" ", "_").replace("+", "p").replace("-", "m")
        fpath = os.path.join(outdir, "{}_s{}.fits".format(clean_name, s))
        if os.path.exists(fpath) and os.path.getsize(fpath) > 100000:
            continue
        
        dl_url = "https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={}&dec={}&x=30&y=30&sector={}".format(ra, dec, s)
        try:
            req = urllib.request.Request(dl_url)
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read()
                with open(fpath, "wb") as f:
                    f.write(body)
            mb = len(body) / 1e6
            print("  Sector {}: {:.1f} MB".format(s, mb))
            dl_count += 1
            tm.sleep(0.3)
        except Exception as e:
            print("  Sector {}: FAIL - {}".format(s, str(e)[:60]))
    
    print("Downloaded {} sectors".format(dl_count))


def cmd_analyze(args):
    """Analyze a single TESS TPF."""
    from astropy.io import fits
    from scipy import stats, signal
    from agn_qpo_analyzer import analyze_light_curve, phase_coherence
    
    fpath = args.fpath
    target_period = args.target_period or 1900  # seconds
    mc_sims = args.mc_sims or 300
    
    hdul = fits.open(fpath)
    tp = hdul[1].data
    
    median_img = np.median(tp["FLUX"], axis=0)
    yp, xp = np.unravel_index(np.argmax(median_img), median_img.shape)
    
    h, w = 30, 30
    ap_pix = [(yp+dy, xp+dx) for dy in range(-1,2) for dx in range(-1,2) 
              if 0 <= yp+dy < h and 0 <= xp+dx < w]
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
    good = (tp["QUALITY"] < 256) & np.isfinite(net) & (net > 5)
    t, f = time[good], net[good]
    
    for _ in range(3):
        z = np.abs(stats.zscore(f))
        if np.max(z) < 3: break
        t, f = t[z < 3], f[z < 3]
    
    mag = -2.5 * np.log10(f / np.median(f))
    
    print("Extracted light curve:")
    print("  Points: {}, Baseline: {:.1f}h, Mag std: {:.4f}".format(
        len(t), (t[-1]-t[0])*24, np.std(mag)))
    
    results = analyze_light_curve(t, mag, target_period=target_period/86400, mc_sims=mc_sims)
    
    print("\nResults:")
    for k, v in sorted(results.items()):
        if k not in ("ls_periods", "ls_power_curve"):
            print("  {}: {}".format(k, v))
    
    hdul.close()
    return results


def cmd_batch(args):
    """Batch analyze all TESS sectors for a target."""
    data_dir = args.dir or os.path.join(PROJECT_DIR, "data", "tess_lc")
    files = sorted(glob.glob(os.path.join(data_dir, "*.fits")))
    
    print("Batch analyzing {} files from {}".format(len(files), data_dir))
    
    from astropy.io import fits
    from scipy import stats, signal
    from agn_qpo_analyzer import analyze_light_curve, phase_coherence, lomb_scargle
    
    all_results = []
    for i, fpath in enumerate(files):
        sector = os.path.basename(fpath).split("_s")[1].split(".")[0] if "_s" in fpath else "unknown"
        
        try:
            hdul = fits.open(fpath)
            tp = hdul[1].data
            median_img = np.median(tp["FLUX"], axis=0)
            yp, xp = np.unravel_index(np.argmax(median_img), median_img.shape)
            
            h, w = 30, 30
            ap_pix = [(yp+dy, xp+dx) for dy in range(-1,2) for dx in range(-1,2)
                      if 0 <= yp+dy < h and 0 <= xp+dx < w]
            if len(ap_pix) < 5:
                hdul.close()
                print("  [{:2}/{}] Sector {}: FAIL (edge)".format(i+1, len(files), sector))
                continue
            
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
            good = (tp["QUALITY"] < 256) & np.isfinite(net) & (net > 5)
            t, f = time[good], net[good]
            
            for _ in range(3):
                z = np.abs(stats.zscore(f))
                if np.max(z) < 3: break
                t, f = t[z < 3], f[z < 3]
            
            if len(t) < 50:
                hdul.close()
                continue
            
            mag = -2.5 * np.log10(f / np.median(f))
            
            pl = analyze_light_curve(t, mag, target_period=1900/86400, mc_sims=300)
            phase = np.mod(t / (1900/86400), 1.0) * 2 * np.pi
            R, z, pv = phase_coherence(phase)
            
            out = {
                "sector": sector, "n_pts": len(t),
                "baseline_h": float((t[-1]-t[0])*24),
                "mag_std": float(np.std(mag)),
                "z_1900s": float(z), "p_1900s": float(pv),
                "verdict": pl.get("verdict", "ERROR"),
            }
            all_results.append(out)
            
            print("  [{:2}/{}] Sector {}: {} pts, std={:.4f}, Z={:.2f}, p={:.4f}, {}".format(
                i+1, len(files), sector, out["n_pts"],
                out["mag_std"], out["z_1900s"], out["p_1900s"],
                out["verdict"]))
            
            hdul.close()
        except Exception as e:
            print("  [{:2}/{}] Sector {}: FAIL ({})".format(i+1, len(files), sector, str(e)[:50]))
    
    z_vals = [r["z_1900s"] for r in all_results]
    p_vals = [r["p_1900s"] for r in all_results]
    print("\n--- Summary ---")
    print("  Sectors analyzed: {}".format(len(all_results)))
    print("  1900s Z range: {:.2f} - {:.2f}".format(min(z_vals), max(z_vals)))
    print("  1900s p range: {:.4f} - {:.4f}".format(min(p_vals), max(p_vals)))
    print("  p < 0.01: {}".format(sum(1 for p in p_vals if p < 0.01)))
    
    return all_results


def cmd_window(args):
    """Window function diagnostic."""
    try:
        sys.path.insert(0, os.path.join(PROJECT_DIR, "code"))
        from window_diagnostic import run_diagnostic
    except ImportError:
        print("Window diagnostic module not found at {}".format(
            os.path.join(PROJECT_DIR, "code", "window_diagnostic.py")))
        return
    run_diagnostic()


def cmd_list(args):
    """List known AGN QPO candidates."""
    print("AGN QPO Candidates")
    print("=" * 60)
    print("{:<20} {:<10} {:<10} {:<20}".format("Name", "RA", "DEC", "Notes"))
    print("-" * 60)
    candidates = [
        ("1ES 1927+654", "291.93", "+65.63", "~1900s optical QPO"),
        ("RE J1034+396", "158.61", "+39.40", "X-ray QPO ~3800s"),
        ("PG 1302-102", "196.28", "-10.44", "~5.2yr binary candidate"),
        ("OJ 287", "133.70", "+20.23", "~12yr binary"),
        ("3C 273", "187.28", "+2.05", "Bright quasar"),
        ("BL Lac", "330.68", "+42.28", "Blazar"),
        ("Mrk 421", "166.11", "+38.21", "TeV blazar"),
        ("PKS 2155-304", "329.72", "-30.23", "TeV blazar"),
        ("1ES 1959+650", "300.00", "+65.15", "TeV blazar"),
        ("M81*", "148.89", "+69.07", "Seyfert"),
        ("PSO J334", "334.12", "+22.50", "~1yr QPO candidate"),
    ]
    for name, ra, dec, note in candidates:
        print("{:<20} {:<10} {:<10} {:<20}".format(name, ra, dec, note))


def main():
    parser = argparse.ArgumentParser(description="AGN Beats — QPO Detection Tool")
    parser.add_argument("command", choices=["search", "download", "analyze", "batch", "window", "list", "help"],
                        help="Command to execute")
    parser.add_argument("--target", "-t", help="Target name (e.g., 1ES1927+654)")
    parser.add_argument("--source", "-s", choices=["ztf", "tess"], default="tess", help="Data source")
    parser.add_argument("--ra", type=float, help="RA in degrees")
    parser.add_argument("--dec", type=float, help="Dec in degrees")
    parser.add_argument("--name", help="Target name for download")
    parser.add_argument("--fpath", help="Path to FITS file for analysis")
    parser.add_argument("--target-period", type=int, default=1900, help="Target period in seconds (default: 1900)")
    parser.add_argument("--mc-sims", type=int, default=300, help="MC simulations (default: 300)")
    parser.add_argument("--dir", help="Data directory for batch analysis")
    
    args = parser.parse_args()
    
    commands = {
        "search": cmd_search,
        "download": cmd_download,
        "analyze": cmd_analyze,
        "batch": cmd_batch,
        "window": cmd_window,
        "list": cmd_list,
        "help": lambda a: print(HELP_TEXT.strip()),
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
