"""
ZTF light curve download via IRSA TAP (v2 — fixes schema issues).

Usage:
    python query_ztf.py test          # quick connectivity check
    python query_ztf.py all            # fetch all candidates
    python query_ztf.py PG_1302-102    # fetch specific source
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
LC_URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "lc")


def votable_to_json(votable_xml):
    """VOTable → JSON parser (namespace-aware)."""
    import xml.etree.ElementTree as ET
    
    # Strip namespace to simplify parsing
    votable_xml = votable_xml.replace('xmlns=', 'ns=')  # disable default ns
    # Also replace any xmlns attributes
    import re
    votable_xml = re.sub(r'xmlns:stc="[^"]*"', '', votable_xml)
    votable_xml = re.sub(r'xmlns:xsi="[^"]*"', '', votable_xml)
    votable_xml = re.sub(r'xsi:schemaLocation="[^"]*"', '', votable_xml)
    
    root = ET.fromstring(votable_xml)

    # Check for errors
    info = root.findall('.//INFO')
    for i in info:
        if i.get('name') == 'QUERY_STATUS' and i.get('value') == 'ERROR':
            print(f"  [TAP ERROR] {i.text}")
            return None

    # Get field names
    table = root.find('.//TABLE')
    if table is None:
        return None

    fields = []
    for field in table.findall('FIELD'):
        fields.append(field.get('name'))

    # Get data rows
    data = []
    for tr in table.findall('.//TR'):
        row = []
        for td in tr.findall('TD'):
            row.append(td.text)
        data.append(row)

    return {"fields": fields, "data": data}


def _tap_query(query, timeout=30):
    """Execute TAP query, parse VOTable result."""
    url = f"{BASE_URL}?query={urllib.parse.quote(query)}&format=VOTable"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
        result = votable_to_json(text)
        return result
    except urllib.error.URLError as e:
        print(f"  [NETWORK] ZTF unreachable: {e}")
        return None


def search_by_coords(ra, dec, radius_deg=0.02, dr="dr24", timeout=30):
    """Search ZTF for bright objects near given coordinates."""
    table = f"ztf_objects_{dr}"
    query = (
        f"SELECT oid, ra, dec, meanmag, ngoodobs, filtercode "
        f"FROM {table} "
        f"WHERE CONTAINS(POINT('ICRS', ra, dec), "
        f"CIRCLE('ICRS', {ra}, {dec}, {radius_deg})) = 1 "
        f"AND ngoodobs > 20 "
        f"AND meanmag < 20 "
        f"ORDER BY ngoodobs DESC"
    )
    return _tap_query(query, timeout)


def get_light_curve(oid, dr="dr24", timeout=60):
    """Fetch light curve for a ZTF object via the dedicated LC service."""
    # The LC service returns a CSV-like response
    url = f"{LC_URL}?collection=ztf_{dr}&ID={oid}&format=csv"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
        return text
    except urllib.error.URLError as e:
        print(f"  [LC ERROR] oid={oid}: {e}")
        return None


def fetch_lc_by_coords(ra, dec, label, dr="dr24", output_dir=None):
    """
    Fetch light curve by coordinates (try DR24-21, pick best).
    Returns path to CSV file.
    """
    if output_dir is None:
        output_dir = DATA_DIR
    os.makedirs(output_dir, exist_ok=True)

    safe_name = label.replace(" ", "_").replace("*", "star").replace("+", "p").replace("-", "m")
    csv_path = os.path.join(output_dir, f"{safe_name}.csv")

    # Cache hit
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 200:
        print(f"  [CACHED] {csv_path}")
        return csv_path

    print(f"  Searching ZTF {dr} near ({ra:.4f}, {dec:.4f})...")

    # Try current DR, fall back to older
    for try_dr in [dr, "dr23", "dr22", "dr21"]:
        result = search_by_coords(ra, dec, dr=try_dr)
        if result and result["data"]:
            dr = try_dr
            break
    else:
        print(f"  [NOT FOUND] No ZTF objects near ({ra}, {dec})")
        return None

    if not result or not result["data"]:
        return None

    # Pick the object with most observations (best light curve)
    rows = result["data"]
    # rows: [oid, ra, dec, meanmag, ngoodobs, filtercode]
    best = max(rows, key=lambda r: int(r[4]) if r[4] else 0)
    oid = best[0]
    ra_found = best[1]
    dec_found = best[2]
    mag = best[3]
    nobs = best[4]

    print(f"  Best match: oid={oid} at ({ra_found}, {dec_found}), mag={mag}, {nobs} obs")

    # Fetch light curve CSV
    print(f"  Fetching light curve...")
    lc_text = get_light_curve(oid, dr=dr)
    if not lc_text:
        print(f"  [NO LC DATA] for oid={oid}")
        return None

    # Write raw LC data
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(lc_text)

    # Count lines
    n_lines = len(lc_text.strip().split("\n"))
    print(f"  Saved {n_lines} rows to {csv_path}")
    return csv_path


def fetch_known_candidates():
    """Fetch all known AGN QPO candidates."""
    # Import here to avoid circular issues
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from candidates import CANDIDATES

    for c in CANDIDATES:
        print(f"\n--- {c['name']} ---")
        try:
            fetch_lc_by_coords(c["ra"], c["dec"], c["name"])
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(2)  # be polite


if __name__ == "__main__":
    import urllib.parse as _  # ensure imported for function calls

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Quick connectivity check
        print("Testing ZTF connectivity...")
        r = search_by_coords(196.25, -10.495, radius_deg=0.05)
        if r and r["data"]:
            print(f"OK: found {len(r['data'])} objects near PG 1302-102")
        else:
            print("FAILED")
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        fetch_known_candidates()
    else:
        print(__doc__)
