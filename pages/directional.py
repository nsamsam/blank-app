import json
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db.connection import SessionLocal
from models.directional_data import DirectionalData
from models.well import Well

# Expected columns — MD is required, all others are optional
DIRECTIONAL_COLUMNS = [
    "MD (ft)",
    "Incl (°)",
    "Azim (°)",
    "TVD (ft)",
    "TVDSS (ft)",
    "VSEC (ft)",
    "NS (ft)",
    "EW (ft)",
    "Northing (ftUS)",
    "Easting (ftUS)",
    "Latitude (°)",
    "Longitude (°)",
    "DLS (°/100ft)",
    "BR (°/100ft)",
    "TR (°/100ft)",
]

_SAMPLE_HINT = (
    "0\t0.00\t0.00\t0\t-100\t0\t0\t0\t\t\t\t\t\t\t\n"
    "500\t1.50\t45.00\t500\t400\t10\t7\t7\t\t\t\t\t0.30\t\t"
)



# ------------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------------

def _get_well_id(well_name: str) -> int | None:
    session = SessionLocal()
    try:
        well = session.query(Well).filter_by(name=well_name).first()
        return well.id if well else None
    finally:
        session.close()


def _load_from_db(well_id: int) -> pd.DataFrame | None:
    """Load saved directional data for a well."""
    session = SessionLocal()
    try:
        rec = session.query(DirectionalData).filter_by(well_id=well_id).first()
        if not rec or not rec.data_json or rec.data_json == "[]":
            return None
        cols = json.loads(rec.columns_json)
        rows = json.loads(rec.data_json)
        if not rows:
            return None
        return pd.DataFrame(rows, columns=cols)
    finally:
        session.close()


def _save_to_db(well_id: int, df: pd.DataFrame):
    """Upsert directional data for a well."""
    session = SessionLocal()
    try:
        rec = session.query(DirectionalData).filter_by(well_id=well_id).first()
        columns_json = json.dumps(list(df.columns))
        data_json = df.to_json(orient="records")
        if rec:
            rec.columns_json = columns_json
            rec.data_json = data_json
        else:
            rec = DirectionalData(
                well_id=well_id,
                columns_json=columns_json,
                data_json=data_json,
            )
            session.add(rec)
        session.commit()
    finally:
        session.close()


def _delete_from_db(well_id: int):
    """Remove directional data for a well."""
    session = SessionLocal()
    try:
        rec = session.query(DirectionalData).filter_by(well_id=well_id).first()
        if rec:
            session.delete(rec)
            session.commit()
    finally:
        session.close()


# ------------------------------------------------------------------
# Page render
# ------------------------------------------------------------------

def render(well_name: str = "Well 1"):
    prefix = well_name.replace(" ", "_").lower()
    data_key = f"{prefix}_dir_data"
    loaded_key = f"{prefix}_dir_loaded"
    paste_key = f"{prefix}_dir_paste"

    well_id = _get_well_id(well_name)
    if well_id is None:
        st.warning("Well not found.")
        return

    # Load from DB into session_state on first visit
    if not st.session_state.get(loaded_key):
        saved = _load_from_db(well_id)
        if saved is not None:
            st.session_state[data_key] = saved
        st.session_state[loaded_key] = True

    # ------------------------------------------------------------------
    # Collapsible data-input section
    # ------------------------------------------------------------------
    has_data = data_key in st.session_state and st.session_state[data_key] is not None
    with st.expander("Input Data", expanded=not has_data):
        st.caption(
            "Paste tab-separated data from Excel — **no header row needed**. "
            "Columns are assigned in order: "
            + ", ".join(DIRECTIONAL_COLUMNS)
            + ". Leave trailing columns blank if not available."
        )
        pasted = st.text_area(
            "Paste data here",
            height=200,
            key=paste_key,
            placeholder=_SAMPLE_HINT,
        )
        if st.button("Load Data", key=f"{prefix}_dir_load"):
            if pasted.strip():
                try:
                    df = pd.read_csv(StringIO(pasted), sep="\t", header=None)
                    num_cols = df.shape[1]
                    if num_cols > len(DIRECTIONAL_COLUMNS):
                        st.error(
                            f"Pasted data has {num_cols} columns but only "
                            f"{len(DIRECTIONAL_COLUMNS)} are expected."
                        )
                    else:
                        df.columns = DIRECTIONAL_COLUMNS[:num_cols]
                        for col in df.columns:
                            df[col] = df[col].astype(str).str.strip().str.replace(",", "", regex=False)
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                        df = df.dropna(axis=1, how="all")
                        missing = [c for c in ["MD (ft)", "TVD (ft)"] if c not in df.columns]
                        if missing:
                            st.warning(f"Could not parse columns: {', '.join(missing)}. Check your data format.")
                        st.session_state[data_key] = df
                        _save_to_db(well_id, df)
                        st.rerun()
                except Exception as exc:
                    st.error(f"Could not parse data: {exc}")
            else:
                st.warning("Paste some data first.")

        if st.session_state.get(data_key) is not None:
            if st.button("Clear Data", key=f"{prefix}_dir_clear"):
                st.session_state.pop(data_key, None)
                _delete_from_db(well_id)
                st.rerun()

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    df: pd.DataFrame | None = st.session_state.get(data_key)

    if df is not None and not df.empty:
        # Height slider
        height_key = f"{prefix}_dir_height"
        if height_key not in st.session_state:
            st.session_state[height_key] = 800
        chart_height = st.slider(
            "Chart height (px)",
            min_value=400,
            max_value=3000,
            value=st.session_state[height_key],
            step=100,
            key=height_key,
        )

        # --- TVD vs VSEC (wellbore path) ---
        has_tvd = "TVD (ft)" in df.columns
        has_vsec = "VSEC (ft)" in df.columns
        if has_tvd and has_vsec:
            path = df[["VSEC (ft)", "TVD (ft)"]].dropna()
            tvd_min = path["TVD (ft)"].min() - 500
            tvd_max = path["TVD (ft)"].max() + 500
            fig_path = go.Figure()
            fig_path.add_trace(go.Scatter(
                x=path["VSEC (ft)"],
                y=path["TVD (ft)"],
                mode="lines+markers",
                name="Wellbore Path",
            ))
            fig_path.update_layout(
                title="Wellbore Path — TVD vs VSEC",
                xaxis=dict(title="VSEC (ft)", showline=True, linecolor="gray",
                           mirror=True, gridcolor="lightgray"),
                yaxis=dict(title="TVD (ft)", range=[tvd_max, tvd_min], showline=True,
                           linecolor="gray", mirror=True, gridcolor="lightgray"),
                height=chart_height,
                plot_bgcolor="white",
                margin=dict(l=60, r=30, t=60, b=60),
            )
            st.plotly_chart(fig_path, use_container_width=True)

        # --- Plan view (NS vs EW) ---
        has_ns = "NS (ft)" in df.columns
        has_ew = "EW (ft)" in df.columns
        if has_ns and has_ew:
            plan = df[["EW (ft)", "NS (ft)"]].dropna()
            fig_plan = go.Figure()
            fig_plan.add_trace(go.Scatter(
                x=plan["EW (ft)"],
                y=plan["NS (ft)"],
                mode="lines+markers",
                name="Plan View",
            ))
            fig_plan.update_layout(
                title="Plan View — NS vs EW",
                xaxis=dict(title="EW (ft)", showline=True, linecolor="gray",
                           mirror=True, gridcolor="lightgray"),
                yaxis=dict(title="NS (ft)", scaleanchor="x", showline=True,
                           linecolor="gray", mirror=True, gridcolor="lightgray"),
                height=chart_height,
                plot_bgcolor="white",
                margin=dict(l=60, r=30, t=60, b=60),
            )
            st.plotly_chart(fig_plan, use_container_width=True)

        # --- DLS vs MD ---
        has_md = "MD (ft)" in df.columns
        has_dls = "DLS (°/100ft)" in df.columns
        if has_md and has_dls:
            dls = df[["MD (ft)", "DLS (°/100ft)"]].dropna()
            md_min = dls["MD (ft)"].min() - 500
            md_max = dls["MD (ft)"].max() + 500
            fig_dls = go.Figure()
            fig_dls.add_trace(go.Scatter(
                x=dls["DLS (°/100ft)"],
                y=dls["MD (ft)"],
                mode="lines+markers",
                name="DLS",
            ))
            fig_dls.update_layout(
                title="Dog Leg Severity vs MD",
                xaxis=dict(title="DLS (°/100ft)", showline=True, linecolor="gray",
                           mirror=True, gridcolor="lightgray"),
                yaxis=dict(title="MD (ft)", range=[md_max, md_min], showline=True,
                           linecolor="gray", mirror=True, gridcolor="lightgray"),
                height=chart_height,
                plot_bgcolor="white",
                margin=dict(l=60, r=30, t=60, b=60),
            )
            st.plotly_chart(fig_dls, use_container_width=True)

        with st.expander("View Data Table"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No directional data loaded. Expand **Input Data** above and paste from Excel.")
