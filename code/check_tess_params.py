"""Find correct TessCut API parameters for TESS light curves."""
import urllib.request

ra, dec = 291.92708, 65.62778

# Try different product values
products = ["sap", "psf", "ffi", "tp", "dvt", "spoc"]
for prod in products:
    url = "https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={}&dec={}&x=30&y=30&sector=0015&product={}".format(ra, dec, prod)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            print("OK product={}: {} bytes".format(prod, len(body)))
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if "enum" in err:
            print("product={}: 422 enum. Error: {}".format(prod, err[:200]))
        else:
            print("product={}: 422 {}".format(prod, err[:150]))
    except Exception as e:
        print("product={}: ERROR {}".format(prod, str(e)[:100]))

# Try without product
url2 = "https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={}&dec={}&x=30&y=30&sector=0015".format(ra, dec)
try:
    req = urllib.request.Request(url2)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
        print("OK no_product: {} bytes".format(len(body)))
except Exception as e:
    print("no_product: {}".format(str(e)[:200]))
