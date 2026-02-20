import streamlit as st
from db.connection import SessionLocal
from models.well import Well
from models.casing_section import CasingSection

# Default section templates when adding a new row
_DEFAULT_SECTIONS = ["Conductor", "Surface", "Intermediate", "Production", "Liner"]

_FIELDS = [
    ("section_name", "Section Name"),
    ("hole_size", "Hole Size (in)"),
    ("casing_od", "Casing OD (in)"),
    ("casing_weight", "Casing Wt (ppf)"),
    ("casing_grade", "Casing Grade"),
    ("casing_id", "Casing ID (in)"),
    ("top_md", "Top MD (ft)"),
    ("shoe_md", "Shoe MD (ft)"),
    ("mud_weight", "Mud Wt (ppg)"),
]


def _get_well_id(well_name: str) -> int | None:
    session = SessionLocal()
    try:
        well = session.query(Well).filter_by(name=well_name).first()
        return well.id if well else None
    finally:
        session.close()


def _load_sections(well_id: int) -> list[CasingSection]:
    session = SessionLocal()
    try:
        return (
            session.query(CasingSection)
            .filter_by(well_id=well_id)
            .order_by(CasingSection.order_index)
            .all()
        )
    finally:
        session.close()


def _add_section(well_id: int, section_name: str = "", order_index: int = 0):
    session = SessionLocal()
    try:
        section = CasingSection(
            well_id=well_id,
            order_index=order_index,
            section_name=section_name,
        )
        session.add(section)
        session.commit()
    finally:
        session.close()


def _delete_section(section_id: int):
    session = SessionLocal()
    try:
        section = session.query(CasingSection).get(section_id)
        if section:
            session.delete(section)
            session.commit()
    finally:
        session.close()


def _save_section(section_id: int, prefix: str):
    """Persist all field values from session state back to the DB."""
    session = SessionLocal()
    try:
        section = session.query(CasingSection).get(section_id)
        if not section:
            return
        for db_col, _ in _FIELDS:
            val = st.session_state.get(f"{prefix}_{db_col}", "")
            setattr(section, db_col, val)
        session.commit()
    finally:
        session.close()
    st.toast("Saved!")


def render(well_name: str = "Well 1"):
    well_id = _get_well_id(well_name)
    if well_id is None:
        st.warning("Well not found.")
        return

    st.subheader("Well Sections")

    # --- Add section controls ---
    col_add, col_template = st.columns([1, 2])
    with col_add:
        if st.button("+ Add Section", type="primary"):
            existing = _load_sections(well_id)
            next_idx = len(existing)
            # Pick a default name based on position
            default_name = _DEFAULT_SECTIONS[next_idx] if next_idx < len(_DEFAULT_SECTIONS) else ""
            _add_section(well_id, section_name=default_name, order_index=next_idx)
            st.rerun()

    # --- Load and render sections ---
    sections = _load_sections(well_id)

    if not sections:
        st.info("No casing sections yet. Click **+ Add Section** to get started.")
        return

    # Column headers
    hdr_cols = st.columns([1.2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.4])
    headers = [label for _, label in _FIELDS] + [""]
    for col, hdr in zip(hdr_cols, headers):
        col.markdown(f"**{hdr}**")

    st.divider()

    # Render each section as a row of inputs
    for sec in sections:
        prefix = f"cs_{sec.id}"
        # Initialize session state from DB values (once)
        init_key = f"{prefix}_loaded"
        if not st.session_state.get(init_key):
            for db_col, _ in _FIELDS:
                st.session_state[f"{prefix}_{db_col}"] = getattr(sec, db_col, None) or ""
            st.session_state[init_key] = True

        save = lambda sid=sec.id, pfx=prefix: _save_section(sid, pfx)

        row_cols = st.columns([1.2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.4])

        for col, (db_col, label) in zip(row_cols[:-1], _FIELDS):
            with col:
                st.text_input(
                    label,
                    key=f"{prefix}_{db_col}",
                    on_change=save,
                    label_visibility="collapsed",
                )

        with row_cols[-1]:
            if st.button("🗑", key=f"{prefix}_del", help="Delete this section"):
                _delete_section(sec.id)
                # Clear session state for this section
                for db_col, _ in _FIELDS:
                    st.session_state.pop(f"{prefix}_{db_col}", None)
                st.session_state.pop(init_key, None)
                st.rerun()

        st.divider()
