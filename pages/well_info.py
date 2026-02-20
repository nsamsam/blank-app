import streamlit as st
from db.connection import SessionLocal
from models.well import Well


def _load_well(well_name: str) -> Well | None:
    session = SessionLocal()
    try:
        return session.query(Well).filter_by(name=well_name).first()
    finally:
        session.close()


def _save_well(well_name: str, data: dict):
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

    # -------------------------------------------------------------------
    # General section
    # -------------------------------------------------------------------
    st.subheader("General")
    g1, g2 = st.columns(2)
    with g1:
        date = st.text_input("Date", value=well.date or "" if well else "", key=f"{prefix}_date", placeholder="MM/DD/YYYY")
        rig = st.text_input("Rig", value=well.rig or "" if well else "", key=f"{prefix}_rig")
        directional_rev = st.text_input("Directional Rev", value=well.directional_rev or "" if well else "", key=f"{prefix}_directional")
    with g2:
        rev = st.text_input("Rev", value=well.rev or "" if well else "", key=f"{prefix}_rev")
        start_date = st.text_input("Start Date", value=well.start_date or "" if well else "", key=f"{prefix}_start_date", placeholder="MM/DD/YYYY")

    st.divider()

    # -------------------------------------------------------------------
    # Well Info section
    # -------------------------------------------------------------------
    st.subheader("Well Info")
    w1, w2 = st.columns(2)
    with w1:
        block = st.text_input("Block", value=well.block or "" if well else "", key=f"{prefix}_block")
        well_field = st.text_input("Well", value=well.well or "" if well else "", key=f"{prefix}_well")
        water_depth = st.text_input("Water Depth", value=well.water_depth or "" if well else "", key=f"{prefix}_water_depth")
        rkb_ml = st.text_input("RKB-ML", value=well.rkb_ml or "" if well else "", key=f"{prefix}_rkb_ml")
    with w2:
        lease = st.text_input("Lease", value=well.lease or "" if well else "", key=f"{prefix}_lease")
        name = st.text_input("Name", value=well.name or "" if well else "", key=f"{prefix}_name")
        rkb_msl = st.text_input("RKB-MSL", value=well.rkb_msl or "" if well else "", key=f"{prefix}_rkb_msl")
        rkb_wh = st.text_input("RKB-WH", value=well.rkb_wh or "" if well else "", key=f"{prefix}_rkb_wh")

    # Save button
    if st.button("Save Well Info", key=f"{prefix}_save_btn"):
        _save_well(well_name, {
            "date": date,
            "rev": rev,
            "rig": rig,
            "start_date": start_date,
            "directional_rev": directional_rev,
            "block": block,
            "lease": lease,
            "well": well_field,
            "water_depth": water_depth,
            "rkb_msl": rkb_msl,
            "rkb_ml": rkb_ml,
            "rkb_wh": rkb_wh,
        })
        st.success("Well info saved.")
