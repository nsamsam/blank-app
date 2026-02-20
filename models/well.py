import datetime
from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Well(Base):
    __tablename__ = "wells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rev: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rig: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    directional_rev: Mapped[str | None] = mapped_column(String(200), nullable=True)
    block: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lease: Mapped[str | None] = mapped_column(String(200), nullable=True)
    well: Mapped[str | None] = mapped_column(String(200), nullable=True)
    water_depth: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rkb_msl: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rkb_ml: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rkb_wh: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
