import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Engineering Workbook", layout="wide")

# ---------------------------------------------------------------------------
# Authentication gate
# ---------------------------------------------------------------------------
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if not APP_PASSWORD:
    try:
        APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        pass

if not APP_PASSWORD:
    st.error("APP_PASSWORD not configured. Set it as an environment variable in Railway.")
    st.stop()


def check_auth():
    """Block access until the user enters the correct password."""
    if st.session_state.get("authenticated"):
        return True

    st.title("Engineering Workbook")
    st.markdown("This workbook is private. Enter the password to continue.")
    password = st.text_input("Password", type="password", key="login_pw")
    if st.button("Log in"):
        if password == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_auth():
    st.stop()

# ---------------------------------------------------------------------------
# Authenticated — load app
# ---------------------------------------------------------------------------
from db.init_db import init_db

init_db()

# Logout button in sidebar
if st.sidebar.button("Log out"):
    st.session_state["authenticated"] = False
    st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Wells list (persisted in DB)
# ---------------------------------------------------------------------------
from db.connection import SessionLocal
from models.well import Well

st.sidebar.title("Engineering Workbook")
st.sidebar.subheader("Wells")


def _load_wells():
    """Return list of well names from the database."""
    session = SessionLocal()
    try:
        return [w.name for w in session.query(Well).order_by(Well.id).all()]
    finally:
        session.close()


# Add-well form
with st.sidebar.expander("Add Well"):
    new_well_name = st.text_input("Well name", key="new_well_input")
    if st.button("Add", key="add_well_btn"):
        name = new_well_name.strip()
        if not name:
            st.sidebar.warning("Enter a well name.")
        else:
            session = SessionLocal()
            try:
                exists = session.query(Well).filter_by(name=name).first()
                if exists:
                    st.sidebar.warning("Well already exists.")
                else:
                    session.add(Well(name=name))
                    session.commit()
                    st.session_state["active_well"] = name
                    st.rerun()
            finally:
                session.close()

well_names = _load_wells()

if not well_names:
    st.sidebar.info("No wells yet. Add one above.")
    st.stop()

# Ensure active_well is valid
if st.session_state.get("active_well") not in well_names:
    st.session_state["active_well"] = well_names[0]

# Well selector
active_well = st.sidebar.radio(
    "Select Well",
    well_names,
    index=well_names.index(st.session_state["active_well"]),
    key="well_selector",
)
st.session_state["active_well"] = active_well

# Delete well with confirmation
st.sidebar.divider()
if f"confirm_delete_{active_well}" not in st.session_state:
    st.session_state[f"confirm_delete_{active_well}"] = False

if not st.session_state[f"confirm_delete_{active_well}"]:
    if st.sidebar.button("Delete Well", key="delete_well_btn", type="primary"):
        st.session_state[f"confirm_delete_{active_well}"] = True
        st.rerun()
else:
    st.sidebar.warning(f'Are you sure you want to delete **{active_well}**?')
    col_yes, col_no = st.sidebar.columns(2)
    if col_yes.button("Yes, delete", key="confirm_delete_yes"):
        session = SessionLocal()
        try:
            well = session.query(Well).filter_by(name=active_well).first()
            if well:
                session.delete(well)
                session.commit()
        finally:
            session.close()
        st.session_state.pop(f"confirm_delete_{active_well}", None)
        st.session_state.pop("active_well", None)
        st.rerun()
    if col_no.button("Cancel", key="confirm_delete_no"):
        st.session_state[f"confirm_delete_{active_well}"] = False
        st.rerun()

# ---------------------------------------------------------------------------
# Main area — Title row with autosave indicator
# ---------------------------------------------------------------------------
title_col, status_col = st.columns([4, 1])
title_col.title(active_well)
with status_col:
    st.write("")  # spacing to align with title
    st.caption("Autosave on")

# ---------------------------------------------------------------------------
# Tabs for each section
# ---------------------------------------------------------------------------
tab_well_info, tab_projects, tab_calculations, tab_import, tab_new_entry = st.tabs(
    ["Well Info", "Projects", "Calculations", "Import Data", "New Entry"]
)

with tab_well_info:
    from pages import well_info
    well_info.render(active_well)

with tab_projects:
    from pages import projects
    projects.render()

with tab_calculations:
    from pages import calculations
    calculations.render()

with tab_import:
    from pages import import_data
    import_data.render()

with tab_new_entry:
    from pages import new_entry
    new_entry.render()
