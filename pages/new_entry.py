import streamlit as st
from db.connection import SessionLocal
from models.well import Well
from models.casing_section import CasingSection
from models.casing_design import CasingDesign

# Design fields stored on CasingDesign
_DESIGN_FIELDS = [
    "shoe_pp", "shoe_mw", "shoe_fg", "toc",
    "rho_displace", "rho_tail", "tvd_tail", "rho_lead", "tvd_lead", "tvd_sw",
    "burst_emw", "backup_emw", "overpull",
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


def _get_or_create_design(section_id: int) -> CasingDesign:
    session = SessionLocal()
    try:
        design = session.query(CasingDesign).filter_by(section_id=section_id).first()
        if not design:
            design = CasingDesign(section_id=section_id, overpull="250000")
            session.add(design)
            session.commit()
            # Re-query to get a detached copy with an id
            design = session.query(CasingDesign).filter_by(section_id=section_id).first()
        return design
    finally:
        session.close()


def _save_design(design_id: int, prefix: str):
    session = SessionLocal()
    try:
        design = session.query(CasingDesign).get(design_id)
        if not design:
            return
        for col in _DESIGN_FIELDS:
            design.__setattr__(col, st.session_state.get(f"{prefix}_{col}", ""))
        session.commit()
    finally:
        session.close()
    st.toast("Saved!")


# ------------------------------------------------------------------
# Calculation helpers
# ------------------------------------------------------------------

def _f(val) -> float | None:
    """Parse a string to float, returning None on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _calc_collapse(prefix: str, shoe_tvd: float | None):
    """Return (p_internal, p_external, collapse_load) or Nones."""
    rho_d = _f(st.session_state.get(f"{prefix}_rho_displace"))
    rho_t = _f(st.session_state.get(f"{prefix}_rho_tail"))
    tvd_t = _f(st.session_state.get(f"{prefix}_tvd_tail"))
    rho_l = _f(st.session_state.get(f"{prefix}_rho_lead"))
    tvd_l = _f(st.session_state.get(f"{prefix}_tvd_lead"))
    tvd_s = _f(st.session_state.get(f"{prefix}_tvd_sw"))

    if None in (rho_d, shoe_tvd):
        return None, None, None

    p_internal = rho_d * 0.052 * shoe_tvd

    if None in (rho_t, tvd_t, rho_l, tvd_l, tvd_s):
        return p_internal, None, None

    p_external = (0.052 * rho_t * tvd_t) + (0.052 * rho_l * tvd_l) + (0.052 * rho_d * tvd_s)
    collapse_load = p_external - p_internal
    return p_internal, p_external, collapse_load


def _calc_burst(prefix: str, shoe_tvd: float | None):
    """Return (p_internal, p_external, burst_load) or Nones."""
    emw = _f(st.session_state.get(f"{prefix}_burst_emw"))
    backup = _f(st.session_state.get(f"{prefix}_backup_emw"))

    if None in (emw, backup, shoe_tvd):
        return None, None, None

    p_internal = 0.052 * emw * shoe_tvd
    p_external = 0.052 * backup * shoe_tvd
    burst_load = p_internal - p_external
    return p_internal, p_external, burst_load


def _calc_tension(prefix: str, csg_wt: float | None, shoe_md: float | None,
                  top_md: float | None, mud_wt: float | None):
    """Return tension_load or None."""
    overpull = _f(st.session_state.get(f"{prefix}_overpull"))

    if None in (csg_wt, shoe_md, top_md, mud_wt, overpull):
        return None

    length = shoe_md - top_md
    if length <= 0:
        return None

    buoyancy_factor = (65.5 - mud_wt) / 65.5
    buoyed_weight = csg_wt * length * buoyancy_factor
    return buoyed_weight + overpull


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------

def render(well_name: str = "Well 1"):
    well_id = _get_well_id(well_name)
    if well_id is None:
        st.warning("Well not found.")
        return

    st.subheader("Casing Design Check")

    sections = _load_sections(well_id)
    if not sections:
        st.info("No casing sections defined. Go to the **Well Sections** tab first.")
        return

    # --- Section selector ---
    section = st.selectbox(
        "Select Casing Section",
        sections,
        format_func=lambda s: s.section_name or f"Section {s.order_index + 1}",
        key="cd_section_select",
    )

    design = _get_or_create_design(section.id)
    prefix = f"cd_{design.id}"
    init_key = f"{prefix}_loaded"

    # Initialize session state from DB
    if not st.session_state.get(init_key):
        for col in _DESIGN_FIELDS:
            st.session_state[f"{prefix}_{col}"] = getattr(design, col, None) or ""
        st.session_state[init_key] = True

    save = lambda: _save_design(design.id, prefix)

    # Pull values from the casing section
    csg_od = section.casing_od or ""
    csg_wt_str = section.casing_weight or ""
    csg_grade = section.casing_grade or ""
    csg_thread = section.thread or ""
    shoe_tvd_val = _f(section.shoe_tvd)
    shoe_md_val = _f(section.shoe_md)
    top_tvd_val = _f(section.top_tvd)
    top_md_val = _f(section.top_md)
    mud_wt_val = _f(section.mud_weight)
    csg_wt_val = _f(csg_wt_str)
    collapse_rating = _f(section.collapse_rating)
    burst_rating = _f(section.burst_rating)
    tension_rating = _f(section.tension_rating)

    # === 1. CASING PROPERTIES (read-only, from Well Sections) ===
    with st.expander("Casing Properties", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        _h = "From Well Sections"
        with c1:
            st.text_input("Size (in)", value=csg_od, disabled=True, help=_h)
            st.text_input("Collapse Rating (psi)", value=section.collapse_rating or "", disabled=True, help=_h)
        with c2:
            st.text_input("Weight (ppf)", value=csg_wt_str, disabled=True, help=_h)
            st.text_input("Burst Rating (psi)", value=section.burst_rating or "", disabled=True, help=_h)
        with c3:
            st.text_input("Grade", value=csg_grade, disabled=True, help=_h)
            st.text_input("Tension Rating (lbs)", value=section.tension_rating or "", disabled=True, help=_h)
        with c4:
            st.text_input("Thread / Connection", value=csg_thread, disabled=True, help=_h)

    # === 2. DEPTH & PRESSURE DATA ===
    with st.expander("Depth & Pressure Data", expanded=True):
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.text_input("Bottom TVD (ft)", value=f"{shoe_tvd_val:.1f}" if shoe_tvd_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input("Shoe PP (ppg)", key=f"{prefix}_shoe_pp", on_change=save)
        with d2:
            st.text_input("Bottom MD (ft)", value=f"{shoe_md_val:.1f}" if shoe_md_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input("Shoe MW (ppg)", key=f"{prefix}_shoe_mw", on_change=save)
        with d3:
            st.text_input("Top TVD (ft)", value=f"{top_tvd_val:.1f}" if top_tvd_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input("Shoe FG (ppg)", key=f"{prefix}_shoe_fg", on_change=save)
        with d4:
            st.text_input("Top MD (ft)", value=f"{top_md_val:.1f}" if top_md_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input("TOC (ft)", key=f"{prefix}_toc", on_change=save)

    # === 3. COLLAPSE ===
    with st.expander("Collapse", expanded=True):
        st.markdown("**Inputs**")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.text_input("Displacing Fluid (ppg)", key=f"{prefix}_rho_displace", on_change=save,
                          help="Seawater or displacement fluid density")
            st.text_input("Tail Cement (ppg)", key=f"{prefix}_rho_tail", on_change=save)
        with cc2:
            st.text_input("Lead Cement (ppg)", key=f"{prefix}_rho_lead", on_change=save)
            st.text_input("Tail Cement Interval (ft)", key=f"{prefix}_tvd_tail", on_change=save)
        with cc3:
            st.text_input("Lead Cement Interval (ft)", key=f"{prefix}_tvd_lead", on_change=save)
            st.text_input("SW / Mud Interval (ft)", key=f"{prefix}_tvd_sw", on_change=save,
                          help="TVD of seawater/mud column above cement")

        st.divider()
        st.markdown("**Results**")
        p_int, p_ext, c_load = _calc_collapse(prefix, shoe_tvd_val)
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("P internal (psi)", f"{p_int:,.0f}" if p_int is not None else "—")
        with r2:
            st.metric("P external (psi)", f"{p_ext:,.0f}" if p_ext is not None else "—")
        with r3:
            st.metric("Collapse Load (psi)", f"{c_load:,.0f}" if c_load is not None else "—")

    # === 4. BURST ===
    with st.expander("Burst", expanded=True):
        st.markdown("**Inputs**")
        b1, b2 = st.columns(2)
        with b1:
            st.text_input("Applied EMW (ppg)", key=f"{prefix}_burst_emw", on_change=save,
                          help="Internal pressure equivalent mud weight")
        with b2:
            st.text_input("Formation Backup EMW (ppg)", key=f"{prefix}_backup_emw", on_change=save,
                          help="External formation pressure equivalent mud weight")

        st.divider()
        st.markdown("**Results**")
        bp_int, bp_ext, b_load = _calc_burst(prefix, shoe_tvd_val)
        br1, br2, br3 = st.columns(3)
        with br1:
            st.metric("P internal (psi)", f"{bp_int:,.0f}" if bp_int is not None else "—")
        with br2:
            st.metric("P external (psi)", f"{bp_ext:,.0f}" if bp_ext is not None else "—")
        with br3:
            st.metric("Burst Load (psi)", f"{b_load:,.0f}" if b_load is not None else "—")

    # === 5. TENSION ===
    with st.expander("Tension", expanded=True):
        st.markdown("**Inputs**")
        t1, t2 = st.columns(2)
        with t1:
            st.text_input("Mud Weight (ppg)",
                          value=f"{mud_wt_val}" if mud_wt_val else "",
                          disabled=True, help="From Well Sections")
        with t2:
            st.text_input("Overpull (lbs)", key=f"{prefix}_overpull", on_change=save)

        st.divider()
        st.markdown("**Results**")
        t_load = _calc_tension(prefix, csg_wt_val, shoe_md_val, top_md_val, mud_wt_val)

        length = (shoe_md_val - top_md_val) if shoe_md_val and top_md_val else None
        bf = ((65.5 - mud_wt_val) / 65.5) if mud_wt_val else None

        tr1, tr2, tr3 = st.columns(3)
        with tr1:
            st.metric("Casing Length (ft)", f"{length:,.0f}" if length else "—")
        with tr2:
            st.metric("Buoyancy Factor", f"{bf:.4f}" if bf else "—")
        with tr3:
            st.metric("Tension Load (lbs)", f"{t_load:,.0f}" if t_load is not None else "—")

    # === 6. SAFETY FACTORS ===
    _, _, c_load = _calc_collapse(prefix, shoe_tvd_val)
    _, _, b_load = _calc_burst(prefix, shoe_tvd_val)
    t_load = _calc_tension(prefix, csg_wt_val, shoe_md_val, top_md_val, mud_wt_val)

    collapse_sf = (collapse_rating / c_load) if collapse_rating and c_load and c_load != 0 else None
    burst_sf = (burst_rating / b_load) if burst_rating and b_load and b_load != 0 else None
    tension_sf = (tension_rating / t_load) if tension_rating and t_load and t_load != 0 else None

    with st.expander("Safety Factors", expanded=True):
        sf1, sf2, sf3 = st.columns(3)
        with sf1:
            val = f"{collapse_sf:.2f}" if collapse_sf is not None else "—"
            st.metric("Collapse SF", val)
        with sf2:
            val = f"{burst_sf:.2f}" if burst_sf is not None else "—"
            st.metric("Burst SF", val)
        with sf3:
            val = f"{tension_sf:.2f}" if tension_sf is not None else "—"
            st.metric("Tension SF", val)
