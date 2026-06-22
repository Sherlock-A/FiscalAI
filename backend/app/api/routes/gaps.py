"""
Gap detections API — the core output of FiscalAI.

Endpoints:
  GET  /gaps              - list detections for a commune (paginated, filterable)
  GET  /gaps/{id}         - single detection with full evidence
  POST /gaps/{id}/status  - update status (sent_notice, dismissed, paid)
  POST /gaps/{id}/notice  - generate enforcement notice PDF
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.db.database import get_db
from app.models.gap_detection import GapDetection
from app.models.building import Building
from app.api.deps import get_current_commune_id, get_current_user_claims, require_role
from app.api.schemas.gaps import (
    GapDetectionResponse,
    GapListResponse,
    StatusUpdateRequest,
)
from app.services.audit import log_action

router = APIRouter(prefix="/gaps", tags=["Gap Detections"])


def _lat_lon_cols():
    centroid = func.ST_Centroid(Building.footprint)
    return (
        func.ST_Y(centroid).label("latitude"),
        func.ST_X(centroid).label("longitude"),
    )


@router.get("", response_model=GapListResponse)
async def list_gaps(
    db: Annotated[AsyncSession, Depends(get_db)],
    commune_id: Annotated[UUID, Depends(get_current_commune_id)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status_filter: str | None = Query(None, alias="status"),
    gap_type: str | None = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    min_gap_mad: float = Query(0.0, ge=0.0),
    sort_by: str = Query("confidence_score", enum=["confidence_score", "estimated_gap_mad", "detected_at"]),
):
    """
    Return paginated gap detections for the authenticated commune.
    Results are always scoped to the caller's commune_id (row-level isolation).
    """
    conditions = [GapDetection.commune_id == commune_id]

    if status_filter:
        conditions.append(GapDetection.status == status_filter)
    if gap_type:
        conditions.append(GapDetection.gap_type == gap_type)
    if min_confidence > 0:
        conditions.append(GapDetection.confidence_score >= min_confidence)
    if min_gap_mad > 0:
        conditions.append(GapDetection.estimated_gap_mad >= min_gap_mad)

    sort_col = {
        "confidence_score": desc(GapDetection.confidence_score),
        "estimated_gap_mad": desc(GapDetection.estimated_gap_mad),
        "detected_at": desc(GapDetection.detected_at),
    }[sort_by]

    offset = (page - 1) * page_size
    lat_col, lon_col = _lat_lon_cols()

    result = await db.execute(
        select(GapDetection, lat_col, lon_col)
        .outerjoin(Building, GapDetection.building_id == Building.id)
        .where(and_(*conditions))
        .order_by(sort_col)
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    total_result = await db.execute(
        select(func.count(GapDetection.id)).where(and_(*conditions))
    )
    total = total_result.scalar() or 0

    items = []
    for gap, latitude, longitude in rows:
        r = GapDetectionResponse.model_validate(gap)
        r.latitude = float(latitude) if latitude is not None else None
        r.longitude = float(longitude) if longitude is not None else None
        items.append(r)

    return GapListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{gap_id}", response_model=GapDetectionResponse)
async def get_gap(
    gap_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    commune_id: Annotated[UUID, Depends(get_current_commune_id)],
):
    lat_col, lon_col = _lat_lon_cols()
    result = await db.execute(
        select(GapDetection, lat_col, lon_col)
        .outerjoin(Building, GapDetection.building_id == Building.id)
        .where(GapDetection.id == gap_id)
    )
    row = result.first()
    if not row or row[0].commune_id != commune_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection not found")

    gap, latitude, longitude = row
    r = GapDetectionResponse.model_validate(gap)
    r.latitude = float(latitude) if latitude is not None else None
    r.longitude = float(longitude) if longitude is not None else None
    return r


@router.patch("/{gap_id}/status", response_model=GapDetectionResponse)
async def update_gap_status(
    gap_id: UUID,
    body: StatusUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    commune_id: Annotated[UUID, Depends(get_current_commune_id)],
    claims: Annotated[dict, Depends(get_current_user_claims)],
    _: Annotated[None, Depends(require_role(["admin", "analyst"]))],
):
    valid_statuses = {"new", "under_review", "notice_sent", "paid", "contested", "dismissed"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    gap = await db.get(GapDetection, gap_id)
    if not gap or gap.commune_id != commune_id:
        raise HTTPException(status_code=404, detail="Detection not found")

    old_status = gap.status
    gap.status = body.status
    await db.flush()

    await log_action(
        db,
        actor_id=UUID(claims["sub"]),
        commune_id=commune_id,
        action="gap.status_update",
        resource_type="gap_detection",
        resource_id=gap_id,
        payload={"old_status": old_status, "new_status": body.status, "note": body.note},
    )

    r = GapDetectionResponse.model_validate(gap)
    return r
