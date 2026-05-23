"""TESS AGN QPO — setup and first data pull."""
import urllib.request, json, os, sys

code_dir = os.path.dirname(__file__)
sys.path.insert(0, code_dir)
from candidates import get_candidate_by_name

# AGN targets with TESS coverage potential
# Focus on known QPO candidates + bright blazars
AGN_TARGETS = [
    ("1ES 1927+654", 291.92708, 65.62778, "known optical QPO ~1900s"),
    ("RE J1034+396", 158.60500, 39.40167, "known X-ray QPO ~3800s"),
    ("3C 273", 187.27800, 2.05200, "bright quasar"),
    ("Mrk 421", 166.11400, 38.20800, "bright blazar"),
    ("PKS 2155-304", 329.71667, -30.22500, "TeV blazar"),
    ("1ES 1959+650", 299.99900, 65.14800, "our marginal ZTF source"),
]

TESS_BASE = "https://mast.stsci.edu/tesscut/api/v0.1/"


def get_sectors(ra, dec):
    """Get TESS sectors covering this position."""
    url = "{}sector?ra={}&dec={}".format(TESS_BASE, ra, dec)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode()
            data = json.loads(text)
            return data.get("results", [])
    except Exception as e:
        print("  sector query FAIL:", e)
        return []


def download_lc(ra, dec, sector, output_dir="data/tess_lc"):
    """Download TESS light curve cutout for given sector."""
    os.makedirs(output_dir, exist_ok=True)
    fname = "s{:04d}_ra{:.2f}_dec{:.1f}.fits".format(int(sector), ra, dec)
    fpath = os.path.join(output_dir, fname)
    
    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
        print("  [CACHED] {}".format(fpath))
        return fpath
    
    url = "{}astrocut?ra={}&dec={}&radius=0.01&sector={}&product=lc".format(
        TESS_BASE, ra, dec, sector)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
            with open(fpath, "wb") as f:
                f.write(body)
            print("  Downloaded: {} ({} bytes)".format(fpath, len(body)))
            return fpath
    except Exception as e:
        print("  download FAIL sector {}: {}".format(sector, e))
        return None


# Check which targets have TESS coverage
print("=" * 60)
print("  TESS AGN QPO — Sector Coverage")
print("=" * 60)

for name, ra, dec, note in AGN_TARGETS:
    print("\n  {} ({:.2f}, {:.1f}) — {}".format(name, ra, dec, note))
    sectors = get_sectors(ra, dec)
    if sectors:
        s_names = list(set(s["sector"] for s in sectors))
        s_names.sort()
        print("  Sectors: {}".format(", ".join(s_names)))
        print("  ({})".format(len(sectors), "observation windows"))
    else:
        print("  No TESS coverage")
