import streamlit as st
from sqlalchemy import func
from db.connection import SessionLocal
from models.workbook import Project, Entry


def render():
    st.title("Dashboard")

    session = SessionLocal()
    try:
        project_count = session.query(func.count(Project.id)).scalar()
        entry_count = session.query(func.count(Entry.id)).scalar()

        col1, col2 = st.columns(2)
        col1.metric("Projects", project_count)
        col2.metric("Entries", entry_count)

        st.subheader("Recent Entries")
        recent = (
            session.query(Entry)
            .order_by(Entry.created_at.desc())
            .limit(10)
            .all()
        )
        if recent:
            for entry in recent:
                with st.expander(f"{entry.title}  —  {entry.category}"):
                    st.caption(f"Project #{entry.project_id} | {entry.created_at:%Y-%m-%d %H:%M}")
                    st.write(entry.body)
        else:
            st.info("No entries yet. Create a project and start logging.")
    finally:
        session.close()
