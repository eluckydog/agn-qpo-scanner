"""Check ASAS-SN data access for 1ES 1959+650."""
import urllib.request

urls = [
    "https://asas-sn.osu.edu/api/v1/sources/299.999+65.148/lightcurve",
    "https://asas-sn.osu.edu/api/v1/sources/299.999,65.148",
    "https://asas-sn.osu.edu/skyviewer/api/sources?ra=299.999&dec=65.148&radius=0.02",
]

for url in urls:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            print("OK:", url)
            print("  CT:", resp.headers.get("Content-Type"), "size:", len(body))
            print("  ", body[:400].decode("utf-8", errors="replace"))
            print()
    except Exception as e:
        print("FAIL:", url, "->", e)
        print()
