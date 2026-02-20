"""Create all tables in the database. Run once or on app startup."""

from sqlalchemy import inspect, text
from models.base import Base
from db.connection import engine
import models.well  # noqa: F401 — ensure Well table is created

# Columns to add to the wells table if they don't already exist
_WELL_COLUMNS_TO_ADD = [
    ("date", "VARCHAR(50)"),
    ("rev", "VARCHAR(50)"),
    ("rig", "VARCHAR(200)"),
    ("start_date", "VARCHAR(50)"),
    ("directional_rev", "VARCHAR(200)"),
    ("block", "VARCHAR(200)"),
    ("lease", "VARCHAR(200)"),
    ("well", "VARCHAR(200)"),
    ("water_depth", "VARCHAR(100)"),
    ("rkb_msl", "VARCHAR(100)"),
    ("rkb_ml", "VARCHAR(100)"),
    ("rkb_wh", "VARCHAR(100)"),
    ("updated_at", "TIMESTAMP"),
]


def init_db():
    # --- ONE-TIME RESET: drop old wells table so it gets recreated cleanly ---
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS wells CASCADE"))
    # -------------------------------------------------------------------------
    Base.metadata.create_all(bind=engine)


def _migrate_wells_table():
    """Add any missing columns to the existing wells table."""
    insp = inspect(engine)
    if "wells" not in insp.get_table_names():
        return
    existing = {col["name"] for col in insp.get_columns("wells")}
    with engine.begin() as conn:
        for col_name, col_type in _WELL_COLUMNS_TO_ADD:
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE wells ADD COLUMN {col_name} {col_type}")
                )


if __name__ == "__main__":
    init_db()
    print("Tables created.")
