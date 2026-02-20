import streamlit as st
from db.connection import SessionLocal
from models.workbook import Project, Entry

CATEGORIES = ["general", "calculation", "observation", "test result", "design note", "issue"]


def render():
    st.title("New Entry")

    session = SessionLocal()
    try:
        projects = session.query(Project).order_by(Project.name).all()
        if not projects:
            st.warning("Create a project first before adding entries.")
            return

        with st.form("new_entry", clear_on_submit=True):
            project = st.selectbox(
                "Project",
                projects,
                format_func=lambda p: p.name,
            )
            title = st.text_input("Title")
            category = st.selectbox("Category", CATEGORIES)
            body = st.text_area("Body / Notes", height=250)
            submitted = st.form_submit_button("Save Entry")

            if submitted and title:
                entry = Entry(
                    project_id=project.id,
                    title=title,
                    category=category,
                    body=body,
                )
                session.add(entry)
                session.commit()
                st.success(f"Entry '{title}' saved to {project.name}.")
                st.rerun()
    finally:
        session.close()
