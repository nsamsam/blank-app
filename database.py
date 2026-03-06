import os
import psycopg2
import psycopg2.extras
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime


DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_engine():
    url = DATABASE_URL
    # Railway provides postgres:// but SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_config (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT,
            auth_token TEXT,
            auth_type TEXT DEFAULT 'bearer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            config_id INTEGER REFERENCES api_config(id),
            channel_name TEXT NOT NULL,
            unit TEXT,
            description TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS realtime_data (
            id SERIAL PRIMARY KEY,
            config_id INTEGER REFERENCES api_config(id),
            channel_name TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            depth DOUBLE PRECISION,
            value DOUBLE PRECISION,
            unit TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS excel_data (
            id SERIAL PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            sheet_name TEXT,
            channel_name TEXT,
            timestamp TIMESTAMP,
            depth DOUBLE PRECISION,
            value DOUBLE PRECISION,
            unit TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            description TEXT,
            row_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


def save_api_config(name, base_url, api_key="", auth_token="", auth_type="bearer"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO api_config (name, base_url, api_key, auth_token, auth_type) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (name, base_url, api_key, auth_token, auth_type),
    )
    config_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return config_id


def get_api_configs():
    engine = get_engine()
    df = pd.read_sql_query("SELECT * FROM api_config ORDER BY created_at DESC", engine)
    engine.dispose()
    return df


def delete_api_config(config_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM realtime_data WHERE config_id = %s", (config_id,))
    cursor.execute("DELETE FROM channels WHERE config_id = %s", (config_id,))
    cursor.execute("DELETE FROM api_config WHERE id = %s", (config_id,))
    conn.commit()
    cursor.close()
    conn.close()


def store_realtime_data(config_id, df, channel_col, value_col, timestamp_col=None, depth_col=None, unit=None):
    conn = get_connection()
    cursor = conn.cursor()
    count = 0
    for _, row in df.iterrows():
        cursor.execute(
            "INSERT INTO realtime_data (config_id, channel_name, timestamp, depth, value, unit) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                config_id,
                row[channel_col] if channel_col in df.columns else channel_col,
                row.get(timestamp_col, datetime.now()) if timestamp_col else datetime.now(),
                row.get(depth_col) if depth_col else None,
                row[value_col],
                unit,
            ),
        )
        count += 1
    conn.commit()
    cursor.close()
    conn.close()
    return count


def store_excel_data(dataset_name, df, sheet_name="Sheet1"):
    engine = get_engine()
    table_name = f"excel_{dataset_name.replace(' ', '_').lower()}"

    # Sanitize column names for PostgreSQL (lowercase, no special chars)
    df.columns = [c.strip().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").lower() for c in df.columns]

    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Register dataset
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO datasets (name, source, description, row_count) VALUES (%s, %s, %s, %s)",
        (dataset_name, "excel", f"Uploaded from Excel - Sheet: {sheet_name}", len(df)),
    )
    conn.commit()
    cursor.close()
    conn.close()
    engine.dispose()
    return table_name


def get_excel_datasets():
    engine = get_engine()
    df = pd.read_sql_query("SELECT * FROM datasets WHERE source = 'excel' ORDER BY created_at DESC", engine)
    engine.dispose()
    return df


def load_excel_table(table_name):
    engine = get_engine()
    try:
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', engine)
    except Exception:
        df = pd.DataFrame()
    engine.dispose()
    return df


def delete_dataset(dataset_id, table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM datasets WHERE id = %s", (dataset_id,))
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.commit()
    cursor.close()
    conn.close()


def get_realtime_data(config_id=None, channel_name=None, limit=1000):
    engine = get_engine()
    query = "SELECT * FROM realtime_data WHERE 1=1"
    params = {}
    if config_id:
        query += " AND config_id = :config_id"
        params["config_id"] = config_id
    if channel_name:
        query += " AND channel_name = :channel_name"
        params["channel_name"] = channel_name
    query += f" ORDER BY timestamp DESC LIMIT {limit}"
    df = pd.read_sql_query(text(query), engine, params=params)
    engine.dispose()
    return df


def run_custom_query(query):
    engine = get_engine()
    try:
        df = pd.read_sql_query(text(query), engine)
        engine.dispose()
        return df, None
    except Exception as e:
        engine.dispose()
        return None, str(e)


def get_all_tables():
    engine = get_engine()
    df = pd.read_sql_query(
        "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename",
        engine,
    )
    engine.dispose()
    return df["tablename"].tolist()
