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
# Sidebar — Wells list
# ---------------------------------------------------------------------------
st.sidebar.title("Engineering Workbook")

# Initialise wells list in session state
if "wells" not in st.session_state:
    st.session_state["wells"] = ["Well 1"]
if "active_well" not in st.session_state:
    st.session_state["active_well"] = "Well 1"

st.sidebar.subheader("Wells")

# Add-well form
with st.sidebar.expander("Add Well"):
    new_well_name = st.text_input("Well name", key="new_well_input")
    if st.button("Add", key="add_well_btn"):
        name = new_well_name.strip()
        if name and name not in st.session_state["wells"]:
            st.session_state["wells"].append(name)
            st.session_state["active_well"] = name
            st.rerun()
        elif name in st.session_state["wells"]:
            st.sidebar.warning("Well already exists.")

# Well selector
active_well = st.sidebar.radio(
    "Select Well",
    st.session_state["wells"],
    index=st.session_state["wells"].index(st.session_state["active_well"]),
    key="well_selector",
)
st.session_state["active_well"] = active_well

# ---------------------------------------------------------------------------
# Main area — Tabs for each section
# ---------------------------------------------------------------------------
st.title(active_well)

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
