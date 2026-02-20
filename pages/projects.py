import streamlit as st
from db.connection import SessionLocal
from models.workbook import Project


def render():
    st.title("Projects")

    session = SessionLocal()
    try:
        # --- Create a new project ---
        with st.form("new_project", clear_on_submit=True):
            st.subheader("Create Project")
            name = st.text_input("Project Name")
            description = st.text_area("Description")
            submitted = st.form_submit_button("Create")
            if submitted and name:
                project = Project(name=name, description=description)
                session.add(project)
                session.commit()
                st.success(f"Project '{name}' created.")
                st.rerun()

        # --- List existing projects ---
        st.subheader("All Projects")
        projects = session.query(Project).order_by(Project.created_at.desc()).all()
        if projects:
            for p in projects:
                with st.expander(f"{p.name}  ({len(p.entries)} entries)"):
                    st.write(p.description or "_No description_")
                    st.caption(f"Created {p.created_at:%Y-%m-%d %H:%M}")
                    if st.button(f"Delete '{p.name}'", key=f"del_{p.id}"):
                        session.delete(p)
                        session.commit()
                        st.rerun()
        else:
            st.info("No projects yet. Create one above.")
    finally:
        session.close()
