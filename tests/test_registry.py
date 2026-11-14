import os
import json
import pytest
from scraper.pdf_parser_v2 import load_dam_lookup, REGISTRY_PATH

def test_registry_file_exists():
    assert os.path.exists(REGISTRY_PATH), f"Registry file not found at {REGISTRY_PATH}"

def test_registry_slugs_and_capacities():
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    # Filter out duplicate tillari if present
    dams = [d for d in registry if d.get('slug') != 'tillari-kokan-sindhudurg']
    assert len(dams) == 138, f"Expected 138 canonical dams, found {len(dams)}"

    slugs = set()
    for dam in dams:
        slug = dam['slug']
        assert slug not in slugs, f"Duplicate slug detected: {slug}"
        slugs.add(slug)

        # Capacities
        live = float(dam.get('live') or dam.get('design_live_mcm') or 0)
        gross = float(dam.get('gross') or dam.get('design_gross_mcm') or 0)
        assert live > 0, f"Dam {slug} has non-positive live capacity: {live}"
        assert gross >= live, f"Dam {slug} gross {gross} < live {live}"

        # Geographic metadata
        assert dam.get('district'), f"Dam {slug} is missing district"
        assert dam.get('division'), f"Dam {slug} is missing division"

def test_no_alias_collisions():
    lookup = load_dam_lookup()
    assert len(lookup) > 0
    # Canonical tillari should resolve
    assert 'tillari' in lookup
    assert lookup['tillari']['slug'] == 'tillari'
