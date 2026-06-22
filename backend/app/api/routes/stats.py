"""
KPI statistics endpoint — aggregates for the commune dashboard.
Route: GET /api/v1/gaps/stats

Must be registered in main.py BEFORE the gaps router so that the literal
path /gaps/stats takes priority over the /gaps/{gap_id} parameter route.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Numeric, cast, select, func

from app.db.database import get_db
from app.models.gap_detection import GapDetection
from app.api.deps import get_current_commune_id

router = APIRouter(prefix="/gaps", tags=["Stats"])


@router.get("/stats")
async def get_gap_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    commune_id: Annotated[UUID, Depends(get_current_commune_id)],
):
    """
    Return aggregate KPI metrics for the authenticated commune.
    Used by the dashboard KPI card row.
    """
    # Total gap count
    total_count = await db.scalar(
        select(func.count(GapDetection.id)).where(GapDetection.commune_id == commune_id)
    )

    # Total estimated annual gap in MAD
    total_mad = await db.scalar(
        select(func.coalesce(func.sum(GapDetection.estimated_gap_mad), 0)).where(
            GapDetection.commune_id == commune_id
        )
    )

    # Total estimated backlog (cumulative arrears) — from JSONB evidence field
    total_backlog = await db.scalar(
        select(
            func.coalesce(
                func.sum(
                    cast(
                        func.jsonb_extract_path_text(GapDetection.evidence, "estimated_backlog_mad"),
                        Numeric,
                    )
                ),
                0,
            )
        ).where(GapDetection.commune_id == commune_id)
    )

    # High-confidence count (score >= 0.70)
    high_conf = await db.scalar(
        select(func.count(GapDetection.id)).where(
            GapDetection.commune_id == commune_id,
            GapDetection.confidence_score >= 0.70,
        )
    )

    # Notices sent (status = 'notice_sent')
    notices_sent = await db.scalar(
        select(func.count(GapDetection.id)).where(
            GapDetection.commune_id == commune_id,
            GapDetection.status == "notice_sent",
        )
    )

    # Paid count and MAD recovered
    paid_count = await db.scalar(
        select(func.count(GapDetection.id)).where(
            GapDetection.commune_id == commune_id,
            GapDetection.status == "paid",
        )
    )

    paid_mad = await db.scalar(
        select(func.coalesce(func.sum(GapDetection.estimated_gap_mad), 0)).where(
            GapDetection.commune_id == commune_id,
            GapDetection.status == "paid",
        )
    )

    # Gap type breakdown — count per type
    breakdown_result = await db.execute(
        select(GapDetection.gap_type, func.count(GapDetection.id))
        .where(GapDetection.commune_id == commune_id)
        .group_by(GapDetection.gap_type)
    )
    gap_type_breakdown = {row[0]: row[1] for row in breakdown_result.all()}

    return {
        "total_gaps":          int(total_count or 0),
        "total_gap_mad":       float(total_mad or 0),
        "total_backlog_mad":   float(total_backlog or 0),
        "high_confidence_count": int(high_conf or 0),
        "notices_sent":        int(notices_sent or 0),
        "paid_count":          int(paid_count or 0),
        "paid_mad":            float(paid_mad or 0),
        "gap_type_breakdown":  gap_type_breakdown,
    }
