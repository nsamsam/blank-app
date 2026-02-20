import json

import numpy as np
import streamlit as st

from db.connection import SessionLocal
from models.casing_section import CasingSection
from models.directional_data import DirectionalData
from models.well import Well

# Default section templates when adding a new row
_DEFAULT_SECTIONS = ["Conductor", "Surface", "Intermediate", "Production", "Liner"]

# Fields displayed inside each expander (db_col, label)
_GENERAL_FIELDS = [
    ("hole_size", "Hole Size (in)"),
    ("casing_od", "Casing OD (in)"),
    ("casing_weight", "Casing Wt (ppf)"),
    ("casing_grade", "Casing Grade"),
    ("casing_id", "Casing ID (in)"),
    ("mud_weight", "Mud Wt (ppg)"),
]

_RATING_FIELDS = [
    ("collapse_rating", "Collapse Rating (psi)"),
    ("burst_rating", "Burst Rating (psi)"),
    ("tension_rating", "Tension Rating (lbs)"),
    ("thread", "Thread / Connection"),
]

# All fields that get persisted (general + ratings + depth)
_ALL_DB_FIELDS = [f for f, _ in _GENERAL_FIELDS] + [f for f, _ in _RATING_FIELDS] + [
    "section_name", "top_tvd", "top_md", "shoe_tvd", "shoe_md",
]


# ------------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------------

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


def _swap_order(id_a: int, id_b: int):
    """Swap order_index of two sections."""
    session = SessionLocal()
    try:
        a = session.query(CasingSection).get(id_a)
        b = session.query(CasingSection).get(id_b)
        if a and b:
            a.order_index, b.order_index = b.order_index, a.order_index
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
        for db_col in _ALL_DB_FIELDS:
            val = st.session_state.get(f"{prefix}_{db_col}", "")
            setattr(section, db_col, val)
        session.commit()
    finally:
        session.close()
    st.toast("Saved!")


# ------------------------------------------------------------------
# TVD → MD interpolation from directional survey
# ------------------------------------------------------------------

def _load_survey_arrays(well_id: int):
    """Return (md_array, tvd_array) from the directional survey, or (None, None)."""
    session = SessionLocal()
    try:
        rec = session.query(DirectionalData).filter_by(well_id=well_id).first()
        if not rec:
            return None, None
        cols = json.loads(rec.columns_json)
        rows = json.loads(rec.data_json)
    finally:
        session.close()

    if not rows or "MD (ft)" not in cols or "TVD (ft)" not in cols:
        return None, None

    md_list, tvd_list = [], []
    for row in rows:
        md_val = row.get("MD (ft)")
        tvd_val = row.get("TVD (ft)")
        try:
            md_list.append(float(md_val))
            tvd_list.append(float(tvd_val))
        except (TypeError, ValueError):
            continue

    if len(md_list) < 2:
        return None, None

    return np.array(md_list), np.array(tvd_list)


def _tvd_to_md(tvd_value: float, md_arr, tvd_arr) -> float | None:
    """Interpolate MD from TVD by bracketing the target between two survey stations.

    Finds the closest station above (TVD1, MD1) and below (TVD2, MD2) and applies:
        MD = MD1 + (TVD_target - TVD1) / (TVD2 - TVD1) * (MD2 - MD1)
    """
    if md_arr is None or tvd_arr is None or len(md_arr) < 2:
        return None

    n = len(tvd_arr)

    # Exact match
    for i in range(n):
        if tvd_arr[i] == tvd_value:
            return float(md_arr[i])

    # Find the bracketing pair: last station with TVD <= target, first with TVD >= target
    idx_above = None  # station above (shallower TVD)
    idx_below = None  # station below (deeper TVD)

    for i in range(n):
        if tvd_arr[i] <= tvd_value:
            if idx_above is None or tvd_arr[i] >= tvd_arr[idx_above]:
                idx_above = i
        if tvd_arr[i] >= tvd_value:
            if idx_below is None or tvd_arr[i] <= tvd_arr[idx_below]:
                idx_below = i

    if idx_above is None or idx_below is None:
        return None
    if idx_above == idx_below:
        return float(md_arr[idx_above])

    tvd1, md1 = tvd_arr[idx_above], md_arr[idx_above]
    tvd2, md2 = tvd_arr[idx_below], md_arr[idx_below]

    if tvd2 == tvd1:
        return float(md1)

    md_interp = md1 + (tvd_value - tvd1) / (tvd2 - tvd1) * (md2 - md1)
    return float(md_interp)


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------

def render(well_name: str = "Well 1"):
    well_id = _get_well_id(well_name)
    if well_id is None:
        st.warning("Well not found.")
        return

    st.subheader("Well Sections")

    # Pre-load directional survey for TVD→MD interpolation
    md_arr, tvd_arr = _load_survey_arrays(well_id)
    has_survey = md_arr is not None

    if st.button("+ Add Section", type="primary"):
        existing = _load_sections(well_id)
        next_idx = len(existing)
        default_name = _DEFAULT_SECTIONS[next_idx] if next_idx < len(_DEFAULT_SECTIONS) else ""
        _add_section(well_id, section_name=default_name, order_index=next_idx)
        st.rerun()

    sections = _load_sections(well_id)

    if not sections:
        st.info("No casing sections yet. Click **+ Add Section** to get started.")
        return

    for idx, sec in enumerate(sections):
        prefix = f"cs_{sec.id}"
        init_key = f"{prefix}_loaded"

        # Initialize session state from DB values once
        if not st.session_state.get(init_key):
            for db_col in _ALL_DB_FIELDS:
                st.session_state[f"{prefix}_{db_col}"] = getattr(sec, db_col, None) or ""
            st.session_state[init_key] = True

        # --- Compute auto-MD from TVD whenever TVD values change ---
        def _recalc_md(sid=sec.id, pfx=prefix):
            for tvd_col, md_col in [("top_tvd", "top_md"), ("shoe_tvd", "shoe_md")]:
                tvd_str = st.session_state.get(f"{pfx}_{tvd_col}", "")
                try:
                    tvd_val = float(tvd_str)
                    md_val = _tvd_to_md(tvd_val, md_arr, tvd_arr)
                    st.session_state[f"{pfx}_{md_col}"] = f"{md_val:.1f}" if md_val is not None else ""
                except (ValueError, TypeError):
                    st.session_state[f"{pfx}_{md_col}"] = ""
            _save_section(sid, pfx)

        save = lambda sid=sec.id, pfx=prefix: _save_section(sid, pfx)

        # Eagerly recompute MD values on each render so they stay current
        for tvd_col, md_col in [("top_tvd", "top_md"), ("shoe_tvd", "shoe_md")]:
            tvd_str = st.session_state.get(f"{prefix}_{tvd_col}", "")
            try:
                tvd_val = float(tvd_str)
                md_val = _tvd_to_md(tvd_val, md_arr, tvd_arr)
                st.session_state[f"{prefix}_{md_col}"] = f"{md_val:.1f}" if md_val is not None else ""
            except (ValueError, TypeError):
                pass

        # --- Section header row: move buttons + expander + delete ---
        section_name = st.session_state.get(f"{prefix}_section_name", "") or f"Section {idx + 1}"
        shoe_tvd_display = st.session_state.get(f"{prefix}_shoe_tvd", "")
        label = f"{section_name}"
        if shoe_tvd_display:
            label += f"  —  Shoe TVD: {shoe_tvd_display} ft"

        btn_col, expand_col = st.columns([0.08, 0.92])

        with btn_col:
            if idx > 0:
                if st.button("▲", key=f"{prefix}_up", help="Move up"):
                    prev = sections[idx - 1]
                    _swap_order(sec.id, prev.id)
                    st.rerun()
            if idx < len(sections) - 1:
                if st.button("▼", key=f"{prefix}_down", help="Move down"):
                    nxt = sections[idx + 1]
                    _swap_order(sec.id, nxt.id)
                    st.rerun()

        with expand_col:
            with st.expander(label):
                # Section name
                st.text_input("Section Name", key=f"{prefix}_section_name", on_change=save)

                # General fields — 3 columns
                st.markdown("**Casing Details**")
                c1, c2, c3 = st.columns(3)
                for i, (db_col, label_text) in enumerate(_GENERAL_FIELDS):
                    with [c1, c2, c3][i % 3]:
                        st.text_input(label_text, key=f"{prefix}_{db_col}", on_change=save)

                st.divider()

                # Rating fields
                st.markdown("**Burst, Collapse & Tension**")
                r1, r2, r3, r4 = st.columns(4)
                for col_w, (db_col, label_text) in zip([r1, r2, r3, r4], _RATING_FIELDS):
                    with col_w:
                        st.text_input(label_text, key=f"{prefix}_{db_col}", on_change=save)

                st.divider()

                # Depth fields — TVD (editable) → MD (auto)
                st.markdown("**Depths**")
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    st.text_input(
                        "Top of Casing TVD (ft)",
                        key=f"{prefix}_top_tvd",
                        on_change=_recalc_md,
                    )
                with d2:
                    st.text_input(
                        "Top MD (ft)",
                        key=f"{prefix}_top_md",
                        disabled=True,
                        help="Auto from directional survey" if has_survey else "No survey loaded",
                    )
                with d3:
                    st.text_input(
                        "Setting Depth TVD (ft)",
                        key=f"{prefix}_shoe_tvd",
                        on_change=_recalc_md,
                    )
                with d4:
                    st.text_input(
                        "Shoe MD (ft)",
                        key=f"{prefix}_shoe_md",
                        disabled=True,
                        help="Auto from directional survey" if has_survey else "No survey loaded",
                    )

                if not has_survey:
                    st.caption("MD values will auto-populate once a directional survey is loaded.")

                # Delete button
                st.divider()
                if st.button("Delete Section", key=f"{prefix}_del", type="secondary"):
                    _delete_section(sec.id)
                    for db_col in _ALL_DB_FIELDS:
                        st.session_state.pop(f"{prefix}_{db_col}", None)
                    st.session_state.pop(init_key, None)
                    st.rerun()
