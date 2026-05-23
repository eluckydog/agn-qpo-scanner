"""TESS AGN search using TessCut API."""
import urllib.request, json

# Try TessCut API directly
# 1ES 1927+654 = RA 291.92708, DEC 65.62778
ra, dec = 291.92708, 65.62778

urls = [
    "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.request.quote(
        '{"service":"Mast.Tess.Coords","params":{"ra":' + str(ra) + ',"dec":' + str(dec) + ',"radius":0.01},"format":"json"}'
    ),
    "https://exo.mast.stsci.edu/api/v0.1/ExoTap/query?query=SELECT+TOP+5+*+FROM+tic_v8+WHERE+ra+" + str(ra-0.5)[:8] + "+AND+ra+" + str(ra+0.5)[:8],
    "https://mast.stsci.edu/tesscut/api/v0.1/sector?ra=" + str(ra) + "&dec=" + str(dec),
]

for url in urls:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            print("URL:", url[:80])
            print("  Status:", resp.status, "Size:", len(text))
            print("  ", text[:300])
            print()
    except Exception as e:
        print("FAIL:", url[:80])
        print("  ", e)
        print()
