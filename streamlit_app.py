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

st.sidebar.title("Engineering Workbook")
page = st.sidebar.radio(
    "Navigate",
    ["Well Info", "Projects", "Calculations", "Import Data", "New Entry"],
)

if page == "Well Info":
    from pages import well_info
    well_info.render()
elif page == "Projects":
    from pages import projects
    projects.render()
elif page == "Calculations":
    from pages import calculations
    calculations.render()
elif page == "Import Data":
    from pages import import_data
    import_data.render()
elif page == "New Entry":
    from pages import new_entry
    new_entry.render()
