import streamlit as st
from db.connection import SessionLocal
from models.well import Well


def _load_well(well_name: str) -> Well | None:
    session = SessionLocal()
    try:
        return session.query(Well).filter_by(name=well_name).first()
    finally:
        session.close()


def render(well_name: str = "Well 1"):
    prefix = well_name.replace(" ", "_").lower()
    well = _load_well(well_name)

    # -------------------------------------------------------------------
    # General section
    # -------------------------------------------------------------------
    st.subheader("General")
    g1, g2 = st.columns(2)
    with g1:
        st.text_input("Date", value=well.date or "" if well else "", key=f"{prefix}_date", placeholder="MM/DD/YYYY")
        st.text_input("Rig", value=well.rig or "" if well else "", key=f"{prefix}_rig")
        st.text_input("Directional Rev", value=well.directional_rev or "" if well else "", key=f"{prefix}_directional")
    with g2:
        st.text_input("Rev", value=well.rev or "" if well else "", key=f"{prefix}_rev")
        st.text_input("Start Date", value=well.start_date or "" if well else "", key=f"{prefix}_start_date", placeholder="MM/DD/YYYY")

    st.divider()

    # -------------------------------------------------------------------
    # Well Info section
    # -------------------------------------------------------------------
    st.subheader("Well Info")
    w1, w2 = st.columns(2)
    with w1:
        st.text_input("Block", value=well.block or "" if well else "", key=f"{prefix}_block")
        st.text_input("Well", value=well.well or "" if well else "", key=f"{prefix}_well")
        st.text_input("Water Depth", value=well.water_depth or "" if well else "", key=f"{prefix}_water_depth")
        st.text_input("RKB-ML", value=well.rkb_ml or "" if well else "", key=f"{prefix}_rkb_ml")
    with w2:
        st.text_input("Lease", value=well.lease or "" if well else "", key=f"{prefix}_lease")
        st.text_input("Name", value=well.name or "" if well else "", key=f"{prefix}_name")
        st.text_input("RKB-MSL", value=well.rkb_msl or "" if well else "", key=f"{prefix}_rkb_msl")
        st.text_input("RKB-WH", value=well.rkb_wh or "" if well else "", key=f"{prefix}_rkb_wh")
