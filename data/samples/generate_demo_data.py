"""
Generates realistic synthetic demo data for the FiscalAI pilot demo.

Simulates a Moroccan commune's tax roll with realistic address formats,
some deliberate "gaps" (properties with utility connections but no tax records),
and building footprint data with varying declaration accuracy.

Usage:
  python generate_demo_data.py --commune sale --output ./sale_demo/
"""

import argparse
import json
import random
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, Polygon, mapping
import geopandas as gpd

# Salé commune approximate bounds (WGS84)
SALE_BOUNDS = {"min_lon": -6.835, "max_lon": -6.720, "min_lat": 34.010, "max_lat": 34.110}

# Real Moroccan neighborhood names used in Salé (expanded for geographic diversity)
SALE_NEIGHBORHOODS = [
    "Hay Salam", "Hay Karima", "Hay El Qods", "Hay Inara", "Hay Essalam",
    "Douar Lhajja", "Lotissement Al Amal", "Cité Bouarfa", "Quartier Hassan",
    "Hay Bettana", "Résidence Moulay Ismail", "Hay Arrahma", "Cité OCP",
    "Hay Nahda", "Tabriquet", "Layayda", "Bab Lamrissa", "Hay Rahma",
    "Quartier Industriel", "Hay Al Matar", "Cité Ennasr",
]

# TSC rates (MAD/m²) by neighborhood zone: downtown 25, residential 14, peripheral 7
NEIGHBORHOOD_TSC_RATE: dict[str, float] = {
    "Bab Lamrissa": 25.0, "Quartier Hassan": 25.0, "Tabriquet": 25.0,
    "Hay Salam": 14.0, "Hay Karima": 14.0, "Hay El Qods": 14.0, "Hay Inara": 14.0,
    "Hay Essalam": 14.0, "Hay Bettana": 14.0, "Hay Nahda": 14.0, "Hay Arrahma": 14.0,
    "Lotissement Al Amal": 14.0, "Cité Bouarfa": 14.0, "Résidence Moulay Ismail": 14.0,
    "Hay Rahma": 14.0, "Hay Al Matar": 14.0, "Cité Ennasr": 14.0,
    "Douar Lhajja": 7.0, "Cité OCP": 7.0, "Layayda": 7.0, "Quartier Industriel": 7.0,
}

def _tsc_rate(neighborhood: str) -> float:
    return NEIGHBORHOOD_TSC_RATE.get(neighborhood, 14.0)

# Street name patterns
STREET_PATTERNS = [
    "Rue {n}", "Avenue {n}", "Boulevard {n}", "Lotissement {n} Lot {k}",
    "Rue des {n}", "Impasse {n}", "Résidence {n} Apt {k}",
]

STREET_NAMES = [
    "Hassan II", "Mohammed V", "Al Qods", "Al Massira", "Bir Anzarane",
    "Oued Tensift", "Al Aaraich", "Ibn Batouta", "Al Fida", "Tarik",
    "Lalla Yacout", "Al Wahda", "Al Massira Al Khadra", "Allal Ben Abdellah",
]


def random_address(rng: random.Random, neighborhood: str | None = None) -> tuple[str, str]:
    if neighborhood is None:
        neighborhood = rng.choice(SALE_NEIGHBORHOODS)
    k = rng.randint(1, 200)
    pattern = rng.choice(STREET_PATTERNS)
    street = pattern.format(n=rng.choice(STREET_NAMES), k=k)
    return f"{k}, {street}, {neighborhood}, Salé", neighborhood


def random_point(rng: random.Random, bounds: dict) -> tuple[float, float]:
    lon = rng.uniform(bounds["min_lon"], bounds["max_lon"])
    lat = rng.uniform(bounds["min_lat"], bounds["max_lat"])
    return lon, lat


def random_building_polygon(center_lon: float, center_lat: float, area_m2: float) -> Polygon:
    """Approximate rectangular footprint centered at point."""
    side = (area_m2 ** 0.5) / 111_000  # degrees approximation
    return Polygon([
        (center_lon - side, center_lat - side),
        (center_lon + side, center_lat - side),
        (center_lon + side, center_lat + side),
        (center_lon - side, center_lat + side),
    ])


def generate_demo(commune: str, output_dir: str, seed: int = 42):
    rng = random.Random(seed)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    bounds = SALE_BOUNDS  # extend for other communes later
    n_declared = 800
    n_gaps = 200           # the "finds" we want FiscalAI to surface
    n_utilities = 950

    # ── Tax roll (declared properties) ────────────────────────────────────────
    declared_rows = []
    declared_coords = []
    for i in range(n_declared):
        lon, lat = random_point(rng, bounds)
        declared_coords.append((lon, lat))
        area = rng.uniform(60, 400)
        address, neighborhood = random_address(rng)
        rate = _tsc_rate(neighborhood)
        tsc = round(area * rate, 2)
        declared_rows.append({
            "redevable_id": f"SIT-{1000+i:05d}",
            "adresse": address,
            "surface": round(area, 1),
            "tsc": tsc,
            "tpb": round(tsc * 0.4, 2),
            "annee_paiement": rng.choice([2022, 2023, 2024, 2024, 2024, 2025]),
            "geo_lon": lon,
            "geo_lat": lat,
        })

    tax_df = pd.DataFrame(declared_rows)
    tax_df.to_csv(output / "tax_roll_2025.csv", index=False)
    print(f"Generated {len(tax_df)} tax roll entries -> {output}/tax_roll_2025.csv")

    # ── GAP buildings (exist but NOT in tax roll) ──────────────────────────────
    gap_rows = []
    gap_buildings = []
    for i in range(n_gaps):
        lon, lat = random_point(rng, bounds)
        area = rng.uniform(80, 350)
        address, neighborhood = random_address(rng)
        rate = _tsc_rate(neighborhood)
        gap_rows.append({
            "osm_id": f"osm_way_{9000000+i}",
            "address_raw": address,
            "area_m2": round(area, 1),
            "in_tax_roll": False,   # deliberately excluded
            "construction_year": rng.randint(1990, 2023),  # wider spread → more backlog years
            "geometry": mapping(random_building_polygon(lon, lat, area)),
        })
        gap_buildings.append({"lon": lon, "lat": lat, "address": address, "area_m2": area, "tsc_rate": rate})

    # ── All OSM buildings (declared + gaps combined) ───────────────────────────
    all_buildings = []
    for i, (row, (lon, lat)) in enumerate(zip(declared_rows, declared_coords)):
        area = row["surface"]
        # Some declared properties have larger actual footprint (underdeclaration)
        actual_area = area * rng.uniform(0.95, 1.60)
        all_buildings.append({
            "external_id": f"osm_way_{i+1}",
            "source": "osm",
            "address_raw": row["adresse"],
            "area_m2": round(actual_area, 1),
            "geometry": mapping(random_building_polygon(lon, lat, actual_area)),
        })
    for row in gap_rows:
        all_buildings.append({
            "external_id": row["osm_id"],
            "source": "osm",
            "address_raw": row["address_raw"],
            "area_m2": row["area_m2"],
            "geometry": row["geometry"],
        })

    with open(output / "buildings_osm.geojson", "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {k: v for k, v in b.items() if k != "geometry"},
                    "geometry": b["geometry"],
                }
                for b in all_buildings
            ],
        }, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(all_buildings)} building footprints -> {output}/buildings_osm.geojson")

    # ── Utility connections (ONEE hookups) ─────────────────────────────────────
    utility_rows = []
    # Hookups for declared properties
    for row, (lon, lat) in zip(declared_rows, declared_coords):
        if rng.random() < 0.92:  # 92% have electricity
            utility_rows.append({
                "utility_type": "electricity",
                "adresse": row["adresse"],
                "meter_id": f"ONEE-{rng.randint(100000, 999999)}",
                "connection_date": f"20{rng.randint(10,24):02d}-{rng.randint(1,12):02d}-01",
                "geo_lon": lon + rng.uniform(-0.0002, 0.0002),
                "geo_lat": lat + rng.uniform(-0.0002, 0.0002),
            })
    # Hookups for GAP properties (key signal: electricity without tax declaration)
    for row in gap_buildings:
        if rng.random() < 0.78:  # 78% of gaps have electricity
            utility_rows.append({
                "utility_type": "electricity",
                "adresse": row["address"],
                "meter_id": f"ONEE-{rng.randint(100000, 999999)}",
                "connection_date": f"20{rng.randint(18,25):02d}-{rng.randint(1,12):02d}-01",
                "geo_lon": row["lon"] + rng.uniform(-0.0002, 0.0002),
                "geo_lat": row["lat"] + rng.uniform(-0.0002, 0.0002),
            })

    utility_df = pd.DataFrame(utility_rows)
    utility_df.to_csv(output / "utility_connections.csv", index=False)
    print(f"Generated {len(utility_df)} utility connections -> {output}/utility_connections.csv")

    # ── Summary ────────────────────────────────────────────────────────────────
    expected_gap_mad = sum(
        row["area_m2"] * row["tsc_rate"]
        for row in gap_buildings
    )
    print(f"\nDemo data summary for Salé pilot:")
    print(f"  Declared properties:    {n_declared}")
    print(f"  Gap buildings (hidden): {n_gaps}")
    print(f"  Utility connections:    {len(utility_df)}")
    print(f"  Expected gap (if found): {expected_gap_mad:,.0f} MAD/year")
    print(f"\nFiscalAI should find approximately {n_gaps} gaps worth {expected_gap_mad:,.0f} MAD/year.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commune", default="sale")
    parser.add_argument("--output", default="./sale_demo")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate_demo(args.commune, args.output, args.seed)
