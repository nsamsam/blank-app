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

# --- Password Protection ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login")
    password = st.text_input("Enter password", type="password")
    if st.button("Login"):
        if password == "NS":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

init_db()


def _get_client():
    """Get a PetroVaultClient from the selected connection, or None."""
    configs = get_api_configs()
    if configs.empty:
        st.warning("No API connections configured. Go to **API Connections** first.")
        return None, None
    selected = st.sidebar.selectbox("Active Connection", configs["name"].tolist(), key="active_conn")
    config_row = configs[configs["name"] == selected].iloc[0]
    return create_client(config_row), config_row


# --- Sidebar Navigation ---
st.sidebar.title("Engineering Workbook")
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "API Connections",
        "Well Model",
        "Channel Data",
        "Resources",
        "API Custom Query",
        "Excel Upload",
        "Data Overlay",
        "SQL Workbook",
    ],
)

# ============================================================
# DASHBOARD
# ============================================================
if page == "Dashboard":
    st.title("Engineering Data Workbook")
    st.markdown("PetroVault API integration + Excel overlays for engineering analysis.")

    col1, col2, col3 = st.columns(3)
    configs = get_api_configs()
    datasets = get_excel_datasets()
    tables = get_all_tables()

    col1.metric("API Connections", len(configs))
    col2.metric("Excel Datasets", len(datasets))
    col3.metric("Database Tables", len(tables))

    # Quick API health check
    if not configs.empty:
        st.subheader("API Status")
        for _, row in configs.iterrows():
            client = create_client(row)
            health_data, err = client.get_health()
            if err:
                st.error(f"**{row['name']}**: {err}")
            else:
                st.success(f"**{row['name']}**: Healthy")
                if isinstance(health_data, dict):
                    with st.expander("Health Details"):
                        st.json(health_data)

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
    st.markdown("Configure connections to PetroVault.")

    with st.expander("Add New Connection", expanded=True):
        with st.form("add_api"):
            name = st.text_input("Connection Name", placeholder="e.g. PetroVault Production")
            base_url = st.text_input(
                "Base URL",
                value="https://pv1.petrolink.net/petrovault/publicapi",
                help="The root URL of the PetroVault Public API",
            )
            auth_type = st.selectbox("Auth Type", ["api_key", "bearer", "basic", "none"])
            api_key = st.text_input("API Key", type="password", help="Your PetroVault API key")
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
        if st.button("Test Connection"):
            row = configs[configs["name"] == selected].iloc[0]
            client = create_client(row)

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Health Check**")
                health, err = client.get_health()
                if err:
                    st.error(err)
                else:
                    st.success("Healthy")
                    st.json(health)
            with col2:
                st.write("**API Version**")
                version, err = client.get_version()
                if err:
                    st.error(err)
                else:
                    st.success("Connected")
                    st.json(version)

# ============================================================
# WELL MODEL
# ============================================================
elif page == "Well Model":
    st.title("Well Model Explorer")
    st.markdown("Browse wells, wellbores, and logs from PetroVault.")

    client, config_row = _get_client()
    if client:
        tab_wells, tab_wellbores, tab_logs = st.tabs(["Wells", "Wellbores", "Logs"])

        # --- Wells Tab ---
        with tab_wells:
            st.subheader("Wells")
            col1, col2 = st.columns(2)
            with col1:
                wells_page = st.number_input("Page", min_value=1, value=1, key="wells_page")
            with col2:
                wells_size = st.number_input("Page Size", min_value=10, max_value=500, value=50, key="wells_size")

            if st.button("Fetch Wells", key="btn_wells"):
                with st.spinner("Fetching wells..."):
                    data, err = client.get_wells(page=wells_page, page_size=wells_size)
                if err:
                    st.error(err)
                elif data:
                    st.json(data) if not isinstance(data, list) else None
                    df, _ = PetroVaultClient._to_dataframe(data)
                    if df is not None and not df.empty:
                        st.dataframe(df, use_container_width=True)
                        st.session_state["wells_df"] = df

                        # Store option
                        if st.button("Store Wells to DB", key="store_wells"):
                            table = store_excel_data(f"wells_{datetime.now().strftime('%Y%m%d_%H%M')}", df, "API")
                            st.success(f"Stored as `{table}`")
                    else:
                        st.info("No wells returned.")

        # --- Wellbores Tab ---
        with tab_wellbores:
            st.subheader("Wellbores")
            well_filter = st.text_input("Filter by Well (ID or name)", key="wb_well_filter",
                                         help="Leave empty to get all wellbores")
            col1, col2 = st.columns(2)
            with col1:
                wb_page = st.number_input("Page", min_value=1, value=1, key="wb_page")
            with col2:
                wb_size = st.number_input("Page Size", min_value=10, max_value=500, value=50, key="wb_size")

            if st.button("Fetch Wellbores", key="btn_wellbores"):
                with st.spinner("Fetching wellbores..."):
                    data, err = client.get_wellbores(
                        well=well_filter if well_filter else None,
                        page=wb_page, page_size=wb_size,
                    )
                if err:
                    st.error(err)
                elif data:
                    df, _ = PetroVaultClient._to_dataframe(data)
                    if df is not None and not df.empty:
                        st.dataframe(df, use_container_width=True)
                        st.session_state["wellbores_df"] = df
                    else:
                        st.info("No wellbores returned.")

        # --- Logs Tab ---
        with tab_logs:
            st.subheader("Logs")
            col1, col2, col3 = st.columns(3)
            with col1:
                log_well = st.text_input("Well (ID or name)", key="log_well",
                                          help="Leave empty to get all logs")
            with col2:
                log_wellbore = st.text_input("Wellbore (ID or name)", key="log_wellbore")
            with col3:
                log_name = st.text_input("Log (ID or name)", key="log_name")

            col1, col2 = st.columns(2)
            with col1:
                log_page = st.number_input("Page", min_value=1, value=1, key="log_page")
            with col2:
                log_size = st.number_input("Page Size", min_value=10, max_value=500, value=50, key="log_size")

            if st.button("Fetch Logs", key="btn_logs"):
                with st.spinner("Fetching logs..."):
                    data, err = client.get_logs(
                        well=log_well if log_well else None,
                        wellbore=log_wellbore if log_wellbore else None,
                        log=log_name if log_name else None,
                        page=log_page, page_size=log_size,
                    )
                if err:
                    st.error(err)
                elif data:
                    df, _ = PetroVaultClient._to_dataframe(data)
                    if df is not None and not df.empty:
                        st.dataframe(df, use_container_width=True)
                        st.session_state["logs_df"] = df

                        if st.button("Store Logs to DB", key="store_logs"):
                            table = store_excel_data(f"logs_{datetime.now().strftime('%Y%m%d_%H%M')}", df, "API")
                            st.success(f"Stored as `{table}`")
                    else:
                        st.info("No logs returned.")

# ============================================================
# CHANNEL DATA
# ============================================================
elif page == "Channel Data":
    st.title("Channel Data")
    st.markdown("Fetch channel data from PetroVault logs — latest values or a date/depth range.")

    client, config_row = _get_client()
    if client:
        tab_data, tab_report = st.tabs(["Channel Data", "Channel Report"])

        # --- Channel Data Tab ---
        with tab_data:
            st.subheader("Channel Data (Raw)")

            log_id = st.text_input("Log ID", help="The ID of the log object to fetch data from", key="cd_log_id")
            mode = st.radio("Mode", ["Latest", "Range"], horizontal=True, key="cd_mode")

            channels_input = st.text_input("Channels (comma-separated)", key="cd_channels",
                                            help="Leave empty for all channels, or specify e.g. DEPTH,ROP,WOB")

            col1, col2, col3 = st.columns(3)
            if mode == "Range":
                with col1:
                    start_val = st.text_input("Start (index or datetime)", key="cd_start",
                                               help="e.g. 2024-01-01T00:00:00 or 1000.0")
                with col2:
                    end_val = st.text_input("End (index or datetime)", key="cd_end")
            else:
                start_val = None
                end_val = None
            with col3 if mode == "Range" else col1:
                max_rows = st.number_input("Max Rows", min_value=1, max_value=100000, value=1000, key="cd_maxrows")

            if st.button("Fetch Channel Data", key="btn_cd"):
                if not log_id:
                    st.error("Enter a Log ID.")
                else:
                    channels = channels_input.strip() if channels_input.strip() else None
                    with st.spinner("Fetching channel data..."):
                        df, err = client.channel_data_as_df(
                            log_id=log_id,
                            start=start_val if start_val else None,
                            end=end_val if end_val else None,
                            channels=channels,
                            max_rows=max_rows,
                            mode="latest" if mode == "Latest" else "range",
                        )
                    if err:
                        st.error(err)
                    elif df is not None and not df.empty:
                        st.success(f"Fetched {len(df)} rows x {len(df.columns)} columns")
                        st.dataframe(df, use_container_width=True)

                        # Chart
                        numeric_cols = df.select_dtypes(include="number").columns.tolist()
                        if len(numeric_cols) >= 2:
                            st.subheader("Quick Chart")
                            all_cols = df.columns.tolist()
                            cx = st.selectbox("X-Axis", all_cols, key="cd_cx")
                            cy = st.multiselect("Y-Axis", numeric_cols, default=numeric_cols[:3], key="cd_cy")
                            if cy:
                                fig = go.Figure()
                                for col in cy:
                                    fig.add_trace(go.Scatter(x=df[cx], y=df[col], mode="lines", name=col))
                                fig.update_layout(template="plotly_white", height=500)
                                st.plotly_chart(fig, use_container_width=True)

                        # Store
                        st.subheader("Store to Database")
                        ds_name = st.text_input("Dataset name",
                                                 value=f"channel_{log_id}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                                                 key="cd_dsname")
                        if st.button("Store", key="cd_store"):
                            table = store_excel_data(ds_name, df, "Channel Data")
                            st.success(f"Stored as `{table}`")

                        # CSV download
                        csv = df.to_csv(index=False)
                        st.download_button("Download CSV", csv, f"channel_data_{log_id}.csv", "text/csv", key="cd_dl")
                    else:
                        st.info("No data returned.")

        # --- Channel Report Tab ---
        with tab_report:
            st.subheader("Channel Report")
            st.markdown("Report format returns data with channel names as columns.")

            rpt_log_id = st.text_input("Log ID", key="rpt_log_id")
            rpt_mode = st.radio("Mode", ["Latest", "Range"], horizontal=True, key="rpt_mode")

            rpt_channels = st.text_input("Channels (comma-separated)", key="rpt_channels")

            col1, col2, col3 = st.columns(3)
            if rpt_mode == "Range":
                with col1:
                    rpt_start = st.text_input("Start", key="rpt_start")
                with col2:
                    rpt_end = st.text_input("End", key="rpt_end")
            else:
                rpt_start = None
                rpt_end = None
            with col3 if rpt_mode == "Range" else col1:
                rpt_max = st.number_input("Max Rows", min_value=1, max_value=100000, value=1000, key="rpt_max")

            if st.button("Fetch Report", key="btn_rpt"):
                if not rpt_log_id:
                    st.error("Enter a Log ID.")
                else:
                    channels = rpt_channels.strip() if rpt_channels.strip() else None
                    with st.spinner("Fetching report..."):
                        df, err = client.channel_report_as_df(
                            log_id=rpt_log_id,
                            start=rpt_start if rpt_start else None,
                            end=rpt_end if rpt_end else None,
                            channels=channels,
                            max_rows=rpt_max,
                            mode="latest" if rpt_mode == "Latest" else "range",
                        )
                    if err:
                        st.error(err)
                    elif df is not None and not df.empty:
                        st.success(f"Report: {len(df)} rows x {len(df.columns)} columns")
                        st.dataframe(df, use_container_width=True)

                        csv = df.to_csv(index=False)
                        st.download_button("Download CSV", csv, f"report_{rpt_log_id}.csv", "text/csv", key="rpt_dl")
                    else:
                        st.info("No report data returned.")

# ============================================================
# RESOURCES
# ============================================================
elif page == "Resources":
    st.title("Resources Explorer")
    st.markdown("Browse and search PetroVault resources.")

    client, config_row = _get_client()
    if client:
        tab_browse, tab_detail = st.tabs(["Browse Resources", "Resource Detail"])

        with tab_browse:
            st.subheader("Search Resources")
            col1, col2 = st.columns(2)
            with col1:
                res_name = st.text_input("Name filter", key="res_name")
            with col2:
                res_type = st.selectbox("Resource type", ["", "Well", "Wellbore", "Log", "MudLog", "Trajectory", "BhaRun", "Tubular"], key="res_type")

            params = {}
            if res_name:
                params["name"] = res_name
            if res_type:
                params["type"] = res_type

            if st.button("Search", key="btn_res"):
                with st.spinner("Searching resources..."):
                    data, err = client.get_resources(params or None)
                if err:
                    st.error(err)
                elif data:
                    df, _ = PetroVaultClient._to_dataframe(data)
                    if df is not None and not df.empty:
                        st.success(f"Found {len(df)} resources")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No resources found.")

        with tab_detail:
            st.subheader("Resource Detail")
            resource_id = st.text_input("Resource ID", key="res_detail_id")
            if st.button("Fetch", key="btn_res_detail"):
                if not resource_id:
                    st.error("Enter a Resource ID.")
                else:
                    with st.spinner("Fetching resource..."):
                        data, err = client.get_resource_by_id(resource_id)
                    if err:
                        st.error(err)
                    elif data:
                        st.json(data)

# ============================================================
# API CUSTOM QUERY (advanced / generic endpoint)
# ============================================================
elif page == "API Custom Query":
    st.title("Custom API Query")
    st.markdown("Call any PetroVault endpoint directly.")

    client, config_row = _get_client()
    if client:
        st.info("**Tip:** Use the dedicated pages (Well Model, Channel Data, Resources) for common operations.")

        endpoint = st.text_input(
            "Endpoint",
            placeholder="e.g. v1/wellmodel/wells or v1/channels/data/latest",
            help="The API endpoint path (without base URL)",
        )

        method = st.radio("Method", ["GET", "POST"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            param_keys = st.text_area("Query Parameter Keys (one per line)",
                                       placeholder="logId\nchannels\nmaxRows")
        with col2:
            param_vals = st.text_area("Query Parameter Values (one per line)",
                                       placeholder="my-log-id\nDEPTH,ROP\n1000")

        post_body = None
        if method == "POST":
            post_body = st.text_area("JSON Body", placeholder='{"key": "value"}', height=150)

        if st.button("Execute"):
            if not endpoint:
                st.error("Enter an endpoint path.")
            else:
                params = {}
                if param_keys.strip() and param_vals.strip():
                    keys = [k.strip() for k in param_keys.strip().split("\n")]
                    vals = [v.strip() for v in param_vals.strip().split("\n")]
                    params = dict(zip(keys, vals))

                with st.spinner("Calling API..."):
                    if method == "GET":
                        data, err = client.get(endpoint, params or None)
                    else:
                        import json
                        json_body = None
                        if post_body:
                            try:
                                json_body = json.loads(post_body)
                            except json.JSONDecodeError:
                                st.error("Invalid JSON body.")
                                st.stop()
                        data, err = client.post(endpoint, json_data=json_body)

                if err:
                    st.error(f"Error: {err}")
                elif data:
                    # Show raw JSON
                    with st.expander("Raw Response", expanded=False):
                        st.json(data)

                    # Try to show as DataFrame
                    df, _ = PetroVaultClient._to_dataframe(data)
                    if df is not None and not df.empty:
                        st.success(f"Fetched {len(df)} rows")
                        st.dataframe(df, use_container_width=True)

                        st.subheader("Store in Database")
                        dataset_name = st.text_input("Dataset name",
                                                      value=f"api_{datetime.now().strftime('%Y%m%d_%H%M')}")
                        if st.button("Store to DB"):
                            table = store_excel_data(dataset_name, df, sheet_name="API Fetch")
                            st.success(f"Stored as table: `{table}`")

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
    st.markdown("Overlay Excel data on API data for comparison and analysis.")

    tables = get_all_tables()
    data_tables = [t for t in tables if t not in ("api_config", "channels", "datasets")]

    if len(data_tables) < 1:
        st.warning("Upload Excel data or fetch API data first to use the overlay feature.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Primary Dataset")
            primary_table = st.selectbox("Select primary table", data_tables, key="primary")
            primary_df, _ = run_custom_query(f'SELECT * FROM "{primary_table}"')

        with col2:
            st.subheader("Overlay Dataset")
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

                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "query_results.csv", "text/csv")

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
