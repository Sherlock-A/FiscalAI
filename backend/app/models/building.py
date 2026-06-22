import uuid
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commune_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("communes.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(200))
    address_raw: Mapped[str | None] = mapped_column(Text)
    address_normalized: Mapped[str | None] = mapped_column(Text)
    footprint = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    floor_count: Mapped[int | None] = mapped_column(SmallInteger)
    construction_year: Mapped[int | None] = mapped_column(SmallInteger)
    osm_tags: Mapped[dict | None] = mapped_column(JSONB)
