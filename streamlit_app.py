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
from demo_data import (
    DEMO_WELLS, DEMO_WELLBORES, DEMO_LOGS,
    generate_demo_channel_data, generate_demo_channel_report,
    DEMO_RESOURCES, DEMO_RESOURCE_DETAIL, DEMO_HEALTH, DEMO_VERSION,
)

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

st.sidebar.divider()
demo_mode = st.sidebar.toggle("Demo Mode", value=False, help="Use sample data instead of live API (useful when API credentials lack permissions)")
if demo_mode:
    st.sidebar.info("Using sample data — no API calls will be made.")

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
    if demo_mode:
        st.subheader("API Status")
        st.success("**Demo Connection**: Healthy")
        with st.expander("Health Details"):
            st.json(DEMO_HEALTH)
    elif not configs.empty:
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
            auth_type = st.selectbox("Auth Type", ["basic", "api_key", "bearer", "none"])
            api_key = st.text_input(
                "API Key / Username", type="password",
                help="API key (for api_key auth) or Username (for basic auth)",
            )
            auth_token = st.text_input(
                "Auth Token / Password", type="password",
                help="Bearer token (for bearer auth) or Password (for basic auth)",
            )
            submitted = st.form_submit_button("Save Connection")
            if submitted:
                if not name:
                    st.error("Please enter a Connection Name.")
                elif not base_url:
                    st.error("Please enter a Base URL.")
                else:
                    try:
                        config_id = save_api_config(name, base_url, api_key, auth_token, auth_type)
                        st.success(f"Connection '{name}' saved (ID: {config_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save connection: {e}")

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

    if demo_mode:
        tab_wells, tab_wellbores, tab_logs = st.tabs(["Wells", "Wellbores", "Logs"])

        with tab_wells:
            st.subheader("Wells")
            if st.button("Fetch Wells", key="btn_wells"):
                data = DEMO_WELLS
                flat = PetroVaultClient._flatten_resource_items(data)
                df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                if df is not None and not df.empty:
                    st.success(f"Demo: {len(df)} wells loaded")
                    st.dataframe(df, use_container_width=True)
                    st.session_state["wells_df"] = df
                    if st.button("Store Wells to DB", key="store_wells"):
                        table = store_excel_data(f"wells_{datetime.now().strftime('%Y%m%d_%H%M')}", df, "API")
                        st.success(f"Stored as `{table}`")

        with tab_wellbores:
            st.subheader("Wellbores")
            if st.button("Fetch Wellbores", key="btn_wellbores"):
                data = DEMO_WELLBORES
                flat = PetroVaultClient._flatten_resource_items(data)
                df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                if df is not None and not df.empty:
                    st.success(f"Demo: {len(df)} wellbores loaded")
                    st.dataframe(df, use_container_width=True)
                    st.session_state["wellbores_df"] = df

        with tab_logs:
            st.subheader("Logs")
            if st.button("Fetch Logs", key="btn_logs"):
                data = DEMO_LOGS
                flat = PetroVaultClient._flatten_resource_items(data)
                df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                if df is not None and not df.empty:
                    st.success(f"Demo: {len(df)} logs loaded")
                    st.dataframe(df, use_container_width=True)
                    st.session_state["logs_df"] = df
                    if st.button("Store Logs to DB", key="store_logs"):
                        table = store_excel_data(f"logs_{datetime.now().strftime('%Y%m%d_%H%M')}", df, "API")
                        st.success(f"Stored as `{table}`")
    else:
        client, config_row = _get_client()
        if client:
            tab_wells, tab_wellbores, tab_logs = st.tabs(["Wells", "Wellbores", "Logs"])

            # --- Wells Tab ---
            with tab_wells:
                st.subheader("Wells")
                col1, col2 = st.columns(2)
                with col1:
                    wells_limit = st.number_input("Limit", min_value=1, max_value=1000, value=50, key="wells_limit")
                with col2:
                    wells_fetch = st.text_input("Fetch parts", placeholder="properties,parents,model",
                                                 help="Comma-separated: properties, parents, model, data", key="wells_fetch")

                if st.button("Fetch Wells", key="btn_wells_live"):
                    with st.spinner("Fetching wells..."):
                        data, err = client.get_wells(
                            limit=wells_limit,
                            fetch=wells_fetch if wells_fetch else None,
                        )
                    if err:
                        st.error(err)
                    elif data:
                        paging = PetroVaultClient._extract_paging(data)
                        flat = PetroVaultClient._flatten_resource_items(data)
                        df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                        if df is not None and not df.empty:
                            st.dataframe(df, use_container_width=True)
                            st.session_state["wells_df"] = df
                            if paging.get("hasMore"):
                                st.info(f"Page {paging.get('pageNumber')} — more results available (cursor: `{paging.get('cursor')}`)")

                            if st.button("Store Wells to DB", key="store_wells_live"):
                                table = store_excel_data(f"wells_{datetime.now().strftime('%Y%m%d_%H%M')}", df, "API")
                                st.success(f"Stored as `{table}`")
                        else:
                            st.info("No wells returned.")

            # --- Wellbores Tab ---
            with tab_wellbores:
                st.subheader("Wellbores")
                well_filter = st.text_input("Filter by Well UID", key="wb_well_filter",
                                             help="Leave empty to get all wellbores")
                col1, col2 = st.columns(2)
                with col1:
                    wb_limit = st.number_input("Limit", min_value=1, max_value=1000, value=50, key="wb_limit")
                with col2:
                    wb_fetch = st.text_input("Fetch parts", placeholder="properties,model", key="wb_fetch")

                if st.button("Fetch Wellbores", key="btn_wellbores_live"):
                    with st.spinner("Fetching wellbores..."):
                        data, err = client.get_wellbores(
                            well=well_filter if well_filter else None,
                            limit=wb_limit,
                            fetch=wb_fetch if wb_fetch else None,
                        )
                    if err:
                        st.error(err)
                    elif data:
                        flat = PetroVaultClient._flatten_resource_items(data)
                        df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
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
                    log_well = st.text_input("Well UID", key="log_well",
                                              help="Leave empty to get all logs")
                with col2:
                    log_wellbore = st.text_input("Wellbore UID", key="log_wellbore")
                with col3:
                    log_name = st.text_input("Log UID", key="log_name")

                col1, col2 = st.columns(2)
                with col1:
                    log_limit = st.number_input("Limit", min_value=1, max_value=1000, value=50, key="log_limit")
                with col2:
                    log_fetch = st.text_input("Fetch parts", placeholder="properties,model", key="log_fetch")

                if st.button("Fetch Logs", key="btn_logs_live"):
                    with st.spinner("Fetching logs..."):
                        data, err = client.get_logs(
                            well=log_well if log_well else None,
                            wellbore=log_wellbore if log_wellbore else None,
                            log=log_name if log_name else None,
                            limit=log_limit,
                            fetch=log_fetch if log_fetch else None,
                        )
                    if err:
                        st.error(err)
                    elif data:
                        flat = PetroVaultClient._flatten_resource_items(data)
                        df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                        if df is not None and not df.empty:
                            st.dataframe(df, use_container_width=True)
                            st.session_state["logs_df"] = df

                            if st.button("Store Logs to DB", key="store_logs_live"):
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

    if demo_mode:
        tab_data, tab_report = st.tabs(["Channel Data", "Channel Report"])

        with tab_data:
            st.subheader("Channel Data (Demo)")
            mode = st.radio("Mode", ["Latest", "Range"], horizontal=True, key="cd_mode_demo")
            if st.button("Fetch Channel Data", key="btn_cd_demo"):
                demo_raw = generate_demo_channel_data(500 if mode == "Range" else 10, mode=mode.lower())
                df, _ = PetroVaultClient._to_dataframe(demo_raw)
                if df is not None and not df.empty:
                    st.success(f"Demo: {len(df)} rows x {len(df.columns)} columns")
                    st.dataframe(df, use_container_width=True)

                    numeric_cols = df.select_dtypes(include="number").columns.tolist()
                    if len(numeric_cols) >= 2:
                        st.subheader("Quick Chart")
                        all_cols = df.columns.tolist()
                        cx = st.selectbox("X-Axis", all_cols, key="cd_cx_demo")
                        cy = st.multiselect("Y-Axis", numeric_cols, default=numeric_cols[:3], key="cd_cy_demo")
                        if cy:
                            fig = go.Figure()
                            for col in cy:
                                fig.add_trace(go.Scatter(x=df[cx], y=df[col], mode="lines", name=col))
                            fig.update_layout(template="plotly_white", height=500)
                            st.plotly_chart(fig, use_container_width=True)

                    csv = df.to_csv(index=False)
                    st.download_button("Download CSV", csv, "demo_channel_data.csv", "text/csv", key="cd_dl_demo")

        with tab_report:
            st.subheader("Channel Report (Demo)")
            if st.button("Fetch Report", key="btn_rpt_demo"):
                rows = generate_demo_channel_report(50)
                df = pd.DataFrame(rows)
                st.success(f"Demo Report: {len(df)} rows")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "demo_report.csv", "text/csv", key="rpt_dl_demo")

    else:
        client, config_row = _get_client()
        if not client:
            st.stop()
        tab_data, tab_report = st.tabs(["Channel Data", "Channel Report"])

        # --- Channel Data Tab ---
        with tab_data:
            st.subheader("Channel Data (Raw DataFrame)")
            st.markdown("""
            Uses `/v1/channels/data/range` or `/v1/channels/data/latest`.
            The **Target** must be a WITSML URI for a log, trajectory, or mud log resource.
            """)

            target = st.text_input("Target URI", key="cd_target",
                                    help="WITSML URI for a log object, e.g. //well(uid)/wellbore(uid)/log(uid)",
                                    placeholder="//well_uid/wellbore_uid/log_uid")
            mode = st.radio("Mode", ["Latest", "Range"], horizontal=True, key="cd_mode")

            fields_input = st.text_input("Fields / Mnemonics (comma-separated)", key="cd_fields",
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
                max_rows = st.number_input("Limit", min_value=1, max_value=100000, value=1000, key="cd_limit")

            if st.button("Fetch Channel Data", key="btn_cd"):
                if not target:
                    st.error("Enter a Target URI.")
                else:
                    fields = fields_input.strip() if fields_input.strip() else None
                    with st.spinner("Fetching channel data..."):
                        df, err = client.channel_data_as_df(
                            target=target,
                            start=start_val if start_val else None,
                            end=end_val if end_val else None,
                            fields=fields,
                            limit=max_rows,
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
                                                 value=f"channel_{datetime.now().strftime('%Y%m%d_%H%M')}",
                                                 key="cd_dsname")
                        if st.button("Store", key="cd_store"):
                            table = store_excel_data(ds_name, df, "Channel Data")
                            st.success(f"Stored as `{table}`")

                        # CSV download
                        csv = df.to_csv(index=False)
                        st.download_button("Download CSV", csv, "channel_data.csv", "text/csv", key="cd_dl")
                    else:
                        st.info("No data returned.")

        # --- Channel Report Tab ---
        with tab_report:
            st.subheader("Channel Report")
            st.markdown("""
            Uses `/v1/channels/report/range` or `/v1/channels/report/latest`.
            The **Channels** field takes comma-separated WITSML 1.4 log/channel URIs.
            """)

            rpt_channels = st.text_input("Channel URIs (comma-separated, required)", key="rpt_channels",
                                          help="WITSML 1.4 log and channel URIs. All must share the same index type.")
            rpt_aliases = st.text_input("Aliases (comma-separated, optional)", key="rpt_aliases",
                                         help='Use "-" for no alias on a given channel')
            rpt_metadata = st.checkbox("Include metadata", key="rpt_metadata")
            rpt_mode = st.radio("Mode", ["Latest", "Range"], horizontal=True, key="rpt_mode")

            col1, col2, col3 = st.columns(3)
            if rpt_mode == "Range":
                with col1:
                    rpt_start = st.text_input("Start", key="rpt_start")
                with col2:
                    rpt_end = st.text_input("End", key="rpt_end")
                with col3:
                    rpt_limit = st.number_input("Limit", min_value=1, max_value=100000, value=1000, key="rpt_limit")
                rpt_count = None
            else:
                rpt_start = None
                rpt_end = None
                rpt_limit = None
                with col1:
                    rpt_count = st.number_input("Count (latest points per channel)", min_value=1,
                                                 max_value=100000, value=100, key="rpt_count")

            if st.button("Fetch Report", key="btn_rpt"):
                if not rpt_channels:
                    st.error("Enter at least one Channel URI.")
                else:
                    with st.spinner("Fetching report..."):
                        df, err = client.channel_report_as_df(
                            channels=rpt_channels.strip(),
                            aliases=rpt_aliases.strip() if rpt_aliases.strip() else None,
                            metadata="true" if rpt_metadata else None,
                            start=rpt_start if rpt_start else None,
                            end=rpt_end if rpt_end else None,
                            limit=rpt_limit,
                            count=rpt_count,
                            mode="latest" if rpt_mode == "Latest" else "range",
                        )
                    if err:
                        st.error(err)
                    elif df is not None and not df.empty:
                        st.success(f"Report: {len(df)} rows x {len(df.columns)} columns")
                        st.dataframe(df, use_container_width=True)

                        csv = df.to_csv(index=False)
                        st.download_button("Download CSV", csv, "report.csv", "text/csv", key="rpt_dl")
                    else:
                        st.info("No report data returned.")

# ============================================================
# RESOURCES
# ============================================================
elif page == "Resources":
    st.title("Resources Explorer")
    st.markdown("Browse and search PetroVault resources.")

    if demo_mode:
        tab_browse, tab_detail = st.tabs(["Browse Resources", "Resource Detail"])

        with tab_browse:
            st.subheader("Search Resources (Demo)")
            if st.button("Search", key="btn_res_demo"):
                data = DEMO_RESOURCES
                with st.expander("Raw Response", expanded=False):
                    st.json(data)
                flat = PetroVaultClient._flatten_resource_items(data)
                df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                if df is not None and not df.empty:
                    st.success(f"Demo: Found {len(df)} resources")
                    st.dataframe(df, use_container_width=True)

        with tab_detail:
            st.subheader("Resource Detail (Demo)")
            if st.button("Fetch", key="btn_res_detail_demo"):
                st.json(DEMO_RESOURCE_DETAIL)

    else:
        client, config_row = _get_client()
        if not client:
            st.stop()
        tab_browse, tab_detail = st.tabs(["Browse Resources", "Resource Detail"])

        with tab_browse:
            st.subheader("Search Resources")
            st.markdown("Only one of URI, Parent URI, or Parent ID may be specified.")

            col1, col2 = st.columns(2)
            with col1:
                res_uri = st.text_input("Resource URI", key="res_uri",
                                         help="If specified, returns the single matching resource")
                res_parent_uri = st.text_input("Parent URI", key="res_parent_uri",
                                                help="All results will be descendants of this parent")
                res_parent_id = st.text_input("Parent ID (UUID)", key="res_parent_id")
            with col2:
                res_type = st.selectbox("Resource type",
                                         ["", "well", "wellbore", "log", "mudLog", "trajectory", "bhaRun", "tubular"],
                                         key="res_type")
                res_fetch = st.text_input("Fetch parts", placeholder="properties,parents,model,data", key="res_fetch")
                res_depth = st.number_input("Search depth", min_value=0, max_value=10, value=1, key="res_depth")
                res_limit = st.number_input("Limit", min_value=1, max_value=1000, value=20, key="res_limit")

            if st.button("Search", key="btn_res"):
                with st.spinner("Searching resources..."):
                    data, err = client.get_resources(
                        uri=res_uri if res_uri else None,
                        parent_uri=res_parent_uri if res_parent_uri else None,
                        parent_id=res_parent_id if res_parent_id else None,
                        resource_type=res_type if res_type else None,
                        fetch=res_fetch if res_fetch else None,
                        depth=res_depth if res_depth > 0 else None,
                        limit=res_limit,
                    )
                if err:
                    st.error(err)
                elif data:
                    with st.expander("Raw Response", expanded=False):
                        st.json(data)
                    flat = PetroVaultClient._flatten_resource_items(data)
                    df, _ = PetroVaultClient._to_dataframe(flat if isinstance(flat, list) else data)
                    if df is not None and not df.empty:
                        st.success(f"Found {len(df)} resources")
                        st.dataframe(df, use_container_width=True)
                        paging = PetroVaultClient._extract_paging(data)
                        if paging.get("hasMore"):
                            st.info(f"More results available. Cursor: `{paging.get('cursor')}`")
                    else:
                        st.info("No resources found.")

        with tab_detail:
            st.subheader("Resource Detail")
            resource_id = st.text_input("Resource ID (UUID)", key="res_detail_id")
            detail_fetch = st.text_input("Fetch parts", placeholder="properties,parents,model,data",
                                          key="res_detail_fetch")
            if st.button("Fetch", key="btn_res_detail"):
                if not resource_id:
                    st.error("Enter a Resource ID.")
                else:
                    with st.spinner("Fetching resource..."):
                        data, err = client.get_resource_by_id(
                            resource_id,
                            fetch=detail_fetch if detail_fetch else None,
                        )
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

    if demo_mode:
        st.warning("Custom API queries are not available in Demo Mode. Switch to a live connection to use this feature.")
        st.stop()

    client, config_row = _get_client()
    if client:
        st.info("**Tip:** Use the dedicated pages (Well Model, Channel Data, Resources) for common operations.")

        endpoint = st.text_input(
            "Endpoint",
            placeholder="e.g. v1/wellmodel/wells or v1/channels/report/range",
            help="The API endpoint path (without base URL)",
        )

        method = st.radio("Method", ["GET", "POST"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            param_keys = st.text_area("Query Parameter Keys (one per line)",
                                       placeholder="target\nfields\nlimit")
        with col2:
            param_vals = st.text_area("Query Parameter Values (one per line)",
                                       placeholder="//well/wellbore/log\nDEPTH,ROP\n1000")

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
