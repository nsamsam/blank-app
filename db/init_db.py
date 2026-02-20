"""Create all tables in the database. Run once or on app startup."""

from models.base import Base
from db.connection import engine


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tables created.")
