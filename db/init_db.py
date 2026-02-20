"""Create all tables in the database. Run once or on app startup."""

from sqlalchemy import inspect, text
from models.base import Base
from db.connection import engine
import models.well  # noqa: F401 — ensure Well table is created
import models.ppfg_data  # noqa: F401 — ensure PpfgData table is created
import models.directional_data  # noqa: F401 — ensure DirectionalData table is created

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
    ("hpwhh_stickup", "VARCHAR(100)"),
    ("lpwhh_stickup", "VARCHAR(100)"),
    ("rkb_to_lpwhh", "VARCHAR(100)"),
    ("rkb_to_hpwhh", "VARCHAR(100)"),
    ("updated_at", "TIMESTAMP"),
]


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_wells_table()
    _migrate_json_data_tables()


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


_JSON_DATA_EXPECTED_COLUMNS = {"id", "well_id", "columns_json", "data_json", "updated_at"}

# Tables that use the standard JSON-data schema (id, well_id, columns_json, data_json, updated_at)
_JSON_DATA_TABLES = ["ppfg_data", "directional_data"]


def _migrate_json_data_tables():
    """Recreate JSON-data tables if their schema is stale."""
    insp = inspect(engine)
    for table_name in _JSON_DATA_TABLES:
        if table_name not in insp.get_table_names():
            continue
        existing = {col["name"] for col in insp.get_columns(table_name)}
        if existing != _JSON_DATA_EXPECTED_COLUMNS:
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE {table_name}"))
            Base.metadata.tables[table_name].create(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tables created.")
