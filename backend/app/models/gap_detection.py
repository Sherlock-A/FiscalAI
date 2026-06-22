import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GapDetection(Base):
    __tablename__ = "gap_detections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commune_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("communes.id", ondelete="CASCADE"))
    building_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("buildings.id"))
    utility_conn_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("utility_connections.id"))
    address_resolved: Mapped[str] = mapped_column(Text, nullable=False)
    gap_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    estimated_gap_mad: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="new")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # server_default lets PostgreSQL set the timestamp on INSERT.
    # onupdate uses a Python callable so SQLAlchemy writes the value directly
    # into the Python object on UPDATE — avoids an async lazy-load when Pydantic
    # serialises the model immediately after flush().
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow)
