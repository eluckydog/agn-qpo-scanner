"""
AGN QPO candidate list — sources with reported optical quasi-periodicity,
searchable via ZTF IRSA TAP.

Each candidate: name, ra, dec, z, reported_period_days, ztf_query_id
"""
# Known optical QPO candidates from literature
CANDIDATES = [
    {
        "name": "PG 1302-102",
        "ra": 196.2507,
        "dec": -10.4950,
        "z": 0.278,
        "period_days": 1884,
        "mag": 15.0,
        "type": "Quasar",
        "notes": "Optical periodicity from CRTS, ~5.2yr. Candidate SMBHB.",
        "ztf_query": None,  # Will use name
    },
    {
        "name": "PSO J334.2028+01.4075",
        "ra": 334.2028,
        "dec": 1.4075,
        "z": 2.06,
        "period_days": 542,
        "mag": 18.5,
        "type": "Quasar",
        "notes": "Periodic quasar from Pan-STARRS. SMBHB candidate.",
        "ztf_query": None,
    },
    {
        "name": "OJ 287",
        "ra": 133.059,
        "dec": 15.823,
        "z": 0.306,
        "period_days": 4380,  # ~12 years
        "mag": 14.5,
        "type": "Blazar",
        "notes": "Classic SMBHB candidate. ~12yr optical period.",
        "ztf_query": None,
    },
    {
        "name": "BL Lac",
        "ra": 330.680,
        "dec": 42.278,
        "z": 0.069,
        "period_days": 0,  # known to have QPOs at various timescales
        "mag": 14.5,
        "type": "Blazar",
        "notes": "Prototype blazar. Known micro-variability + QPO epochs.",
        "ztf_query": None,
    },
    {
        "name": "3C 273",
        "ra": 187.278,
        "dec": 2.052,
        "z": 0.158,
        "period_days": 0,
        "mag": 12.9,
        "type": "Quasar",
        "notes": "Brightest quasar. Known ~16yr optical period.",
        "ztf_query": None,
    },
    {
        "name": "Mrk 421",
        "ra": 166.114,
        "dec": 38.208,
        "z": 0.030,
        "period_days": 0,
        "mag": 12.9,
        "type": "Blazar",
        "notes": "TeV blazar. Known X-ray QPOs, optical QPO candidate.",
        "ztf_query": None,
    },
    {
        "name": "1ES 1959+650",
        "ra": 299.999,
        "dec": 65.148,
        "z": 0.047,
        "period_days": 0,
        "mag": 14.2,
        "type": "Blazar",
        "notes": "TeV blazar. Possible QPO at ~220d.",
        "ztf_query": None,
    },
    {
        "name": "M81* Optical",
        "ra": 148.888,
        "dec": 69.065,
        "z": 0.0007,
        "period_days": 237,
        "mag": 14.0,
        "type": "AGN",
        "notes": "Nearby AGN. Known optical quasi-periodicity.",
        "ztf_query": None,
    },
]


def get_candidate_names():
    return [c["name"] for c in CANDIDATES]


def get_candidate_by_name(name):
    for c in CANDIDATES:
        if c["name"].lower() == name.lower():
            return c
    return None


def get_target_list():
    """Return list of (ra, dec, ztf_id) tuples for ZTF queries."""
    targets = []
    for c in CANDIDATES:
        # Use name for ZTF search (some have dedicated ZTF IDs)
        targets.append((c["ra"], c["dec"], c["name"]))
    return targets
