import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.db.database import Base


class UtilityConnection(Base):
    __tablename__ = "utility_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commune_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    utility_type: Mapped[str | None] = mapped_column(String(50))
    address_raw: Mapped[str | None] = mapped_column(Text)
    address_normalized: Mapped[str | None] = mapped_column(Text)
    connection_date: Mapped[date | None] = mapped_column(Date)
    meter_id: Mapped[str | None] = mapped_column(String(100))
    imported_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
