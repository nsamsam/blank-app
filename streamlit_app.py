import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from database import (
    init_db, save_api_config, get_api_configs, delete_api_config,
    store_excel_data, get_excel_datasets, load_excel_table, delete_dataset,
    get_realtime_data, store_realtime_data, run_custom_query, get_all_tables,
)
from api_client import PetroVaultClient, create_client

st.set_page_config(page_title="Engineering Data Workbook", layout="wide")
init_db()

# --- Sidebar Navigation ---
st.sidebar.title("Engineering Workbook")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "API Connections", "API Data Fetch", "Excel Upload", "Data Overlay", "SQL Workbook"],
)

# ============================================================
# DASHBOARD
# ============================================================
if page == "Dashboard":
    st.title("Engineering Data Workbook")
    st.markdown("Real-time API data + Excel overlays for engineering analysis.")

    col1, col2, col3 = st.columns(3)
    configs = get_api_configs()
    datasets = get_excel_datasets()
    tables = get_all_tables()

    col1.metric("API Connections", len(configs))
    col2.metric("Excel Datasets", len(datasets))
    col3.metric("Database Tables", len(tables))

    st.subheader("Database Tables")
    if tables:
        selected_table = st.selectbox("Select a table to preview", tables)
        if selected_table:
            df, err = run_custom_query(f'SELECT * FROM "{selected_table}" LIMIT 100')
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            elif err:
                st.error(err)
            else:
                st.info("Table is empty.")
    else:
        st.info("No tables yet. Connect an API or upload Excel data to get started.")

# ============================================================
# API CONNECTIONS
# ============================================================
elif page == "API Connections":
    st.title("API Connections")
    st.markdown("Configure connections to PetroVault or other data APIs.")

    with st.expander("Add New Connection", expanded=True):
        with st.form("add_api"):
            name = st.text_input("Connection Name", placeholder="e.g. PetroVault Production")
            base_url = st.text_input(
                "Base URL",
                value="https://pv1.petrolink.net/petrovault/publicapi",
                help="The root URL of the API (without trailing slash)",
            )
            auth_type = st.selectbox("Auth Type", ["bearer", "api_key", "basic", "none"])
            api_key = st.text_input("API Key", type="password")
            auth_token = st.text_input("Auth Token / Password", type="password")
            submitted = st.form_submit_button("Save Connection")
            if submitted and name and base_url:
                config_id = save_api_config(name, base_url, api_key, auth_token, auth_type)
                st.success(f"Connection '{name}' saved (ID: {config_id})")
                st.rerun()

    st.subheader("Saved Connections")
    configs = get_api_configs()
    if configs.empty:
        st.info("No connections configured yet.")
    else:
        for _, row in configs.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{row['name']}** — `{row['base_url']}`")
            col2.write(f"Auth: {row['auth_type']}")
            if col3.button("Delete", key=f"del_{row['id']}"):
                delete_api_config(row["id"])
                st.rerun()

        # Test connection
        st.subheader("Test Connection")
        config_names = configs["name"].tolist()
        selected = st.selectbox("Select connection", config_names)
        if st.button("Test"):
            row = configs[configs["name"] == selected].iloc[0]
            client = create_client(row)
            status, msg = client.test_connection()
            if status:
                st.success(f"Status {status}: Connected successfully")
                with st.expander("Response"):
                    st.code(msg)
            else:
                st.error(f"Failed: {msg}")

# ============================================================
# API DATA FETCH
# ============================================================
elif page == "API Data Fetch":
    st.title("Fetch Data from API")
    configs = get_api_configs()

    if configs.empty:
        st.warning("No API connections configured. Go to 'API Connections' first.")
    else:
        selected = st.selectbox("Connection", configs["name"].tolist())
        config_row = configs[configs["name"] == selected].iloc[0]

        endpoint = st.text_input(
            "Endpoint",
            placeholder="e.g. /api/v1/wells or /api/v1/channels/data",
            help="The API endpoint path to fetch data from",
        )

        col1, col2 = st.columns(2)
        with col1:
            param_keys = st.text_area("Query Parameter Keys (one per line)", placeholder="wellId\nstartDate\nendDate")
        with col2:
            param_vals = st.text_area("Query Parameter Values (one per line)", placeholder="WELL-001\n2024-01-01\n2024-12-31")

        if st.button("Fetch Data"):
            if not endpoint:
                st.error("Enter an endpoint path.")
            else:
                client = create_client(config_row)
                params = {}
                if param_keys.strip() and param_vals.strip():
                    keys = [k.strip() for k in param_keys.strip().split("\n")]
                    vals = [v.strip() for v in param_vals.strip().split("\n")]
                    params = dict(zip(keys, vals))

                with st.spinner("Fetching data..."):
                    df, error = client.fetch_data_as_df(endpoint, params or None)

                if error:
                    st.error(f"Error: {error}")
                elif df is not None and not df.empty:
                    st.success(f"Fetched {len(df)} rows")
                    st.dataframe(df, use_container_width=True)

                    # Option to store in DB
                    st.subheader("Store in Database")
                    dataset_name = st.text_input("Dataset name for storage", value=f"api_{selected}_{datetime.now().strftime('%Y%m%d_%H%M')}")
                    if st.button("Store to DB"):
                        table = store_excel_data(dataset_name, df, sheet_name="API Fetch")
                        st.success(f"Stored as table: `{table}`")
                else:
                    st.info("No data returned.")

        # Show stored real-time data
        st.divider()
        st.subheader("Stored API Data")
        rt_data = get_realtime_data(config_id=int(config_row["id"]))
        if not rt_data.empty:
            st.dataframe(rt_data, use_container_width=True)
        else:
            st.info("No stored real-time data for this connection yet.")

# ============================================================
# EXCEL UPLOAD
# ============================================================
elif page == "Excel Upload":
    st.title("Excel Data Upload")
    st.markdown("Upload Excel or CSV files to store in the database and overlay with API data.")

    uploaded = st.file_uploader("Upload file", type=["xlsx", "xls", "csv"])
    if uploaded:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
            sheets = {"CSV": df}
        else:
            xls = pd.ExcelFile(uploaded)
            sheet_names = xls.sheet_names
            selected_sheets = st.multiselect("Select sheets to import", sheet_names, default=sheet_names)
            sheets = {s: xls.parse(s) for s in selected_sheets}

        for sheet_name, df in sheets.items():
            st.subheader(f"Sheet: {sheet_name}")
            st.write(f"{len(df)} rows x {len(df.columns)} columns")
            st.dataframe(df.head(50), use_container_width=True)

        dataset_name = st.text_input("Dataset name", value=uploaded.name.rsplit(".", 1)[0])
        if st.button("Import to Database"):
            for sheet_name, df in sheets.items():
                suffix = f"_{sheet_name}" if len(sheets) > 1 else ""
                table = store_excel_data(f"{dataset_name}{suffix}", df, sheet_name)
                st.success(f"Sheet '{sheet_name}' stored as `{table}` ({len(df)} rows)")
            st.rerun()

    st.divider()
    st.subheader("Stored Excel Datasets")
    datasets = get_excel_datasets()
    if datasets.empty:
        st.info("No Excel datasets uploaded yet.")
    else:
        for _, row in datasets.iterrows():
            table_name = f"excel_{row['name'].replace(' ', '_').lower()}"
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{row['name']}** — {row['row_count']} rows — {row['created_at']}")
            if col2.button("View", key=f"view_{row['id']}"):
                data = load_excel_table(table_name)
                st.dataframe(data, use_container_width=True)
            if col3.button("Delete", key=f"xdel_{row['id']}"):
                delete_dataset(row["id"], table_name)
                st.rerun()

# ============================================================
# DATA OVERLAY
# ============================================================
elif page == "Data Overlay":
    st.title("Data Overlay")
    st.markdown("Overlay Excel data on real-time API data for comparison and analysis.")

    tables = get_all_tables()
    data_tables = [t for t in tables if t not in ("api_config", "channels", "datasets")]

    if len(data_tables) < 1:
        st.warning("Upload Excel data or fetch API data first to use the overlay feature.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Primary Dataset (API / Real-time)")
            primary_table = st.selectbox("Select primary table", data_tables, key="primary")
            primary_df, _ = run_custom_query(f'SELECT * FROM "{primary_table}"')

        with col2:
            st.subheader("Overlay Dataset (Excel)")
            overlay_options = [t for t in data_tables if t != primary_table]
            if overlay_options:
                overlay_table = st.selectbox("Select overlay table", overlay_options, key="overlay")
                overlay_df, _ = run_custom_query(f'SELECT * FROM "{overlay_table}"')
            else:
                overlay_table = None
                overlay_df = None

        if primary_df is not None and not primary_df.empty:
            st.divider()
            st.subheader("Chart Configuration")

            p_cols = primary_df.columns.tolist()
            numeric_cols_p = primary_df.select_dtypes(include="number").columns.tolist()

            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("X-Axis column (primary)", p_cols, key="xcol")
            with col2:
                y_col = st.selectbox("Y-Axis column (primary)", numeric_cols_p if numeric_cols_p else p_cols, key="ycol")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=primary_df[x_col],
                y=primary_df[y_col],
                mode="lines+markers",
                name=f"{primary_table}: {y_col}",
                line=dict(color="blue"),
            ))

            if overlay_df is not None and not overlay_df.empty:
                o_cols = overlay_df.columns.tolist()
                numeric_cols_o = overlay_df.select_dtypes(include="number").columns.tolist()
                col1, col2 = st.columns(2)
                with col1:
                    ox_col = st.selectbox("X-Axis column (overlay)", o_cols, key="oxcol")
                with col2:
                    oy_col = st.selectbox("Y-Axis column (overlay)", numeric_cols_o if numeric_cols_o else o_cols, key="oycol")

                fig.add_trace(go.Scatter(
                    x=overlay_df[ox_col],
                    y=overlay_df[oy_col],
                    mode="lines+markers",
                    name=f"{overlay_table}: {oy_col}",
                    line=dict(color="red", dash="dash"),
                ))

            fig.update_layout(
                title="Data Overlay Chart",
                xaxis_title=x_col,
                yaxis_title=y_col,
                template="plotly_white",
                height=600,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Data tables side by side
            st.subheader("Data Tables")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**{primary_table}**")
                st.dataframe(primary_df, use_container_width=True)
            with c2:
                if overlay_df is not None:
                    st.write(f"**{overlay_table}**")
                    st.dataframe(overlay_df, use_container_width=True)

# ============================================================
# SQL WORKBOOK
# ============================================================
elif page == "SQL Workbook":
    st.title("SQL Workbook")
    st.markdown("Run custom SQL queries against the database.")

    tables = get_all_tables()
    if tables:
        with st.expander("Available Tables"):
            for t in tables:
                st.code(t)

    query = st.text_area(
        "SQL Query",
        value="SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';",
        height=150,
        help="Write any SELECT query. Only read-only queries are supported.",
    )
    if st.button("Run Query"):
        if query.strip():
            df, err = run_custom_query(query)
            if err:
                st.error(f"Query error: {err}")
            elif df is not None:
                st.success(f"Returned {len(df)} rows")
                st.dataframe(df, use_container_width=True)

                # Download as CSV
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "query_results.csv", "text/csv")

    # Quick query templates
    st.divider()
    st.subheader("Quick Queries")
    templates = {
        "Show all tables": "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename;",
        "API Connections": "SELECT id, name, base_url, auth_type, created_at FROM api_config;",
        "Excel Datasets": "SELECT id, name, source, row_count, created_at FROM datasets;",
        "Real-time Data (latest 50)": "SELECT * FROM realtime_data ORDER BY timestamp DESC LIMIT 50;",
    }
    for label, q in templates.items():
        if st.button(label, key=f"tpl_{label}"):
            df, err = run_custom_query(q)
            if err:
                st.error(err)
            elif df is not None:
                st.dataframe(df, use_container_width=True)
