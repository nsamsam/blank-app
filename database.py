import sqlite3
import pandas as pd
from datetime import datetime


DB_PATH = "engineering_data.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS api_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT,
            auth_token TEXT,
            auth_type TEXT DEFAULT 'bearer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_id INTEGER,
            channel_name TEXT NOT NULL,
            unit TEXT,
            description TEXT,
            FOREIGN KEY (config_id) REFERENCES api_config(id)
        );

        CREATE TABLE IF NOT EXISTS realtime_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_id INTEGER,
            channel_name TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            depth REAL,
            value REAL,
            unit TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (config_id) REFERENCES api_config(id)
        );

        CREATE TABLE IF NOT EXISTS excel_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_name TEXT NOT NULL,
            sheet_name TEXT,
            channel_name TEXT,
            timestamp TIMESTAMP,
            depth REAL,
            value REAL,
            unit TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            description TEXT,
            row_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def save_api_config(name, base_url, api_key="", auth_token="", auth_type="bearer"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO api_config (name, base_url, api_key, auth_token, auth_type) VALUES (?, ?, ?, ?, ?)",
        (name, base_url, api_key, auth_token, auth_type),
    )
    conn.commit()
    config_id = cursor.lastrowid
    conn.close()
    return config_id


def get_api_configs():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM api_config ORDER BY created_at DESC", conn)
    conn.close()
    return df


def delete_api_config(config_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM realtime_data WHERE config_id = ?", (config_id,))
    cursor.execute("DELETE FROM channels WHERE config_id = ?", (config_id,))
    cursor.execute("DELETE FROM api_config WHERE id = ?", (config_id,))
    conn.commit()
    conn.close()


def store_realtime_data(config_id, df, channel_col, value_col, timestamp_col=None, depth_col=None, unit=None):
    conn = get_connection()
    records = []
    for _, row in df.iterrows():
        records.append({
            "config_id": config_id,
            "channel_name": row[channel_col] if channel_col in df.columns else channel_col,
            "timestamp": row.get(timestamp_col, datetime.now()) if timestamp_col else datetime.now(),
            "depth": row.get(depth_col) if depth_col else None,
            "value": row[value_col],
            "unit": unit,
        })
    insert_df = pd.DataFrame(records)
    insert_df.to_sql("realtime_data", conn, if_exists="append", index=False)
    conn.close()
    return len(records)


def store_excel_data(dataset_name, df, sheet_name="Sheet1"):
    conn = get_connection()
    cursor = conn.cursor()

    # Store raw data in a dedicated table for this dataset
    table_name = f"excel_{dataset_name.replace(' ', '_').lower()}"
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    # Register dataset
    cursor.execute(
        "INSERT INTO datasets (name, source, description, row_count) VALUES (?, ?, ?, ?)",
        (dataset_name, "excel", f"Uploaded from Excel - Sheet: {sheet_name}", len(df)),
    )
    conn.commit()
    conn.close()
    return table_name


def get_excel_datasets():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM datasets WHERE source = 'excel' ORDER BY created_at DESC", conn)
    conn.close()
    return df


def load_excel_table(table_name):
    conn = get_connection()
    try:
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def delete_dataset(dataset_id, table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.commit()
    conn.close()


def get_realtime_data(config_id=None, channel_name=None, limit=1000):
    conn = get_connection()
    query = "SELECT * FROM realtime_data WHERE 1=1"
    params = []
    if config_id:
        query += " AND config_id = ?"
        params.append(config_id)
    if channel_name:
        query += " AND channel_name = ?"
        params.append(channel_name)
    query += f" ORDER BY timestamp DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def run_custom_query(query):
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        conn.close()
        return None, str(e)


def get_all_tables():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name", conn
    )
    conn.close()
    return df["name"].tolist()
