from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict


class GapDetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    commune_id: UUID
    building_id: UUID | None
    address_resolved: str
    gap_type: str
    confidence_score: Decimal | None
    estimated_gap_mad: Decimal | None
    evidence: dict[str, Any] | None
    status: str
    assigned_to: UUID | None
    detected_at: datetime
    updated_at: datetime
    latitude: float | None = None
    longitude: float | None = None


class GapListResponse(BaseModel):
    items: list[GapDetectionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class StatusUpdateRequest(BaseModel):
    status: str
    note: str | None = None
