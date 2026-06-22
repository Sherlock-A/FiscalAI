"""
Spatial gap detection engine.

Core logic: find buildings (from OSM/cadastre) that have no corresponding
entry in the commune's tax roll, using a three-stage strategy:

  Stage 1: Address matching (normalized string similarity)
  Stage 2: Spatial proximity fallback (PostGIS 50m buffer join)
  Stage 3: Commercial tag detection (unlicensed businesses)

The output is a list of candidate gap detections ranked by confidence_score.
Revenue estimates incorporate floor count, zone-based TSC rates, and
a backlog estimate (annual gap × years unregistered).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from app.services.address_normalizer import address_similarity, normalize_address

logger = logging.getLogger(__name__)

# Matching thresholds
SIMILARITY_THRESHOLD = 0.72
SPATIAL_BUFFER_METERS = 50
MIN_CONFIDENCE_TO_REPORT = 0.40

# Current year for backlog estimation
CURRENT_YEAR = 2025

# Zone-differentiated TSC rates (MAD/m²/year) — Moroccan fiscal zones
ZONE_RATES = {
    "downtown":    25.0,   # Centre-ville, Medina, Hay Salam
    "residential": 14.0,   # Hay Arrahma, Hay Inara, Hay Essalam (default urban)
    "peripheral":   7.0,   # Douar, Route, peri-urban zones
}
DOWNTOWN_KEYWORDS  = {"medina", "hassan", "salam", "centre", "ville", "souk", "fes"}
PERIPHERAL_KEYWORDS = {"douar", "route", "rurale", "peri", "mechkoura", "lot"}
DEFAULT_TSC_RATE_PERI = 6.0

# Commercial building detection (OSM tags)
COMMERCIAL_OSM_KEYS = {"shop", "office", "restaurant", "cafe", "clinic", "pharmacy", "school", "hotel"}
COMMERCIAL_BUILDING_VALUES = {"commercial", "retail", "office", "shop"}


@dataclass
class GapCandidate:
    building_external_id: str
    address_raw: str
    address_normalized: str | None
    area_m2: float | None
    geometry_wkt: str
    match_method: str               # 'address' | 'spatial' | 'unmatched' | 'commercial_tag'
    match_score: float              # 0.0–1.0 similarity
    confidence_score: float         # final model score
    estimated_gap_mad: Decimal
    evidence: dict[str, Any] = field(default_factory=dict)
    floor_count: int = 1


def detect_gaps(
    buildings_gdf: gpd.GeoDataFrame,
    tax_roll_df: pd.DataFrame,
    utility_df: pd.DataFrame | None = None,
    zone_type: str = "urban",
) -> list[GapCandidate]:
    """
    Main gap detection function.

    Args:
        buildings_gdf: GeoDataFrame with columns [external_id, address_raw, area_m2,
                       geometry, floor_count?, construction_year?, osm_tags?]
        tax_roll_df:   DataFrame with columns [address_raw, declared_area_m2, tsc_annual_mad,
                       tpb_annual_mad?]
        utility_df:    Optional DataFrame with geo_point_wkt column for occupancy signal
        zone_type:     'urban' or 'peri'

    Returns:
        List of GapCandidate objects, sorted by confidence_score descending.
    """
    # Normalize all addresses upfront
    buildings_gdf = buildings_gdf.copy()
    buildings_gdf["address_norm"] = buildings_gdf["address_raw"].apply(normalize_address)

    tax_roll_df = tax_roll_df.copy()
    tax_roll_df["address_norm"] = tax_roll_df["address_raw"].apply(normalize_address)

    tax_norm_set = set(tax_roll_df["address_norm"].dropna().tolist())
    tax_gdf = _tax_roll_to_geodataframe(tax_roll_df)

    candidates: list[GapCandidate] = []
    detected_ids: set[str] = set()

    # ── Stage 1 & 2: missing_declaration + underdeclared ──────────────────────
    for _, building in buildings_gdf.iterrows():
        b_norm   = building.get("address_norm")
        b_area   = building.get("area_m2")
        b_geom   = building.get("geometry")
        b_id     = str(building.get("external_id", ""))
        b_floors = int(building.get("floor_count") or 1)
        b_year   = int(building.get("construction_year") or 0)
        tsc_rate = _zone_rate(b_norm, zone_type)
        backlog_years = max(1, CURRENT_YEAR - b_year) if b_year > 2000 else 3

        best_score, best_match = _best_address_match(b_norm, tax_norm_set)

        if best_score >= SIMILARITY_THRESHOLD:
            matched_row = tax_roll_df[tax_roll_df["address_norm"] == best_match]
            if not matched_row.empty:
                declared_area = matched_row.iloc[0].get("declared_area_m2", 0) or 0
                if b_area and declared_area and (b_area > declared_area * 1.3):
                    has_utility = _has_utility_hookup(b_geom, utility_df)
                    confidence = _score_underdeclared(
                        address_match_score=best_score,
                        declared_m2=float(declared_area),
                        actual_m2=float(b_area),
                        has_utility=has_utility,
                    )
                    if confidence < MIN_CONFIDENCE_TO_REPORT:
                        continue
                    gap_area = b_area - declared_area
                    gap_mad  = _estimate_gap(gap_area, tsc_rate, b_floors)
                    backlog_mad = float(gap_mad) * backlog_years
                    evidence = {
                        "gap_type":                    "underdeclared",
                        "declared_m2":                 float(declared_area),
                        "actual_m2":                   float(b_area),
                        "area_ratio":                  round(float(b_area) / float(declared_area), 2),
                        "floor_count":                 b_floors,
                        "effective_area_m2":           round(gap_area * b_floors, 1),
                        "has_utility_hookup":          has_utility,
                        "address_match_score":         round(best_score, 3),
                        "tsc_zone":                    _zone_name(b_norm, zone_type),
                        "estimated_tsc_rate_mad_per_m2": tsc_rate,
                        "backlog_years":               backlog_years,
                        "estimated_backlog_mad":       round(backlog_mad, 2),
                    }
                    candidate = _make_candidate(building, b_id, b_norm, "address", best_score, gap_mad, evidence, confidence)
                    candidates.append(candidate)
                    detected_ids.add(b_id)
            continue  # matched — skip spatial fallback

        # Stage 2: spatial proximity fallback
        spatial_match, spatial_score = _spatial_match(b_geom, tax_gdf)
        if spatial_match and spatial_score >= SIMILARITY_THRESHOLD:
            continue

        # No match — missing_declaration
        estimated_gap = _estimate_gap(b_area, tsc_rate, b_floors)
        has_utility   = _has_utility_hookup(b_geom, utility_df)
        confidence    = _score_confidence(address_match_score=best_score, has_utility=has_utility, area_m2=b_area)

        if confidence < MIN_CONFIDENCE_TO_REPORT:
            continue

        backlog_mad = float(estimated_gap) * backlog_years
        evidence = {
            "gap_type":                    "missing_declaration",
            "address_match_score":         round(best_score, 3),
            "has_utility_hookup":          has_utility,
            "building_area_m2":            b_area,
            "floor_count":                 b_floors,
            "effective_area_m2":           round((b_area or 0) * b_floors, 1),
            "tsc_zone":                    _zone_name(b_norm, zone_type),
            "estimated_tsc_rate_mad_per_m2": tsc_rate,
            "backlog_years":               backlog_years,
            "estimated_backlog_mad":       round(backlog_mad, 2),
        }
        candidate = _make_candidate(
            building, b_id, b_norm,
            "unmatched" if best_score < 0.3 else "low_confidence_match",
            best_score, estimated_gap, evidence, confidence
        )
        candidates.append(candidate)
        detected_ids.add(b_id)

    # ── Stage 3: Unlicensed business detection ────────────────────────────────
    if "osm_tags" in buildings_gdf.columns:
        commercial_mask = buildings_gdf["osm_tags"].apply(_is_commercial)
        for _, building in buildings_gdf[commercial_mask].iterrows():
            b_id   = str(building.get("external_id", ""))
            if b_id in detected_ids:
                continue

            b_norm   = building.get("address_norm")
            b_area   = building.get("area_m2")
            b_geom   = building.get("geometry")
            b_year   = int(building.get("construction_year") or 0)
            tsc_rate = _zone_rate(b_norm, zone_type)

            # Skip if already in tax roll with taxe professionnelle entry
            matched = tax_roll_df[tax_roll_df["address_norm"] == b_norm] if b_norm else pd.DataFrame()
            if not matched.empty and float(matched.iloc[0].get("tpb_annual_mad") or 0) > 0:
                continue

            gap_mad     = _estimate_gap(b_area, tsc_rate * 1.5, 1)  # 1.5× commercial multiplier
            has_utility = _has_utility_hookup(b_geom, utility_df)
            confidence  = _score_confidence(0.05, has_utility, b_area)
            if confidence < MIN_CONFIDENCE_TO_REPORT:
                continue

            tags = building.get("osm_tags") or {}
            commercial_tag  = tags.get("shop") or tags.get("office") or tags.get("building") or "commercial"
            backlog_years_c = max(1, CURRENT_YEAR - b_year) if b_year > 2000 else 3
            backlog_mad     = float(gap_mad) * backlog_years_c
            evidence = {
                "gap_type":                    "unlicensed_business",
                "commercial_tag":              commercial_tag,
                "has_utility_hookup":          has_utility,
                "building_area_m2":            b_area,
                "tsc_zone":                    _zone_name(b_norm, zone_type),
                "estimated_tsc_rate_mad_per_m2": tsc_rate * 1.5,
                "backlog_years":               backlog_years_c,
                "estimated_backlog_mad":       round(backlog_mad, 2),
            }
            candidate = _make_candidate(building, b_id, b_norm, "commercial_tag", 0.05, gap_mad, evidence, confidence)
            candidates.append(candidate)

    candidates.sort(key=lambda c: c.confidence_score, reverse=True)
    logger.info(f"Gap detection complete: {len(candidates)} candidates found")
    return candidates


# ── Internal helpers ──────────────────────────────────────────────────────────

def _zone_rate(address_norm: str | None, zone_type: str) -> float:
    if zone_type != "urban" or not address_norm:
        return DEFAULT_TSC_RATE_PERI
    if any(k in address_norm for k in DOWNTOWN_KEYWORDS):
        return ZONE_RATES["downtown"]
    if any(k in address_norm for k in PERIPHERAL_KEYWORDS):
        return ZONE_RATES["peripheral"]
    return ZONE_RATES["residential"]


def _zone_name(address_norm: str | None, zone_type: str) -> str:
    if zone_type != "urban" or not address_norm:
        return "peripheral"
    if any(k in address_norm for k in DOWNTOWN_KEYWORDS):
        return "downtown"
    if any(k in address_norm for k in PERIPHERAL_KEYWORDS):
        return "peripheral"
    return "residential"


def _is_commercial(osm_tags) -> bool:
    if not isinstance(osm_tags, dict):
        return False
    return (
        str(osm_tags.get("building", "")).lower() in COMMERCIAL_BUILDING_VALUES
        or any(k in osm_tags for k in COMMERCIAL_OSM_KEYS)
    )


def _best_address_match(normalized: str | None, candidate_set: set[str]) -> tuple[float, str | None]:
    if not normalized or not candidate_set:
        return 0.0, None
    best_score = 0.0
    best_match = None
    for candidate in candidate_set:
        score = address_similarity(normalized, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate
    return best_score, best_match


def _tax_roll_to_geodataframe(tax_roll_df: pd.DataFrame) -> gpd.GeoDataFrame | None:
    if "geo_point_wkt" not in tax_roll_df.columns:
        return None
    try:
        from shapely import wkt
        tax_roll_df = tax_roll_df.dropna(subset=["geo_point_wkt"]).copy()
        tax_roll_df["geometry"] = tax_roll_df["geo_point_wkt"].apply(wkt.loads)
        return gpd.GeoDataFrame(tax_roll_df, crs="EPSG:4326")
    except Exception:
        return None


def _spatial_match(geometry, tax_gdf: gpd.GeoDataFrame | None) -> tuple[bool, float]:
    if tax_gdf is None or geometry is None:
        return False, 0.0
    try:
        building_gdf = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326").to_crs("EPSG:32629")
        buffered = building_gdf.iloc[0].geometry.buffer(SPATIAL_BUFFER_METERS)
        tax_utm = tax_gdf.to_crs("EPSG:32629")
        nearby = tax_utm[tax_utm.geometry.within(buffered)]
        if not nearby.empty:
            return True, 0.8
    except Exception as e:
        logger.debug(f"Spatial match error: {e}")
    return False, 0.0


def _has_utility_hookup(geometry, utility_df: pd.DataFrame | None) -> bool:
    if utility_df is None or geometry is None:
        return False
    try:
        from shapely import wkt
        utility_df = utility_df.dropna(subset=["geo_point_wkt"]).copy()
        utility_df["geometry"] = utility_df["geo_point_wkt"].apply(wkt.loads)
        utility_gdf = gpd.GeoDataFrame(utility_df, crs="EPSG:4326").to_crs("EPSG:32629")
        building_utm = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326").to_crs("EPSG:32629")
        buffered = building_utm.iloc[0].geometry.buffer(30)
        return not utility_gdf[utility_gdf.geometry.within(buffered)].empty
    except Exception:
        return False


def _estimate_gap(area_m2: float | None, tsc_rate: float, floor_count: int = 1) -> Decimal:
    if not area_m2:
        return Decimal("0.00")
    effective_area = area_m2 * floor_count
    return Decimal(str(round(effective_area * tsc_rate, 2)))


def _score_underdeclared(
    address_match_score: float,
    declared_m2: float,
    actual_m2: float,
    has_utility: bool,
) -> float:
    score = address_match_score * 0.25
    ratio = actual_m2 / declared_m2 if declared_m2 > 0 else 1.0
    if ratio >= 2.0:
        score += 0.45
    elif ratio >= 1.6:
        score += 0.35
    elif ratio >= 1.4:
        score += 0.25
    else:
        score += 0.15
    if has_utility:
        score += 0.15
    return min(score, 1.0)


def _score_confidence(
    address_match_score: float,
    has_utility: bool,
    area_m2: float | None,
) -> float:
    """
    Heuristic confidence scorer — will be replaced by XGBoost model after first labeled dataset.
    Low address match + utility hookup + large area = high confidence of genuine gap.
    """
    score = 0.0
    score += (1.0 - address_match_score) * 0.4
    if has_utility:
        score += 0.35
    if area_m2:
        if area_m2 >= 200:
            score += 0.20
        elif area_m2 >= 80:
            score += 0.12
        elif area_m2 >= 40:
            score += 0.05
    return min(score, 1.0)


def _make_candidate(
    building_row,
    b_id: str,
    b_norm: str | None,
    method: str,
    match_score: float,
    gap_mad: Decimal,
    evidence: dict,
    confidence: float | None = None,
) -> GapCandidate:
    if confidence is None:
        confidence = _score_confidence(match_score, evidence.get("has_utility_hookup", False), building_row.get("area_m2"))
    return GapCandidate(
        building_external_id=b_id,
        address_raw=str(building_row.get("address_raw", "")),
        address_normalized=b_norm,
        area_m2=building_row.get("area_m2"),
        geometry_wkt=str(building_row.get("geometry")),
        match_method=method,
        match_score=match_score,
        confidence_score=confidence,
        estimated_gap_mad=gap_mad,
        evidence=evidence,
        floor_count=int(building_row.get("floor_count") or 1),
    )
