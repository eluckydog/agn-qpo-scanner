# -*- coding: utf-8 -*-
"""Run QPO analysis on remaining candidates (BL Lac, OJ 287, M81*, PSO)."""
import sys, csv, json, os, glob
sys.path.insert(0, "code")
import numpy as np
from agn_qpo_analyzer import analyze_light_curve
from candidates import get_candidate_by_name

DATA_DIR = "data/lc"
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Already analyzed: PG 1302, 1ES 1959, 3C 273
# Remaining: BL Lac, OJ 287, M81*, PSO J334
TARGETS = ["BL_Lac.csv", "OJ_287.csv", "M81star_Optical.csv", "PSO_J334.2028p01.4075.csv"]

all_results = {}  # will merge with previous results

for csv_name in TARGETS:
    csv_path = os.path.join(DATA_DIR, csv_name)
    if not os.path.exists(csv_path):
        print("SKIP: {} not found".format(csv_name))
        continue

    name = os.path.splitext(csv_name)[0]
    name_display = name.replace("_", " ").replace("star", "*")

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

# Print summary
print()
print("=" * 60)
print("  RESULTS")
print("=" * 60)
for name, res in sorted(all_results.items()):
    v = res.get("verdict", "?")
    rp = "{:.6f}".format(res.get("phase_rayleigh_p", 1)) if "phase_rayleigh_p" in res else "-"
    print("  {:<25} {:<20} p={}".format(name, v, rp))

# Save
rpt = os.path.join(RESULTS_DIR, "qpo_remaining_results.json")
with open(rpt, "w") as f:
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer, np.floating, np.bool_)):
                return obj.item()
            return super().default(obj)
    json.dump(all_results, f, indent=2, cls=NpEncoder, default=str)
print("\n  Saved {}".format(rpt))
