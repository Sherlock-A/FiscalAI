"""
OSM building footprint ingestion for a given commune bounding box.

Uses the Overpass API (free, no key needed) to download all building
footprints in a commune's territory. This is the Day 1 data source
before the commune provides its own cadastre shapefile.
"""

import asyncio
import logging
from typing import Any

import geopandas as gpd
import httpx
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, shape

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OVERPASS_TIMEOUT = 120  # seconds


def build_overpass_query(bbox: tuple[float, float, float, float]) -> str:
    """
    Build an Overpass QL query for all buildings within a bounding box.
    bbox = (south, west, north, east) in WGS84.
    """
    south, west, north, east = bbox
    return f"""
[out:json][timeout:{OVERPASS_TIMEOUT}];
(
  way["building"]({south},{west},{north},{east});
  relation["building"]({south},{west},{north},{east});
);
out geom;
"""


async def fetch_buildings_from_osm(
    bbox: tuple[float, float, float, float],
    commune_name: str = "unknown",
) -> gpd.GeoDataFrame:
    """
    Fetch all building footprints from OSM for the given bounding box.

    Returns a GeoDataFrame with columns:
      osm_id, address_raw, area_m2, geometry (Polygon/EPSG:4326)
    """
    query = build_overpass_query(bbox)
    logger.info(f"Fetching OSM buildings for {commune_name} bbox={bbox}")

    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT + 10) as client:
        response = await client.post(
            settings.osm_overpass_url,
            data={"data": query},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()

    elements = data.get("elements", [])
    logger.info(f"OSM returned {len(elements)} elements for {commune_name}")

    rows = []
    for element in elements:
        geom = _parse_osm_geometry(element)
        if geom is None:
            continue

        tags = element.get("tags", {})
        address_raw = _extract_address(tags)
        area_m2 = _compute_area_m2(geom)

        rows.append({
            "external_id": f"osm_{element['type']}_{element['id']}",
            "source": "osm",
            "address_raw": address_raw,
            "area_m2": area_m2,
            "floor_count": _parse_int(tags.get("building:levels")),
            "osm_tags": tags,
            "geometry": geom,
        })

    if not rows:
        logger.warning(f"No buildings found in OSM for {commune_name}")
        return gpd.GeoDataFrame(columns=["external_id", "source", "address_raw", "area_m2", "geometry"])

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    logger.info(f"Parsed {len(gdf)} building footprints for {commune_name}")
    return gdf


def _parse_osm_geometry(element: dict[str, Any]) -> Polygon | None:
    """Convert an OSM way/relation element to a Shapely Polygon."""
    try:
        if element["type"] == "way":
            nodes = element.get("geometry", [])
            if len(nodes) < 3:
                return None
            coords = [(n["lon"], n["lat"]) for n in nodes]
            return Polygon(coords)
        elif element["type"] == "relation":
            members = element.get("members", [])
            outer_rings = []
            for member in members:
                if member.get("role") == "outer" and member.get("type") == "way":
                    coords = [(n["lon"], n["lat"]) for n in member.get("geometry", [])]
                    if len(coords) >= 3:
                        outer_rings.append(Polygon(coords))
            if not outer_rings:
                return None
            if len(outer_rings) == 1:
                return outer_rings[0]
            return MultiPolygon(outer_rings)
    except Exception as e:
        logger.debug(f"Failed to parse OSM geometry: {e}")
    return None


def _extract_address(tags: dict[str, str]) -> str | None:
    """Extract a human-readable address from OSM tags."""
    parts = []
    if tags.get("addr:housenumber"):
        parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
    elif tags.get("addr:place"):
        parts.append(tags["addr:place"])
    if tags.get("addr:suburb"):
        parts.append(tags["addr:suburb"])
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    return ", ".join(parts) if parts else tags.get("name") or tags.get("addr:full")


def _compute_area_m2(geom: Polygon | MultiPolygon) -> float | None:
    """
    Compute area in m² using UTM zone 29N (appropriate for Morocco).
    Returns None if geometry is invalid.
    """
    try:
        gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
        gdf_utm = gdf.to_crs("EPSG:32629")  # UTM zone 29N
        return round(float(gdf_utm.iloc[0].geometry.area), 2)
    except Exception:
        return None


def _parse_int(value: Any) -> int | None:
    try:
        return int(str(value).split(";")[0].strip())
    except (TypeError, ValueError):
        return None


# Convenience bounding boxes for Moroccan pilot communes
COMMUNE_BBOXES: dict[str, tuple[float, float, float, float]] = {
    "sale":        (34.010, -6.840, 34.110, -6.720),
    "temara":      (33.880, -6.960, 33.960, -6.850),
    "kenitra":     (34.190, -6.680, 34.320, -6.560),
    "mohammedia":  (33.660, -7.420, 33.740, -7.300),
    "ben_guerir":  (32.060, -7.970, 32.120, -7.900),
    "casablanca":  (33.480, -7.730, 33.680, -7.480),
}
