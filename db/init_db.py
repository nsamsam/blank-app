"""Create all tables in the database. Run once or on app startup."""

from sqlalchemy import inspect, text
from models.base import Base
from db.connection import engine
import models.well  # noqa: F401 — ensure Well table is created
import models.ppfg_data  # noqa: F401 — ensure PpfgData table is created
import models.directional_data  # noqa: F401 — ensure DirectionalData table is created
import models.casing_section  # noqa: F401 — ensure CasingSection table is created
import models.casing_design  # noqa: F401 — ensure CasingDesign table is created

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


_CASING_COLUMNS_TO_ADD = [
    ("top_tvd", "VARCHAR(100)"),
    ("shoe_tvd", "VARCHAR(100)"),
    ("collapse_rating", "VARCHAR(100)"),
    ("burst_rating", "VARCHAR(100)"),
    ("tension_rating", "VARCHAR(100)"),
    ("thread", "VARCHAR(200)"),
    ("toc", "VARCHAR(100)"),
    ("cement_length", "VARCHAR(100)"),
]


_CASING_DESIGN_COLUMNS_TO_ADD = [
    ("md_tail", "VARCHAR(100)"),
    ("md_lead", "VARCHAR(100)"),
]


def init_db():
    # Drop stale JSON-data tables BEFORE create_all, so they get recreated
    # with the correct schema. create_all skips tables that already exist.
    _drop_stale_json_data_tables()
    Base.metadata.create_all(bind=engine)
    _migrate_wells_table()
    _migrate_casing_sections_table()
    _migrate_casing_designs_table()


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


def _migrate_casing_sections_table():
    """Add any missing columns to the existing casing_sections table."""
    insp = inspect(engine)
    if "casing_sections" not in insp.get_table_names():
        return
    existing = {col["name"] for col in insp.get_columns("casing_sections")}
    with engine.begin() as conn:
        for col_name, col_type in _CASING_COLUMNS_TO_ADD:
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE casing_sections ADD COLUMN {col_name} {col_type}")
                )


def _migrate_casing_designs_table():
    """Add any missing columns to the existing casing_designs table."""
    insp = inspect(engine)
    if "casing_designs" not in insp.get_table_names():
        return
    existing = {col["name"] for col in insp.get_columns("casing_designs")}
    with engine.begin() as conn:
        for col_name, col_type in _CASING_DESIGN_COLUMNS_TO_ADD:
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE casing_designs ADD COLUMN {col_name} {col_type}")
                )


_JSON_DATA_EXPECTED_COLUMNS = {"id", "well_id", "columns_json", "data_json", "updated_at"}

# Tables that use the standard JSON-data schema (id, well_id, columns_json, data_json, updated_at)
_JSON_DATA_TABLES = ["ppfg_data", "directional_data"]


def _drop_stale_json_data_tables():
    """Drop JSON-data tables whose schema doesn't match the model."""
    insp = inspect(engine)
    tables = insp.get_table_names()
    for table_name in _JSON_DATA_TABLES:
        if table_name not in tables:
            continue
        existing = {col["name"] for col in insp.get_columns(table_name)}
        if existing != _JSON_DATA_EXPECTED_COLUMNS:
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE {table_name}"))



if __name__ == "__main__":
    init_db()
    print("Tables created.")
