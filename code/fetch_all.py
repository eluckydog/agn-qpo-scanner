"""Batch fetch all AGN QPO candidates from ZTF."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from query_ztf import fetch_lc_by_coords
from candidates import CANDIDATES

for c in CANDIDATES:
    name = c["name"]
    if name == "PG 1302-102":
        print(f"  SKIP {name} (already downloaded)")
        continue
    print(f"\n=== {name} ===")
    try:
        path = fetch_lc_by_coords(c["ra"], c["dec"], name)
        if path:
            print(f"  OK: {os.path.getsize(path)} bytes")
        else:
            print(f"  NO DATA")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(2)
