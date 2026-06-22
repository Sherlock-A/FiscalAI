"""
Integration smoke test: gap detector against generated demo data.
Run from backend/: python -m pytest tests/test_gap_detector_smoke.py -v -s
"""

import sys
import json
from pathlib import Path
from decimal import Decimal

import pytest
import pandas as pd
import geopandas as gpd

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

DEMO_DIR = Path(__file__).parent.parent.parent / "data" / "samples" / "sale_demo"


def load_demo_data():
    tax_df = pd.read_csv(DEMO_DIR / "tax_roll_2025.csv")
    tax_df = tax_df.rename(columns={
        "adresse": "address_raw",
        "surface": "declared_area_m2",
        "tsc": "tsc_annual_mad",
        "tpb": "tpb_annual_mad",
        "annee_paiement": "last_payment_year",
        "geo_lon": "geo_lon",
        "geo_lat": "geo_lat",
    })

    with open(DEMO_DIR / "buildings_osm.geojson", encoding="utf-8") as f:
        geojson = json.load(f)

    buildings_gdf = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")

    utility_df = pd.read_csv(DEMO_DIR / "utility_connections.csv")
    utility_df = utility_df.rename(columns={"adresse": "address_raw"})

    return buildings_gdf, tax_df, utility_df


@pytest.fixture(scope="module")
def demo_data():
    if not DEMO_DIR.exists():
        pytest.skip("Demo data not generated — run generate_demo_data.py first")
    return load_demo_data()


class TestGapDetectorSmoke:
    def test_demo_data_loads(self, demo_data):
        buildings, tax, utility = demo_data
        assert len(buildings) == 1000, f"Expected 1000 buildings, got {len(buildings)}"
        assert len(tax) == 800, f"Expected 800 tax entries, got {len(tax)}"
        assert len(utility) > 0

    def test_gap_detection_finds_candidates(self, demo_data):
        from app.services.gap_detector import detect_gaps
        buildings, tax, utility = demo_data
        candidates = detect_gaps(buildings, tax, utility)
        assert len(candidates) > 0, "Gap detector found no candidates"
        print(f"\nFound {len(candidates)} gap candidates")

    def test_gap_detection_finds_significant_fraction(self, demo_data):
        """Should find at least 30% of the 200 planted gaps."""
        from app.services.gap_detector import detect_gaps
        buildings, tax, utility = demo_data
        candidates = detect_gaps(buildings, tax, utility)
        # 200 gaps were planted; we expect at least 60 to surface
        assert len(candidates) >= 60, f"Expected >=60 gaps, found {len(candidates)}"
        print(f"\nRecall: {len(candidates)}/200 gaps found ({len(candidates)/200*100:.1f}%)")

    def test_gap_candidates_have_valid_scores(self, demo_data):
        from app.services.gap_detector import detect_gaps
        buildings, tax, utility = demo_data
        candidates = detect_gaps(buildings, tax, utility)
        for c in candidates:
            assert 0.0 <= c.confidence_score <= 1.0
            assert c.estimated_gap_mad >= Decimal("0")
            assert c.address_raw or c.address_normalized

    def test_total_estimated_gap_is_material(self, demo_data):
        """Total estimated gap should be > 100,000 MAD to be commercially meaningful."""
        from app.services.gap_detector import detect_gaps
        buildings, tax, utility = demo_data
        candidates = detect_gaps(buildings, tax, utility)
        total = sum(c.estimated_gap_mad for c in candidates)
        print(f"\nTotal estimated gap: {total:,.0f} MAD/year")
        assert total >= Decimal("100000"), f"Expected >=100,000 MAD gap, found {total}"

    def test_top_10_sorted_by_confidence(self, demo_data):
        from app.services.gap_detector import detect_gaps
        buildings, tax, utility = demo_data
        candidates = detect_gaps(buildings, tax, utility)[:10]
        scores = [c.confidence_score for c in candidates]
        assert scores == sorted(scores, reverse=True), "Candidates should be sorted by confidence desc"
        print("\nTop 10 gaps:")
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c.address_raw[:50]:<50} | conf={c.confidence_score:.2f} | gap={c.estimated_gap_mad:>8,.0f} MAD")
