"""Download TESS SPOC light curve for 1ES 1927+654, sector 15."""
import urllib.request, os

ra, dec = 291.92708, 65.62778
outdir = "data/tess_lc"
os.makedirs(outdir, exist_ok=True)

fpath = os.path.join(outdir, "1ES1927_s0015.fits")
if os.path.exists(fpath) and os.path.getsize(fpath) > 10000:
    print("Cached: {} ({} bytes)".format(fpath, os.path.getsize(fpath)))
else:
    url = "https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={}&dec={}&x=30&y=30&sector=0015".format(ra, dec)
    print("Downloading...")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read()
        with open(fpath, "wb") as f:
            f.write(body)
    print("Saved: {} ({} bytes)".format(fpath, len(body)))
