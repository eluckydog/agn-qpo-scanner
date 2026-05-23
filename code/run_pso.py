# -*- coding: utf-8 -*-
"""Run PSO J334 only (got SIGKILL'd in batch)."""
import sys, csv
sys.path.insert(0, "code")
import numpy as np
from agn_qpo_analyzer import analyze_light_curve
from candidates import get_candidate_by_name

csv_path = "data/lc/PSO_J334.2028p01.4075.csv"
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
rows.sort(key=lambda x: x[0])
t = np.array([r[0] for r in rows])
mag = np.array([r[1] for r in rows])

print("PSO J334: {} pts, {:.0f}d baseline".format(len(t), t[-1]-t[0]))
results = analyze_light_curve(t, mag, target_period=542, mc_sims=200)

for k, v in sorted(results.items()):
    if k not in ("ls_periods", "ls_power_curve"):
        print("  {}: {}".format(k, v))
