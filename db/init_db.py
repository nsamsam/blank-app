"""Create all tables in the database. Run once or on app startup."""

from models.base import Base
from db.connection import engine
import models.well  # noqa: F401 — ensure Well table is created


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tables created.")
