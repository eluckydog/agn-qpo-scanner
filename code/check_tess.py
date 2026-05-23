"""Quick TESS Target Search for AGN QPO candidates."""
import urllib.request, json

# TESS MAST API for target search
# Use the TIC catalog to search for AGN near known QPO hosts

# 1ES 1927+654 (known optical QPO at ~1900s)
agn_targets = [
    ("1ES 1927+654", 291.92708, 65.62778),   # ra, dec
    ("RE J1034+396", 158.60500, 39.40167),    # X-ray QPO
    ("3C 273", 187.27800, 2.05200),           # bright quasar
    ("Mrk 421", 166.11400, 38.20800),          # blazar
    ("PKS 2155-304", 329.71667, -30.22500),    # blazar
]

for name, ra, dec in agn_targets:
    query = {
        "service": "Mast.Tess.Pipeline",
        "params": {
            "ra": ra,
            "dec": dec,
            "radius": 0.01,
        },
        "format": "json",
    }
    url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.request.quote(json.dumps(query))
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode()
            print("{}: {} bytes".format(name, len(text)))
            # Look for target info
            if "target" in text.lower() or "tic" in text.lower():
                print("  Has TIC data: {}".format(text[:200]))
            else:
                print("  response: {}".format(text[:150]))
    except Exception as e:
        print("{}: FAIL {}".format(name, e))
