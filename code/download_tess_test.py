"""Download TESS LC for 1ES 1927+654 (first sector)."""
import urllib.request, json, os, sys

ra, dec = 291.92708, 65.62778
outdir = "data/tess_lc"
os.makedirs(outdir, exist_ok=True)

sector = 15
url = "https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={}&dec={}&radius=0.01&sector={}&product=lc".format(ra, dec, sector)
fpath = os.path.join(outdir, "1ES1927_s{:04d}.fits".format(sector))

print("Downloading TESS sector {}...".format(sector))
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=120) as resp:
    body = resp.read()
    with open(fpath, "wb") as f:
        f.write(body)
    print("Done: {} ({} bytes)".format(fpath, len(body)))
