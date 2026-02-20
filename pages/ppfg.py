import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Expected columns — TVD is required, all others are optional
PPFG_COLUMNS = [
    "TVD",
    "MW-0deg breakout",
    "PP",
    "Min H",
    "Frac Grad",
    "Frac Int",
    "OBG",
    "95% OBG",
    "90% OBG",
    "85% OBG",
    "750psi over OBG",
]

_HEADER_LINE = "\t".join(PPFG_COLUMNS)
_SAMPLE_HINT = (
    f"{_HEADER_LINE}\n"
    "1000\t\t8.6\t\t12.5\t\t14.0\t\t\t\n"
    "2000\t\t9.0\t\t13.0\t\t15.0\t\t\t"
)


def _normalize_col(name: str) -> str:
    """Lowercase + strip for fuzzy column matching."""
    return name.strip().lower()


def _match_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Try to map pasted columns to the expected PPFG columns."""
    norm_map = {_normalize_col(c): c for c in PPFG_COLUMNS}
    rename = {}
    for col in df.columns:
        normed = _normalize_col(col)
        if normed in norm_map:
            rename[col] = norm_map[normed]
    if rename:
        df = df.rename(columns=rename)
    return df


def render(well_name: str = "Well 1"):
    prefix = well_name.replace(" ", "_").lower()
    data_key = f"{prefix}_ppfg_data"
    paste_key = f"{prefix}_ppfg_paste"

    # ------------------------------------------------------------------
    # Collapsible data-input section
    # ------------------------------------------------------------------
    has_data = data_key in st.session_state and st.session_state[data_key] is not None
    with st.expander("Input Data", expanded=not has_data):
        st.caption(
            "Paste tab-separated data from Excel. "
            "Columns: **TVD** (required) plus any of: "
            + ", ".join(PPFG_COLUMNS[1:])
            + ". Leave columns blank if not available."
        )
        pasted = st.text_area(
            "Paste data here",
            height=200,
            key=paste_key,
            placeholder=_SAMPLE_HINT,
        )
        if st.button("Load Data", key=f"{prefix}_ppfg_load"):
            if pasted.strip():
                try:
                    from io import StringIO
                    df = pd.read_csv(StringIO(pasted), sep="\t")
                    df = _match_columns(df)

                    # Validate TVD column exists
                    if "TVD" not in df.columns:
                        st.error(
                            "Could not find a **TVD** column. "
                            "Make sure the first column header is 'TVD'."
                        )
                    else:
                        # Convert to numeric, coerce blanks to NaN
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                        # Drop columns that are entirely empty
                        df = df.dropna(axis=1, how="all")
                        st.session_state[data_key] = df
                        st.rerun()
                except Exception as exc:
                    st.error(f"Could not parse data: {exc}")
            else:
                st.warning("Paste some data first.")

        if st.session_state.get(data_key) is not None:
            if st.button("Clear Data", key=f"{prefix}_ppfg_clear"):
                st.session_state.pop(data_key, None)
                st.rerun()

    # ------------------------------------------------------------------
    # Chart — full width when expander is collapsed
    # ------------------------------------------------------------------
    df: pd.DataFrame | None = st.session_state.get(data_key)

    if df is not None and not df.empty:
        depth_col = "TVD"
        curve_cols = [c for c in df.columns if c != depth_col and df[c].notna().any()]

        # Height slider so user can stretch the chart like in Excel
        height_key = f"{prefix}_ppfg_height"
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

        fig = go.Figure()
        for col in curve_cols:
            series = df[[depth_col, col]].dropna()
            fig.add_trace(go.Scatter(
                x=series[col],
                y=series[depth_col],
                mode="lines+markers",
                name=col,
            ))

        fig.update_layout(
            title="PPFG Plot",
            xaxis=dict(
                title="Pressure / Gradient (ppg)",
                dtick=0.5,
                minor=dict(dtick=0.25, showgrid=True, gridcolor="lightgray"),
                showline=True,
                linecolor="gray",
                mirror=True,
                gridcolor="lightgray",
            ),
            yaxis=dict(
                title="TVD (ft)",
                autorange="reversed",
                dtick=500,
                minor=dict(dtick=250, showgrid=True, gridcolor="lightgray"),
                showline=True,
                linecolor="gray",
                mirror=True,
                gridcolor="lightgray",
            ),
            height=chart_height,
            plot_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            # Gray border around the plot area
            margin=dict(l=60, r=30, t=60, b=60),
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View Data Table"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No PPFG data loaded. Expand **Input Data** above and paste from Excel.")
