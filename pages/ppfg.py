import streamlit as st
import pandas as pd
import plotly.graph_objects as go

_SAMPLE_HINT = "Depth\tPore Pressure\tFrac Gradient\n1000\t8.6\t12.5\n2000\t9.0\t13.0"


def render(well_name: str = "Well 1"):
    prefix = well_name.replace(" ", "_").lower()
    data_key = f"{prefix}_ppfg_data"
    paste_key = f"{prefix}_ppfg_paste"

    # ------------------------------------------------------------------
    # Collapsible data-input section
    # ------------------------------------------------------------------
    with st.expander("Input Data", expanded=not bool(st.session_state.get(data_key))):
        st.caption(
            "Paste tab-separated data from Excel. "
            "First column = Depth (TVD). Remaining columns are plotted as curves."
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
                    if df.shape[1] < 2:
                        st.error("Need at least two columns (Depth + one curve).")
                    else:
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
        depth_col = df.columns[0]
        curve_cols = df.columns[1:]

        fig = go.Figure()
        for col in curve_cols:
            fig.add_trace(go.Scatter(
                x=df[col],
                y=df[depth_col],
                mode="lines+markers",
                name=col,
            ))

        fig.update_layout(
            title="PPFG Plot",
            xaxis_title="Pressure / Gradient",
            yaxis_title=depth_col,
            yaxis=dict(autorange="reversed"),  # depth increases downward
            height=700,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Show data table below chart
        with st.expander("View Data Table"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No PPFG data loaded. Expand **Input Data** above and paste from Excel.")
