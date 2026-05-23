"""Find TESS data for AGN via MAST Catalogs API."""
import urllib.request, json

# Check available MAST catalog services
services = ["Mast.Catalogs.TessTic", "Mast.Catalogs.Filtered", "Mast.Catalogs.Tess"]
for svc in services:
    query = json.dumps({
        "service": svc,
        "params": {},
        "format": "json",
    })
    url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.request.quote(query)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode()
            print("{}: {} bytes".format(svc, len(text)))
            print("  {}".format(text[:200]))
    except Exception as e:
        print("{}: FAIL {}".format(svc, e))
