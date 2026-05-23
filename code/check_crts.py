"""Deep dive: check CRTS data access for 1ES 1959+650."""
import urllib.request, sys, os

urls = [
    "https://crts.caltech.edu/cgi-bin/lightcurve?name=1ES+1959%2B650",
    "https://crts.caltech.edu/cgi-bin/lightcurve?ra=299.999&dec=65.148",
    "http://nun.caltech.edu/cgi-bin/getlightcurves.cgi?ra=299.999&dec=65.148&name=1ES_1959",
    "https://irsa.ipac.caltech.edu/cgi-bin/CatSummary/nph-summary?name=1ES+1959%2B650",
    "https://irsa.ipac.caltech.edu/TAP/sync?query=SELECT+TOP+5+*+FROM+crts_objects+WHERE+ra>299+AND+ra<300+AND+dec>65+AND+dec<66&format=VOTable",
]

for url in urls:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            text = body.decode("utf-8", errors="replace")
            print("URL:", url)
            print("  Status:", resp.status, "CT:", resp.headers.get("Content-Type", "?"))
            print("  Size:", len(body), "bytes")
            print("  Preview:", text[:300])
            print()
    except Exception as e:
        print("FAIL:", url)
        print("  ", e)
        print()
