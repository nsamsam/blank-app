import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class CasingSection(Base):
    __tablename__ = "casing_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[int] = mapped_column(Integer, ForeignKey("wells.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    section_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hole_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    casing_od: Mapped[str | None] = mapped_column(String(100), nullable=True)
    casing_weight: Mapped[str | None] = mapped_column(String(100), nullable=True)
    casing_grade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    casing_id: Mapped[str | None] = mapped_column("casing_id_val", String(100), nullable=True)
    top_md: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shoe_md: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mud_weight: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
