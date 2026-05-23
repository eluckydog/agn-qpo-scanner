"""Probe TESS and Fermi data access for AGN QPO."""
import urllib.request, json

# 1. TESS via MAST TAP
url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.request.quote(
    '{"service":"Mast.Tess.Pipeline","params":{},"format":"json"}'
)
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode()
        print("=== MAST TESS ===")
        print("Status:", resp.status, "Size:", len(text))
        # Just check if it works
        print("OK" if '"status"' in text else "Bad response")
except Exception as e:
    print("MAST FAIL:", e)

# 2. TESS light curve for a known AGN (e.g., 1ES 1927+654)
# Try the MAST TAP query for TESS targets near an AGN
url2 = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.request.quote(
    '{"service":"Mast.Tess.Pipeline","params":{},"format":"json"}'
)
try:
    req = urllib.request.Request(url2)
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode()
        print("\n=== TESS Pipeline Access ===")
        print("OK, pipeline accessible")
except Exception as e:
    print("TESS pipeline FAIL:", e)

# 3. Fermi AGN catalog via HEASARC TAP
# HEASARC TAP endpoint: https://heasarc.gsfc.nasa.gov/TAP/sync
# For Fermi LAT AGN catalog (4LAC)
url3 = "https://heasarc.gsfc.nasa.gov/TAP/sync?query=SELECT+TOP+3+%2A+FROM+fermilat_4lac_dr2+WHERE+DEC_LL>30&format=json"
try:
    req = urllib.request.Request(url3)
    with urllib.request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode()
        print("\n=== Fermi 4LAC ===")
        print("Status:", resp.status, "Size:", len(text))
        print(text[:300])
except Exception as e:
    print("Fermi FAIL:", e)

# 4. TESS sector info
url4 = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.request.quote(
    '{"service":"Mast.Tess.SectorInfo","params":{},"format":"json"}'
)
try:
    req = urllib.request.Request(url4)
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode()
        print("\n=== TESS Sector Info ===")
        print("Status:", resp.status, "Size:", len(text))
        print("OK" if len(text) > 100 else "small: " + text[:200])
except Exception as e:
    print("TESS Sector FAIL:", e)
