"""
Audit log read API — chronological record of all actions taken by commune agents.
Route: GET /api/v1/audit

Scoped automatically to the caller's commune_id via JWT.
"""

from typing import Annotated
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_commune_id
from app.db.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogItem(BaseModel):
    id: int
    actor_email: str | None
    action: str
    resource_type: str | None
    resource_id: UUID | None
    payload: dict | None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    commune_id: Annotated[UUID, Depends(get_current_commune_id)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Return paginated audit log for the authenticated commune, newest first."""
    offset = (page - 1) * page_size
    where = AuditLog.commune_id == commune_id

    rows = (
        await db.execute(
            select(AuditLog)
            .where(where)
            .order_by(desc(AuditLog.occurred_at))
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()

    total = await db.scalar(
        select(func.count(AuditLog.id)).where(where)
    )

    return AuditLogListResponse(
        items=[AuditLogItem.model_validate(r) for r in rows],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )
