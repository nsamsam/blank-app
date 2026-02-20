import streamlit as st
from db.init_db import init_db

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Engineering Workbook", layout="wide")

# Ensure tables exist on first run
init_db()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("Engineering Workbook")
page = st.sidebar.radio("Navigate", ["Dashboard", "Projects", "New Entry"])

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if page == "Dashboard":
    from pages import dashboard
    dashboard.render()
elif page == "Projects":
    from pages import projects
    projects.render()
elif page == "New Entry":
    from pages import new_entry
    new_entry.render()
