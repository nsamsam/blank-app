import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Project(Base):
    """A project groups related workbook entries together."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    entries: Mapped[list["Entry"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Entry.created_at.desc()"
    )

    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.name}>"


class Entry(Base):
    """A single workbook entry — notes, calculations, observations, etc."""

    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="general")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    project: Mapped["Project"] = relationship(back_populates="entries")

    def __repr__(self) -> str:
        return f"<Entry {self.id}: {self.title}>"
