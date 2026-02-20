import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Dataset(Base):
    """An imported dataset (CSV/Excel) stored as JSON rows."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    source_filename: Mapped[str] = mapped_column(String(500), default="")

    # Column names as JSON list: ["col_a", "col_b", ...]
    columns_json: Mapped[str] = mapped_column(Text, default="[]")

    # Row data as JSON list of dicts: [{"col_a": 1, "col_b": 2}, ...]
    data_json: Mapped[str] = mapped_column(Text, default="[]")

    row_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    project: Mapped["Base"] = relationship("Project", back_populates="datasets")

    def __repr__(self) -> str:
        return f"<Dataset {self.id}: {self.name} ({self.row_count} rows)>"
