import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class PpfgData(Base):
    """PPFG curve data stored as JSON, one record per well."""

    __tablename__ = "ppfg_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[int] = mapped_column(ForeignKey("wells.id"), nullable=False, unique=True)

    # Column names as JSON list: ["TVD", "PP", "Frac Grad", ...]
    columns_json: Mapped[str] = mapped_column(Text, default="[]")

    # Row data as JSON list of dicts: [{"TVD": 1000, "PP": 8.6}, ...]
    data_json: Mapped[str] = mapped_column(Text, default="[]")

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<PpfgData well_id={self.well_id}>"
