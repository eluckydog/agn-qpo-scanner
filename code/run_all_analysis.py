# -*- coding: utf-8 -*-
"""Run full QPO analysis on all downloaded candidates."""
import sys, csv, json, os, glob
sys.path.insert(0, "code")
import numpy as np
from agn_qpo_analyzer import analyze_light_curve
from candidates import get_candidate_by_name

DATA_DIR = "data/lc"
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
print("Found {} CSV files: {}".format(len(csv_files), [os.path.basename(f) for f in csv_files]))
print()

if not csv_files:
    print("NO DATA FILES FOUND. Check DATA_DIR.")
    sys.exit(1)

all_results = {}

for csv_path in sorted(csv_files):
    name = os.path.splitext(os.path.basename(csv_path))[0]
    name_display = name.replace("_", " ").replace("star", "*")

    # Load
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                jd = float(r["hjd"])
                mag = float(r["mag"])
                rows.append((jd, mag))
            except (ValueError, KeyError):
                continue
    rows.sort(key=lambda x: x[0])
    t = np.array([r[0] for r in rows])
    mag = np.array([r[1] for r in rows])

    # Target period
    c = get_candidate_by_name(name_display)
    target_period = c["period_days"] if c and c["period_days"] > 0 else None

    print("=" * 60)
    print("  {}: {} pts, {:.0f}d baseline".format(name_display, len(t), t[-1]-t[0]))
    print("=" * 60)

    results = analyze_light_curve(t, mag, target_period=target_period, mc_sims=500)

    if "error" in results:
        print("  ERROR: {}".format(results["error"]))
        all_results[name_display] = results
        continue

    print("  LS best period:     {:.0f} d".format(results["ls_period"]))
    print("  LS peak power:      {:.1f}".format(results["ls_power"]))
    print("  MC p-value:         {:.4f}".format(results["mc_p_value"]))
    print("  Significant @95%:   {}".format(results["significant_95"]))
    print("  Significant @99%:   {}".format(results["significant_99"]))
    print("  Phase Rayleigh R:   {:.4f}".format(results["phase_rayleigh_R"]))
    print("  Phase Rayleigh Z:   {:.1f}".format(results["phase_rayleigh_z"]))
    print("  Phase Rayleigh p:   {:.6f}".format(results["phase_rayleigh_p"]))
    print("  von Mises mu:       {:.1f} deg".format(np.degrees(results["vm_mu"])))
    print("  von Mises kappa:    {:.3f}".format(results["vm_kappa"]))
    print("  von Mises R^2:      {:.3f}".format(results["vm_r_squared"]))
    print("  VERDICT:            {}".format(results["verdict"]), end="")
    if results.get("confidence"):
        print(" ({})".format(results["confidence"]), end="")
    print()

    if target_period and "target_rayleigh_z" in results:
        print("  Target period ({}d): R={:.4f}, Z={:.1f}, p={:.4f}".format(
            target_period, results["target_rayleigh_R"],
            results["target_rayleigh_z"], results["target_rayleigh_p"]))

    all_results[name_display] = results

# Summary table
print()
print("=" * 60)
print("  SUMMARY - AGN QPO Scan")
print("=" * 60)
print("  {:<25} {:<20} {:<12} {:<12}".format("Source", "Verdict", "LS Period", "Rayleigh p"))
print("  " + "-" * 25 + " " + "-" * 20 + " " + "-" * 12 + " " + "-" * 12)
for name, res in sorted(all_results.items()):
    v = res.get("verdict", "?")[:19]
    p = "{:.0f}d".format(res.get("ls_period", 0)) if "ls_period" in res else "-"
    rp = "{:.6f}".format(res.get("phase_rayleigh_p", 1)) if "phase_rayleigh_p" in res else "-"
    print("  {:<25} {:<20} {:<12} {:<12}".format(name, v, p, rp))

# Save
with open(os.path.join(RESULTS_DIR, "qpo_scan_results.json"), "w") as f:
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer, np.floating, np.bool_)):
                return obj.item()
            return super().default(obj)
    json.dump(all_results, f, indent=2, cls=NpEncoder, default=str)
print("\n  Results saved to results/qpo_scan_results.json")
