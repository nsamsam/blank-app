import streamlit as st


def render():
    st.title("Well Info")

    # -------------------------------------------------------------------
    # General section
    # -------------------------------------------------------------------
    st.subheader("General")
    g1, g2 = st.columns(2)
    with g1:
        st.text_input("Date", value="", key="wi_date", placeholder="MM/DD/YYYY")
        st.text_input("Rig", value="", key="wi_rig")
        st.text_input("Directional", value="", key="wi_directional")
    with g2:
        st.text_input("Rev", value="", key="wi_rev")
        st.text_input("Start Date", value="", key="wi_start_date", placeholder="MM/DD/YYYY")

    st.divider()

    # -------------------------------------------------------------------
    # Well Info section
    # -------------------------------------------------------------------
    st.subheader("Well Info")
    w1, w2 = st.columns(2)
    with w1:
        st.text_input("Block", value="", key="wi_block")
        st.text_input("Well", value="", key="wi_well")
        st.text_input("Water Depth", value="", key="wi_water_depth")
        st.text_input("RKB-ML", value="", key="wi_rkb_ml")
    with w2:
        st.text_input("Lease", value="", key="wi_lease")
        st.text_input("Name", value="", key="wi_name")
        st.text_input("RKB-MSL", value="", key="wi_rkb_msl")
        st.text_input("RKB-WH", value="", key="wi_rkb_wh")
