import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class CasingDesign(Base):
    __tablename__ = "casing_designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("casing_sections.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Casing properties (ratings & thread)
    collapse_rating: Mapped[str | None] = mapped_column(String(100), nullable=True)
    burst_rating: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tension_rating: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thread: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Pressure / formation data at shoe
    shoe_pp: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shoe_mw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shoe_fg: Mapped[str | None] = mapped_column(String(100), nullable=True)
    toc: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Collapse inputs — cement column
    rho_displace: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rho_tail: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tvd_tail: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rho_lead: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tvd_lead: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tvd_sw: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Burst inputs
    burst_emw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    backup_emw: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Tension inputs
    overpull: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
