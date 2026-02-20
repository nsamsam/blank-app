import streamlit as st
from db.connection import SessionLocal
from models.well import Well

# Fields that map DB column → session state suffix
_FIELDS = {
    "date": "date",
    "rev": "rev",
    "rig": "rig",
    "start_date": "start_date",
    "directional_rev": "directional",
    "block": "block",
    "lease": "lease",
    "well": "well",
    "water_depth": "water_depth",
    "rkb_msl": "rkb_msl",
    "rkb_ml": "rkb_ml",
    "rkb_wh": "rkb_wh",
    "hpwhh_stickup": "hpwhh_stickup",
    "lpwhh_stickup": "lpwhh_stickup",
    "rkb_to_lpwhh": "rkb_to_lpwhh",
    "rkb_to_hpwhh": "rkb_to_hpwhh",
}


def _init_session_state(well_name: str, prefix: str):
    """Load well data from DB into session state (runs once per well)."""
    init_key = f"{prefix}_loaded"
    if st.session_state.get(init_key):
        return
    session = SessionLocal()
    try:
        well = session.query(Well).filter_by(name=well_name).first()
        for db_col, suffix in _FIELDS.items():
            st.session_state[f"{prefix}_{suffix}"] = (getattr(well, db_col, None) or "") if well else ""
    finally:
        session.close()
    st.session_state[init_key] = True


def _autosave(well_name: str, prefix: str):
    """Save all well info fields from session state to the database."""
    data = {db_col: st.session_state.get(f"{prefix}_{suffix}", "") for db_col, suffix in _FIELDS.items()}
    session = SessionLocal()
    try:
        well = session.query(Well).filter_by(name=well_name).first()
        if well:
            for k, v in data.items():
                setattr(well, k, v)
            session.commit()
    finally:
        session.close()
    st.toast("Autosaved!")


def render(well_name: str = "Well 1"):
    prefix = well_name.replace(" ", "_").lower()

    # Load DB values into session state on first visit for this well
    _init_session_state(well_name, prefix)

    def _calc_derived(do_save=True):
        """Recalculate all derived fields (RKB-ML, RKB to LPWHH, RKB to HPWHH)."""
        wd = st.session_state.get(f"{prefix}_water_depth", "")
        msl = st.session_state.get(f"{prefix}_rkb_msl", "")
        try:
            rkb_ml = float(wd) + float(msl)
            st.session_state[f"{prefix}_rkb_ml"] = str(rkb_ml)
        except (ValueError, TypeError):
            rkb_ml = None

        if rkb_ml is not None:
            lp = st.session_state.get(f"{prefix}_lpwhh_stickup", "")
            try:
                st.session_state[f"{prefix}_rkb_to_lpwhh"] = str(rkb_ml - float(lp))
            except (ValueError, TypeError):
                pass
            hp = st.session_state.get(f"{prefix}_hpwhh_stickup", "")
            try:
                st.session_state[f"{prefix}_rkb_to_hpwhh"] = str(rkb_ml - float(hp))
            except (ValueError, TypeError):
                pass

        if do_save:
            _autosave(well_name, prefix)

    def _recalc_derived():
        _calc_derived(do_save=True)

    # Eagerly compute derived fields on every render so they stay up-to-date
    _calc_derived(do_save=False)

    save = lambda: _autosave(well_name, prefix)

    # -------------------------------------------------------------------
    # General section
    # -------------------------------------------------------------------
    st.subheader("General")
    g1, g2 = st.columns(2)
    with g1:
        st.text_input("Date", key=f"{prefix}_date", placeholder="MM/DD/YYYY", on_change=save)
        st.text_input("Rig", key=f"{prefix}_rig", on_change=save)
        st.text_input("Directional Rev", key=f"{prefix}_directional", on_change=save)
    with g2:
        st.text_input("Rev", key=f"{prefix}_rev", on_change=save)
        st.text_input("Start Date", key=f"{prefix}_start_date", placeholder="MM/DD/YYYY", on_change=save)

    st.divider()

    # -------------------------------------------------------------------
    # Well Info section
    # -------------------------------------------------------------------
    st.subheader("Well Info")
    w1, w2 = st.columns(2)
    with w1:
        st.text_input("Block", key=f"{prefix}_block", on_change=save)
        st.text_input("Well", key=f"{prefix}_well", on_change=save)
        st.text_input("Water Depth", key=f"{prefix}_water_depth", on_change=_recalc_derived)
        st.text_input("RKB-ML", key=f"{prefix}_rkb_ml", disabled=True, help="Auto: Water Depth + RKB-MSL")
        st.text_input("HPWHH Stick up", key=f"{prefix}_hpwhh_stickup", on_change=_recalc_derived)
        st.text_input("RKB to HPWHH", key=f"{prefix}_rkb_to_hpwhh", disabled=True, help="Auto: RKB-ML − HPWHH Stick up")
    with w2:
        st.text_input("Lease", key=f"{prefix}_lease", on_change=save)
        st.text_input("Name", key=f"{prefix}_name", on_change=save)
        st.text_input("RKB-MSL", key=f"{prefix}_rkb_msl", on_change=_recalc_derived)
        st.text_input("LPWHH Stick up", key=f"{prefix}_lpwhh_stickup", on_change=_recalc_derived)
        st.text_input("RKB to LPWHH", key=f"{prefix}_rkb_to_lpwhh", disabled=True, help="Auto: RKB-ML − LPWHH Stick up")
