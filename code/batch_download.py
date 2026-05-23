# -*- coding: utf-8 -*-
"""Batch download all 41 TESS sectors for 1ES 1927+654."""
import urllib.request, json, os, sys, time

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "tess_lc"))
os.makedirs(OUT, exist_ok=True)

RA, DEC = 291.92708, 65.62778
X, Y = 30, 30

# Get sector list
url = "https://mast.stsci.edu/tesscut/api/v0.1/sector?ra={}&dec={}".format(RA, DEC)
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read().decode())

sectors = sorted(set(s["sector"] for s in data["results"]))
print("Total sectors: {}".format(len(sectors)))
print("Sectors: {}".format(", ".join(sectors)))

# Download each
downloaded = 0
skipped = 0
failed = 0

for s in sectors:
    fname = "1ES1927_s{}.fits".format(s)
    fpath = os.path.join(OUT, fname)
    
    if os.path.exists(fpath) and os.path.getsize(fpath) > 100000:
        skipped += 1
        continue
    
    dl_url = "https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={}&dec={}&x={}&y={}&sector={}".format(RA, DEC, X, Y, s)
    try:
        req = urllib.request.Request(dl_url)
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read()
            with open(fpath, "wb") as f:
                f.write(body)
        
        mb = len(body) / 1e6
        print("  Sector {}: {:.1f} MB - OK".format(s, mb))
        downloaded += 1
        time.sleep(0.5)  # Rate limiting
    except Exception as e:
        print("  Sector {}: FAIL - {}".format(s, str(e)[:80]))
        failed += 1

print()
print("Summary: {} downloaded, {} skipped, {} failed".format(downloaded, skipped, failed))
