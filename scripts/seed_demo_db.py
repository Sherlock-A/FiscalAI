"""
Seed the development database with FiscalAI demo data.

Run after TRUNCATE to regenerate all detections:
  psql ... -c "TRUNCATE TABLE gap_detections RESTART IDENTITY CASCADE;"
  python scripts/seed_demo_db.py

Environment variables (set automatically by docker-compose):
  DATABASE_URL   — postgres connection string
  DEMO_DATA_DIR  — path to sale_demo/ directory
  BACKEND_PATH   — path to backend/ directory (for gap_detector import)
"""

import json
import math
import os
import random
import sys
import uuid
from pathlib import Path

import psycopg2.extras
psycopg2.extras.register_uuid()

import geopandas as gpd
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, Json
from shapely.geometry import Polygon

# ── Path resolution — works both inside Docker and locally ─────────────────
ROOT = Path(__file__).parent.parent  # d:\Commune or /

BACKEND_PATH  = os.environ.get("BACKEND_PATH")  or str(ROOT / "backend")
DEMO_DATA_DIR = os.environ.get("DEMO_DATA_DIR") or str(ROOT / "data" / "samples" / "sale_demo")
DATABASE_URL  = os.environ.get(
    "DATABASE_URL",
    "postgresql://fiscalai:fiscalai_dev_secret@localhost:5434/fiscalai",
)

sys.path.insert(0, BACKEND_PATH)

DEMO_DIR = Path(DEMO_DATA_DIR)

# ── Commercial building generation config ──────────────────────────────────
random.seed(42)

COMMERCIAL_COUNT     = 60
COMMERCIAL_LICENSED  = 20   # out of 60 → 40 unlicensed detected by Stage 3

# Salé bounding box (approx)
SALE_LAT_MIN, SALE_LAT_MAX = 34.010, 34.110
SALE_LON_MIN, SALE_LON_MAX = -6.840, -6.720

COMMERCIAL_OSM_TAGS = [
    {"building": "commercial", "shop": "grocery"},
    {"building": "commercial", "shop": "clothing"},
    {"building": "commercial", "office": "yes"},
    {"building": "commercial", "shop": "restaurant"},
    {"building": "commercial", "shop": "pharmacy"},
    {"building": "commercial", "cafe": "yes"},
    {"building": "commercial", "shop": "bakery"},
    {"building": "commercial", "shop": "electronics"},
    {"building": "commercial", "shop": "hardware"},
    {"building": "commercial", "office": "real_estate"},
]

COMMERCIAL_ADDR_TEMPLATES = [
    "Local {n}, Av. Mohammed V, Quartier Hassan, Salé",
    "N° {n}, Rue de Fès, Hay Salam, Salé",
    "Boutique {n}, Souk El Had, Medina, Salé",
    "N° {n}, Boulevard Hassan II, Centre-Ville, Salé",
    "Local Commercial {n}, Hay Arrahma, Salé",
    "Cellule {n}, Résidence Al Fath, Hay Inara, Salé",
    "N° {n}, Rue Al Qods, Hay Essalam, Salé",
    "Commerce {n}, Route de Rabat, Salé",
    "N° {n}, Av. Al Qods, Bettana, Salé",
    "Local {n}, Rue Ibn Sina, Medina, Salé",
]


def _make_building_polygon(center_lon: float, center_lat: float, area_m2: float) -> Polygon:
    side_m = math.sqrt(area_m2)
    dlat = side_m / 111000
    dlon = side_m / (111000 * math.cos(math.radians(center_lat)))
    return Polygon([
        (center_lon - dlon / 2, center_lat - dlat / 2),
        (center_lon + dlon / 2, center_lat - dlat / 2),
        (center_lon + dlon / 2, center_lat + dlat / 2),
        (center_lon - dlon / 2, center_lat + dlat / 2),
    ])


def main():
    print("FiscalAI — Demo Database Seeder")
    print("=" * 50)

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Get Salé commune ID
        cur.execute("SELECT id FROM communes WHERE code_commune = '101040'")
        row = cur.fetchone()
        if not row:
            print("ERROR: Salé commune not found. Is init-db.sql loaded correctly?")
            sys.exit(1)
        commune_id = row[0]

        # Idempotency check — skip if already seeded
        cur.execute("SELECT COUNT(*) FROM gap_detections WHERE commune_id = %s", (commune_id,))
        existing = cur.fetchone()[0]
        if existing > 0:
            print(f"Already seeded ({existing} gap detections found for Salé). Skipping.")
            print("To reseed: TRUNCATE TABLE gap_detections RESTART IDENTITY CASCADE;")
            return

        print(f"Commune Salé: {commune_id}")

        # ── Load demo files ──────────────────────────────────────────────────
        tax_df = pd.read_csv(DEMO_DIR / "tax_roll_2025.csv")
        tax_df = tax_df.rename(columns={
            "adresse":         "address_raw",
            "surface":         "declared_area_m2",
            "tsc":             "tsc_annual_mad",
            "tpb":             "tpb_annual_mad",
            "annee_paiement":  "last_payment_year",
        })

        with open(DEMO_DIR / "buildings_osm.geojson", encoding="utf-8") as f:
            geojson = json.load(f)
        buildings_gdf = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")

        utility_df = pd.read_csv(DEMO_DIR / "utility_connections.csv")
        utility_df = utility_df.rename(columns={"adresse": "address_raw"})

        print(f"Loaded: {len(tax_df)} tax entries, {len(buildings_gdf)} buildings, {len(utility_df)} utilities")

        # ── Augment buildings_gdf with floor_count + construction_year ───────
        # Floor count: weighted 1=55%, 2=30%, 3=12%, 4=3%
        buildings_gdf = buildings_gdf.copy()
        buildings_gdf["floor_count"] = [
            random.choices([1, 2, 3, 4], weights=[55, 30, 12, 3])[0]
            for _ in range(len(buildings_gdf))
        ]
        # Construction years: simulate an older unregistered population
        buildings_gdf["construction_year"] = [
            random.randint(2005, 2022) for _ in range(len(buildings_gdf))
        ]
        # Ensure osm_tags column exists (GeoJSON may not have it)
        if "osm_tags" not in buildings_gdf.columns:
            buildings_gdf["osm_tags"] = None

        # ── Generate commercial buildings ─────────────────────────────────────
        commercial_records = []
        for i in range(COMMERCIAL_COUNT):
            lat  = random.uniform(SALE_LAT_MIN, SALE_LAT_MAX)
            lon  = random.uniform(SALE_LON_MIN, SALE_LON_MAX)
            area = round(random.uniform(60, 200), 1)
            tags = random.choice(COMMERCIAL_OSM_TAGS).copy()
            addr = random.choice(COMMERCIAL_ADDR_TEMPLATES).format(n=100 + i)
            year = random.randint(2010, 2020)
            geom = _make_building_polygon(lon, lat, area)
            commercial_records.append({
                "external_id":       f"osm_commercial_{i + 1}",
                "source":            "osm",
                "address_raw":       addr,
                "area_m2":           area,
                "floor_count":       random.choices([1, 2], weights=[70, 30])[0],
                "construction_year": year,
                "osm_tags":          tags,
                "geometry":          geom,
            })

        commercial_gdf = gpd.GeoDataFrame(commercial_records, crs="EPSG:4326")
        buildings_gdf = pd.concat([buildings_gdf, commercial_gdf], ignore_index=True)
        print(f"Added {COMMERCIAL_COUNT} commercial buildings (total: {len(buildings_gdf)})")

        # ── Fix utility_df: add geo_point_wkt for _has_utility_hookup() ──────
        if "geo_lon" in utility_df.columns and "geo_lat" in utility_df.columns:
            utility_df = utility_df.copy()
            utility_df["geo_point_wkt"] = utility_df.apply(
                lambda r: (
                    f"POINT ({float(r['geo_lon'])} {float(r['geo_lat'])})"
                    if pd.notna(r.get("geo_lon")) and pd.notna(r.get("geo_lat"))
                    else None
                ),
                axis=1,
            )

        # ── Insert buildings ─────────────────────────────────────────────────
        building_rows = []
        for _, b in buildings_gdf.iterrows():
            geom = b.get("geometry")
            geom_wkt = geom.wkt if geom is not None else None
            if not geom_wkt:
                continue
            tags     = b.get("osm_tags")
            tags_val = Json(dict(tags)) if isinstance(tags, dict) else None
            fc  = int(b.get("floor_count") or 1)
            cy_raw = b.get("construction_year")
            cy  = int(cy_raw) if cy_raw and not pd.isna(cy_raw) else None
            building_rows.append((
                uuid.uuid4(),
                commune_id,
                str(b.get("source", "osm")),
                str(b.get("external_id", "")),
                str(b.get("address_raw", "")) or None,
                float(b.get("area_m2") or 0) or None,
                fc,
                cy,
                tags_val,
                geom_wkt,
            ))

        execute_values(cur, """
            INSERT INTO buildings
              (id, commune_id, source, external_id, address_raw, area_m2,
               floor_count, construction_year, osm_tags, footprint)
            VALUES %s ON CONFLICT DO NOTHING
        """, building_rows,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, ST_GeomFromText(%s, 4326))")
        print(f"Inserted {len(building_rows)} buildings")

        # ── Insert tax roll (base + licensed commercial) ──────────────────────
        tax_rows = []
        for _, t in tax_df.iterrows():
            tax_rows.append((
                uuid.uuid4(),
                commune_id,
                str(t.get("redevable_id", "")) or None,
                str(t.get("address_raw", "")),
                float(t.get("declared_area_m2") or 0) or None,
                float(t.get("tsc_annual_mad") or 0) or None,
                float(t.get("tpb_annual_mad") or 0) or None,
                int(t.get("last_payment_year") or 0) or None,
                2025,
            ))

        # Add licensed commercial businesses (first COMMERCIAL_LICENSED records)
        for i in range(COMMERCIAL_LICENSED):
            rec  = commercial_records[i]
            area = rec["area_m2"]
            tax_rows.append((
                uuid.uuid4(),
                commune_id,
                f"COM-{i + 1:04d}",
                rec["address_raw"],
                area,
                round(area * 25.0, 2),  # TSC downtown rate
                round(area * 1.5, 2),   # taxe professionnelle (marks as registered)
                2024,
                2025,
            ))

        execute_values(cur, """
            INSERT INTO tax_roll (id, commune_id, redevable_id, address_raw,
                                  declared_area_m2, tsc_annual_mad, tpb_annual_mad,
                                  last_payment_year, tax_year)
            VALUES %s ON CONFLICT DO NOTHING
        """, tax_rows)
        print(f"Inserted {len(tax_rows)} tax roll entries")

        # ── Insert utility connections ───────────────────────────────────────
        util_rows = []
        for _, u in utility_df.iterrows():
            lon = float(u.get("geo_lon") or 0)
            lat = float(u.get("geo_lat") or 0)
            if not lon or not lat:
                continue
            util_rows.append((
                uuid.uuid4(),
                commune_id,
                str(u.get("utility_type", "electricity")),
                str(u.get("address_raw", "")),
                lon, lat,
            ))

        execute_values(cur, """
            INSERT INTO utility_connections (id, commune_id, utility_type, address_raw, geo_point)
            VALUES %s ON CONFLICT DO NOTHING
        """, util_rows,
        template="(%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))")
        print(f"Inserted {len(util_rows)} utility connections")

        # Build building_id lookup by external_id (needed to link gap_detections → buildings)
        cur.execute("SELECT id, external_id FROM buildings WHERE commune_id = %s", (commune_id,))
        building_id_by_ext = {row[1]: row[0] for row in cur.fetchall()}

        # ── Run gap detector and insert results ──────────────────────────────
        print("\nRunning gap detector...")
        from app.services.gap_detector import detect_gaps

        candidates = detect_gaps(buildings_gdf, tax_df, utility_df, zone_type="urban")
        print(f"Found {len(candidates)} gap candidates")

        gap_rows = []
        for c in candidates:
            gap_type = c.evidence.get("gap_type", "missing_declaration")
            b_uuid   = building_id_by_ext.get(c.building_external_id)
            gap_rows.append((
                uuid.uuid4(),
                commune_id,
                b_uuid,
                c.address_raw or c.address_normalized or "Adresse inconnue",
                gap_type,
                round(float(c.confidence_score), 4),
                round(float(c.estimated_gap_mad), 2),
                Json(c.evidence),
                "new",
            ))

        execute_values(cur, """
            INSERT INTO gap_detections
              (id, commune_id, building_id, address_resolved, gap_type,
               confidence_score, estimated_gap_mad, evidence, status)
            VALUES %s
        """, gap_rows)

        conn.commit()

        total_mad  = sum(r[6] for r in gap_rows)
        total_back = sum(c.evidence.get("estimated_backlog_mad", 0) for c in candidates)
        by_type: dict[str, int] = {}
        for c in candidates:
            t = c.evidence.get("gap_type", "missing_declaration")
            by_type[t] = by_type.get(t, 0) + 1

        print(f"\n{'='*50}")
        print(f"Seed complete!")
        print(f"  Commune:          Salé ({commune_id})")
        print(f"  Gap detections:   {len(gap_rows)}")
        print(f"  Annual revenue:   {total_mad:,.0f} MAD/year")
        print(f"  Total backlog:    {total_back:,.0f} MAD")
        for gap_t, cnt in sorted(by_type.items()):
            print(f"    {gap_t}: {cnt}")
        print(f"\nFrontend: http://localhost:3000")
        print(f"API docs: http://localhost:8000/docs")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
