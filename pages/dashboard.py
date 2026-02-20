import streamlit as st
from sqlalchemy import func
from db.connection import SessionLocal
from models.workbook import Project, Entry
from models.calculation import Calculation
from models.dataset import Dataset


def render():
    st.title("Dashboard")

    session = SessionLocal()
    try:
        project_count = session.query(func.count(Project.id)).scalar()
        entry_count = session.query(func.count(Entry.id)).scalar()
        calc_count = session.query(func.count(Calculation.id)).scalar()
        dataset_count = session.query(func.count(Dataset.id)).scalar()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projects", project_count)
        c2.metric("Entries", entry_count)
        c3.metric("Calculations", calc_count)
        c4.metric("Datasets", dataset_count)

        # --- Recent calculations ---
        st.subheader("Recent Calculations")
        recent_calcs = (
            session.query(Calculation)
            .order_by(Calculation.created_at.desc())
            .limit(5)
            .all()
        )
        if recent_calcs:
            for c in recent_calcs:
                with st.expander(f"{c.title}  =  {c.result_value} {c.result_unit}"):
                    st.caption(f"{c.created_at:%Y-%m-%d %H:%M}")
                    if c.formula_latex:
                        st.latex(c.formula_latex)
                    else:
                        st.code(c.formula)
        else:
            st.info("No calculations yet.")

        # --- Recent entries ---
        st.subheader("Recent Entries")
        recent = (
            session.query(Entry)
            .order_by(Entry.created_at.desc())
            .limit(5)
            .all()
        )
        if recent:
            for entry in recent:
                with st.expander(f"{entry.title}  —  {entry.category}"):
                    st.caption(
                        f"Project #{entry.project_id} | {entry.created_at:%Y-%m-%d %H:%M}"
                    )
                    st.write(entry.body)
        else:
            st.info("No entries yet. Create a project and start logging.")

        # --- Recent datasets ---
        st.subheader("Recent Datasets")
        recent_ds = (
            session.query(Dataset)
            .order_by(Dataset.created_at.desc())
            .limit(5)
            .all()
        )
        if recent_ds:
            for ds in recent_ds:
                st.write(f"- **{ds.name}** — {ds.row_count} rows ({ds.source_filename})")
        else:
            st.info("No datasets imported yet.")
    finally:
        session.close()
