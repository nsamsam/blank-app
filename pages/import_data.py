import json
import streamlit as st
import pandas as pd
from db.connection import SessionLocal
from models.workbook import Project
from models.dataset import Dataset


def render():
    st.title("Import Data")

    session = SessionLocal()
    try:
        projects = session.query(Project).order_by(Project.name).all()
        if not projects:
            st.warning("Create a project first before importing data.")
            return

        tab_upload, tab_browse = st.tabs(["Upload", "Saved Datasets"])

        # ==================================================================
        # TAB: Upload
        # ==================================================================
        with tab_upload:
            project = st.selectbox(
                "Project", projects, format_func=lambda p: p.name, key="import_proj"
            )
            uploaded = st.file_uploader(
                "Upload CSV or Excel file",
                type=["csv", "xlsx", "xls"],
                key="import_file",
            )

            if uploaded is not None:
                # Parse the file
                try:
                    if uploaded.name.endswith(".csv"):
                        df = pd.read_csv(uploaded)
                    else:
                        df = pd.read_excel(uploaded)
                except Exception as e:
                    st.error(f"Could not read file: {e}")
                    return

                st.subheader("Preview")
                st.dataframe(df.head(20), use_container_width=True)
                st.caption(f"{len(df)} rows, {len(df.columns)} columns")

                dataset_name = st.text_input(
                    "Dataset name", value=uploaded.name, key="import_name"
                )
                description = st.text_area(
                    "Description (optional)", key="import_desc", height=80
                )

                if st.button("Save to Database", type="primary"):
                    if not dataset_name.strip():
                        st.error("Give the dataset a name.")
                        return

                    dataset = Dataset(
                        project_id=project.id,
                        name=dataset_name.strip(),
                        description=description,
                        source_filename=uploaded.name,
                        columns_json=json.dumps(list(df.columns)),
                        data_json=df.to_json(orient="records", date_format="iso"),
                        row_count=len(df),
                    )
                    session.add(dataset)
                    session.commit()
                    st.success(
                        f"Dataset '{dataset_name}' saved — {len(df)} rows, {len(df.columns)} columns."
                    )

        # ==================================================================
        # TAB: Browse saved datasets
        # ==================================================================
        with tab_browse:
            filter_proj = st.selectbox(
                "Filter by project",
                [None] + projects,
                format_func=lambda p: "All" if p is None else p.name,
                key="ds_filter",
            )
            query = session.query(Dataset).order_by(Dataset.created_at.desc())
            if filter_proj:
                query = query.filter(Dataset.project_id == filter_proj.id)
            datasets = query.limit(50).all()

            if not datasets:
                st.info("No datasets imported yet.")

            for ds in datasets:
                with st.expander(f"{ds.name}  —  {ds.row_count} rows"):
                    st.caption(
                        f"Source: {ds.source_filename} | Imported {ds.created_at:%Y-%m-%d %H:%M}"
                    )
                    if ds.description:
                        st.write(ds.description)

                    # Reconstruct dataframe for display
                    try:
                        cols = json.loads(ds.columns_json)
                        rows = json.loads(ds.data_json)
                        df = pd.DataFrame(rows, columns=cols)
                        st.dataframe(df.head(50), use_container_width=True)
                        if len(df) > 50:
                            st.caption(f"Showing first 50 of {len(df)} rows.")

                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "Download CSV",
                            csv,
                            file_name=f"{ds.name}.csv",
                            mime="text/csv",
                            key=f"dl_{ds.id}",
                        )
                    except Exception as e:
                        st.error(f"Could not load data: {e}")

                    if st.button(f"Delete", key=f"dsdel_{ds.id}"):
                        session.delete(ds)
                        session.commit()
                        st.rerun()
    finally:
        session.close()
