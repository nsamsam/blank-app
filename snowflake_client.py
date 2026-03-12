"""Snowflake connector for WellView data."""

import pandas as pd
import streamlit as st

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False


# Default connection parameters (WellView read-only)
DEFAULT_CONFIG = {
    "account": "mm48497.us-east-2.aws",
    "user": "WellView_read_user",
    "password": "fMLmFyHchvWJ4ehDdvRQ",
    "warehouse": "Compute_WH",
    "database": "PELOTON_TALOSENERGY_TALOSENERGY_WV120",
    "schema": "TALOSENERGY_WV120_CALC",
}


@st.cache_resource(ttl=600)
def get_snowflake_connection(_config: dict = None):
    """Create and cache a Snowflake connection."""
    if not SNOWFLAKE_AVAILABLE:
        return None, "snowflake-connector-python is not installed."
    cfg = _config or DEFAULT_CONFIG
    try:
        conn = snowflake.connector.connect(
            account=cfg["account"],
            user=cfg["user"],
            password=cfg["password"],
            warehouse=cfg["warehouse"],
            database=cfg["database"],
            schema=cfg["schema"],
        )
        return conn, None
    except Exception as e:
        return None, str(e)


def test_snowflake_connection(config: dict = None) -> tuple[bool, str]:
    """Test connectivity and return (ok, message)."""
    conn, err = get_snowflake_connection(config)
    if err:
        return False, err
    try:
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_VERSION()")
        version = cur.fetchone()[0]
        cur.close()
        return True, f"Connected — Snowflake v{version}"
    except Exception as e:
        return False, str(e)


def get_schemas(config: dict = None) -> tuple[list[str], str | None]:
    """List schemas in the database."""
    conn, err = get_snowflake_connection(config)
    if err:
        return [], err
    try:
        cur = conn.cursor()
        cur.execute("SHOW SCHEMAS")
        rows = cur.fetchall()
        cur.close()
        return [r[1] for r in rows], None
    except Exception as e:
        return [], str(e)


def get_tables(schema: str = None, config: dict = None) -> tuple[list[str], str | None]:
    """List tables in a schema."""
    conn, err = get_snowflake_connection(config)
    if err:
        return [], err
    try:
        cur = conn.cursor()
        if schema:
            cur.execute(f"SHOW TABLES IN SCHEMA \"{schema}\"")
        else:
            cur.execute("SHOW TABLES")
        rows = cur.fetchall()
        cur.close()
        return [r[1] for r in rows], None
    except Exception as e:
        return [], str(e)


def get_views(schema: str = None, config: dict = None) -> tuple[list[str], str | None]:
    """List views in a schema."""
    conn, err = get_snowflake_connection(config)
    if err:
        return [], err
    try:
        cur = conn.cursor()
        if schema:
            cur.execute(f"SHOW VIEWS IN SCHEMA \"{schema}\"")
        else:
            cur.execute("SHOW VIEWS")
        rows = cur.fetchall()
        cur.close()
        return [r[1] for r in rows], None
    except Exception as e:
        return [], str(e)


def get_columns(table: str, schema: str = None, config: dict = None) -> tuple[pd.DataFrame, str | None]:
    """Get column info for a table."""
    conn, err = get_snowflake_connection(config)
    if err:
        return pd.DataFrame(), err
    try:
        cur = conn.cursor()
        full_name = f'"{schema}"."{table}"' if schema else f'"{table}"'
        cur.execute(f"DESCRIBE TABLE {full_name}")
        rows = cur.fetchall()
        desc = cur.description
        cur.close()
        cols = [d[0] for d in desc]
        df = pd.DataFrame(rows, columns=cols)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def run_query(sql: str, config: dict = None, limit: int = 10000) -> tuple[pd.DataFrame | None, str | None]:
    """Run a read-only SQL query and return a DataFrame."""
    conn, err = get_snowflake_connection(config)
    if err:
        return None, err
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchmany(limit)
        desc = cur.description
        cur.close()
        if not desc:
            return pd.DataFrame(), None
        cols = [d[0] for d in desc]
        df = pd.DataFrame(rows, columns=cols)
        return df, None
    except Exception as e:
        return None, str(e)


def preview_table(table: str, schema: str = None, config: dict = None, limit: int = 100) -> tuple[pd.DataFrame | None, str | None]:
    """Quick preview of a table's data."""
    full_name = f'"{schema}"."{table}"' if schema else f'"{table}"'
    return run_query(f"SELECT * FROM {full_name} LIMIT {limit}", config)
