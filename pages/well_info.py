import streamlit as st


def render(well_name: str = "Well 1"):
    # Build a prefix from the well name so each well's fields are independent
    prefix = well_name.replace(" ", "_").lower()

    # -------------------------------------------------------------------
    # General section
    # -------------------------------------------------------------------
    st.subheader("General")
    g1, g2 = st.columns(2)
    with g1:
        st.text_input("Date", value="", key=f"{prefix}_date", placeholder="MM/DD/YYYY")
        st.text_input("Rig", value="", key=f"{prefix}_rig")
        st.text_input("Directional", value="", key=f"{prefix}_directional")
    with g2:
        st.text_input("Rev", value="", key=f"{prefix}_rev")
        st.text_input("Start Date", value="", key=f"{prefix}_start_date", placeholder="MM/DD/YYYY")

    st.divider()

    # -------------------------------------------------------------------
    # Well Info section
    # -------------------------------------------------------------------
    st.subheader("Well Info")
    w1, w2 = st.columns(2)
    with w1:
        st.text_input("Block", value="", key=f"{prefix}_block")
        st.text_input("Well", value="", key=f"{prefix}_well")
        st.text_input("Water Depth", value="", key=f"{prefix}_water_depth")
        st.text_input("RKB-ML", value="", key=f"{prefix}_rkb_ml")
    with w2:
        st.text_input("Lease", value="", key=f"{prefix}_lease")
        st.text_input("Name", value="", key=f"{prefix}_name")
        st.text_input("RKB-MSL", value="", key=f"{prefix}_rkb_msl")
        st.text_input("RKB-WH", value="", key=f"{prefix}_rkb_wh")
