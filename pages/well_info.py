import streamlit as st
from db.connection import SessionLocal
from models.well import Well


def _load_well(well_name: str) -> Well | None:
    session = SessionLocal()
    try:
        return session.query(Well).filter_by(name=well_name).first()
    finally:
        session.close()


def _autosave(well_name: str):
    """Save all well info fields from session state to the database."""
    prefix = well_name.replace(" ", "_").lower()
    field_map = {
        "date": f"{prefix}_date",
        "rev": f"{prefix}_rev",
        "rig": f"{prefix}_rig",
        "start_date": f"{prefix}_start_date",
        "directional_rev": f"{prefix}_directional",
        "block": f"{prefix}_block",
        "lease": f"{prefix}_lease",
        "well": f"{prefix}_well",
        "water_depth": f"{prefix}_water_depth",
        "rkb_msl": f"{prefix}_rkb_msl",
        "rkb_ml": f"{prefix}_rkb_ml",
        "rkb_wh": f"{prefix}_rkb_wh",
    }
    data = {db_col: st.session_state.get(ss_key, "") for db_col, ss_key in field_map.items()}
    session = SessionLocal()
    try:
        well = session.query(Well).filter_by(name=well_name).first()
        if well:
            for k, v in data.items():
                setattr(well, k, v)
            session.commit()
    finally:
        session.close()


def render(well_name: str = "Well 1"):
    prefix = well_name.replace(" ", "_").lower()
    well = _load_well(well_name)
    save = lambda: _autosave(well_name)

    # -------------------------------------------------------------------
    # General section
    # -------------------------------------------------------------------
    st.subheader("General")
    g1, g2 = st.columns(2)
    with g1:
        st.text_input("Date", value=well.date or "" if well else "", key=f"{prefix}_date", placeholder="MM/DD/YYYY", on_change=save)
        st.text_input("Rig", value=well.rig or "" if well else "", key=f"{prefix}_rig", on_change=save)
        st.text_input("Directional Rev", value=well.directional_rev or "" if well else "", key=f"{prefix}_directional", on_change=save)
    with g2:
        st.text_input("Rev", value=well.rev or "" if well else "", key=f"{prefix}_rev", on_change=save)
        st.text_input("Start Date", value=well.start_date or "" if well else "", key=f"{prefix}_start_date", placeholder="MM/DD/YYYY", on_change=save)

    st.divider()

    # -------------------------------------------------------------------
    # Well Info section
    # -------------------------------------------------------------------
    st.subheader("Well Info")
    w1, w2 = st.columns(2)
    with w1:
        st.text_input("Block", value=well.block or "" if well else "", key=f"{prefix}_block", on_change=save)
        st.text_input("Well", value=well.well or "" if well else "", key=f"{prefix}_well", on_change=save)
        st.text_input("Water Depth", value=well.water_depth or "" if well else "", key=f"{prefix}_water_depth", on_change=save)
        st.text_input("RKB-ML", value=well.rkb_ml or "" if well else "", key=f"{prefix}_rkb_ml", on_change=save)
    with w2:
        st.text_input("Lease", value=well.lease or "" if well else "", key=f"{prefix}_lease", on_change=save)
        st.text_input("Name", value=well.name or "" if well else "", key=f"{prefix}_name", on_change=save)
        st.text_input("RKB-MSL", value=well.rkb_msl or "" if well else "", key=f"{prefix}_rkb_msl", on_change=save)
        st.text_input("RKB-WH", value=well.rkb_wh or "" if well else "", key=f"{prefix}_rkb_wh", on_change=save)
