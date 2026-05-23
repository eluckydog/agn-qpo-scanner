"""
AGN QPO Pipeline — updated for v2 query_ztf
"""
import sys, os, json, time, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import numpy as np

from candidates import CANDIDATES
from query_ztf import fetch_lc_by_coords
from agn_qpo_analyzer import analyze_light_curve

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "lc")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def load_lc(csv_path):
    """Load ZTF light curve CSV (with full header)."""
    import csv
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                jd = float(r["hjd"])
                mag = float(r["mag"])
                magerr = float(r.get("magerr", 0.01))
                rows.append((jd, mag, magerr))
            except (ValueError, KeyError):
                continue
    if not rows:
        return None, None, None
    rows.sort(key=lambda x: x[0])
    t = np.array([r[0] for r in rows])
    mag = np.array([r[1] for r in rows])
    err = np.array([r[2] for r in rows])
    return t, mag, err


def load_cache():
    """Return set of already-downloaded source names."""
    cached = set()
    for f in glob.glob(os.path.join(DATA_DIR, "*.csv")):
        name = os.path.splitext(os.path.basename(f))[0]
        cached.add(name)
    return cached


def analyze_candidate(t, mag, name, target_period=None):
    """Run full QPO analysis pipeline."""
    print(f"\n  ─── Analyzing {name} ───")
    print(f"  {len(t)} points, {(t[-1]-t[0]):.0f}d baseline")

    results = analyze_light_curve(t, mag, target_period=target_period, mc_sims=500)

    if "error" in results:
        print(f"  ❌ {results['error']}")
        return results

    # Print
    print(f"  LS best period: {results['ls_period']:.1f} d")
    print(f"  LS peak power:  {results['ls_power']:.3f}")
    print(f"  MC p-value:     {results['mc_p_value']:.4f}")
    print(f"  MC sig @95%:    {results.get('significant_95', False)}")
    print(f"  MC sig @99%:    {results.get('significant_99', False)}")
    print(f"  ─────────────────────────────")
    print(f"  Phase Rayleigh R: {results['phase_rayleigh_R']:.4f}")
    print(f"  Phase Rayleigh Z: {results['phase_rayleigh_z']:.1f}")
    print(f"  Phase Rayleigh p: {results['phase_rayleigh_p']:.6f}")
    print(f"  von Mises μ:      {np.degrees(results['vm_mu']):.1f}°")
    print(f"  von Mises κ:      {results['vm_kappa']:.3f}")
    print(f"  von Mises R²:     {results['vm_r_squared']:.3f}")
    print(f"  Verdict:          {results.get('verdict', '?')}")
    return results


def run_all(mode="fast"):
    """
    mode='fast': only analyze already-cached data
    mode='fetch': fetch all missing, then analyze
    """
    os.makedirs(REPORT_DIR, exist_ok=True)
    cached = load_cache()
    all_results = {}

    for c in CANDIDATES:
        name = c["name"]
        safe = name.replace(" ", "_").replace("*", "star").replace("+", "p").replace("-", "m")
        target_period = c["period_days"] if c["period_days"] > 0 else None

        csv_path = os.path.join(DATA_DIR, f"{safe}.csv")
        have_data = os.path.exists(csv_path) and os.path.getsize(csv_path) > 200

        if not have_data and mode == "fetch":
            print(f"\n=== Fetching {name} ===")
            path = fetch_lc_by_coords(c["ra"], c["dec"], name)
            have_data = path is not None

        if have_data:
            t, mag, err = load_lc(csv_path)
            if t is not None and len(t) > 10:
                results = analyze_candidate(t, mag, name, target_period)
                all_results[name] = results
                time.sleep(1)  # polite

    # Summary
    print(f"\n\n{'='*60}")
    print("  SUMMARY TABLE")
    print(f"{'='*60}")
    print(f"  {'Source':<25} {'Verdict':<20} {'Period':<12} {'p-value':<10}")
    print(f"  {'─'*25} {'─'*20} {'─'*12} {'─'*10}")
    for name, res in all_results.items():
        verdict = res.get("verdict", "ERROR")[:20]
        period = f"{res.get('ls_period', 0):.0f}d" if "ls_period" in res else "-"
        p_val = f"{res.get('phase_rayleigh_p', 1):.4f}" if "phase_rayleigh_p" in res else "-"
        print(f"  {name:<25} {verdict:<20} {period:<12} {p_val:<10}")

    # Save
    rpt = os.path.join(REPORT_DIR, "qpo_scan.json")
    with open(rpt, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Saved: {rpt}")


if __name__ == "__main__":
    import time

    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        run_all(mode="fetch")
    else:
        run_all(mode="fast")
