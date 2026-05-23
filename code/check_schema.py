"""Quick ZTF TAP schema check"""
import urllib.request
import re

# Get full column list for ztf_objects_dr24
url = "https://irsa.ipac.caltech.edu/TAP/sync?query=SELECT+*+FROM+ztf_objects_dr24+WHERE+oid%3C0&format=VOTable"
req = urllib.request.Request(url=url)
with urllib.request.urlopen(req, timeout=30) as resp:
    body = resp.read().decode("utf-8")

fields = re.findall(r'<FIELD.*?name="([A-Za-z0-9_]+)".*?>', body)
print("Columns:", fields)
print()

# Test actual query - get some real data
q2 = "SELECT+TOP+5+oid,ra,dec+FROM+ztf_objects_dr24+WHERE+dec>0"
url2 = "https://irsa.ipac.caltech.edu/TAP/sync?query={}&format=VOTable".format(q2)
req2 = urllib.request.Request(url=url2)
with urllib.request.urlopen(req2, timeout=30) as resp:
    body2 = resp.read().decode("utf-8")
    td_start = body2.find("<TD>")
    if td_start > 0:
        print("Has TD elements, likely has data")
        print(body2[td_start : td_start + 300])
    else:
        print("Response (first 500):")
        print(body2[:500])
