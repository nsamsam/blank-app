import json

import numpy as np
import streamlit as st

from db.connection import SessionLocal
from models.well import Well
from models.casing_section import CasingSection
from models.casing_design import CasingDesign
from models.ppfg_data import PpfgData

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
            design = CasingDesign(section_id=section_id, overpull="250000", rho_displace="8.6")
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
# PPFG interpolation helpers
# ------------------------------------------------------------------

def _load_ppfg_arrays(well_id: int):
    """Return (tvd_arr, pp_arr, fg_arr) from the PPFG data, or (None, None, None)."""
    session = SessionLocal()
    try:
        rec = session.query(PpfgData).filter_by(well_id=well_id).first()
        if not rec:
            return None, None, None
        cols = json.loads(rec.columns_json)
        rows = json.loads(rec.data_json)
    finally:
        session.close()

    if not rows:
        return None, None, None

    # Find column keys — scan the saved column list first (authoritative),
    # then fall back to row-dict keys for resilience.
    tvd_key = pp_key = fg_key = None

    # Scan the columns_json list (saved from df.columns)
    for c in cols:
        cl = c.strip().lower()
        if cl == "tvd" and tvd_key is None:
            tvd_key = c
        elif (cl == "pp" or "pore" in cl) and pp_key is None:
            pp_key = c
        elif "frac" in cl and "grad" in cl and fg_key is None:
            fg_key = c

    # Also scan row-dict keys in case columns_json diverged
    if rows:
        for k in rows[0].keys():
            kl = k.strip().lower()
            if tvd_key is None and kl == "tvd":
                tvd_key = k
            if pp_key is None and (kl == "pp" or "pore" in kl):
                pp_key = k
            if fg_key is None and "frac" in kl and "grad" in kl:
                fg_key = k

    if tvd_key is None:
        return None, None, None

    tvd_list, pp_list, fg_list = [], [], []
    for row in rows:
        try:
            tvd_val = float(row.get(tvd_key))
        except (TypeError, ValueError):
            continue
        tvd_list.append(tvd_val)

        # PP — may be absent
        try:
            pp_list.append(float(row.get(pp_key)) if pp_key else np.nan)
        except (TypeError, ValueError):
            pp_list.append(np.nan)

        # FG — may be absent
        try:
            fg_list.append(float(row.get(fg_key)) if fg_key else np.nan)
        except (TypeError, ValueError):
            fg_list.append(np.nan)

    if len(tvd_list) < 2:
        return None, None, None

    return np.array(tvd_list), np.array(pp_list), np.array(fg_list)


def _interp_at_tvd(target_tvd: float, tvd_arr, val_arr) -> float | None:
    """Linearly interpolate a value at target_tvd from sorted survey arrays."""
    if tvd_arr is None or val_arr is None:
        return None

    # Build valid (non-NaN) pairs
    mask = ~np.isnan(val_arr)
    tvd_v = tvd_arr[mask]
    val_v = val_arr[mask]
    if len(tvd_v) < 2:
        return None

    # Sort by TVD
    order = np.argsort(tvd_v)
    tvd_v = tvd_v[order]
    val_v = val_v[order]

    # Clamp to range (extrapolate from nearest segment)
    if target_tvd <= tvd_v[0]:
        if len(tvd_v) >= 2 and tvd_v[1] != tvd_v[0]:
            return float(val_v[0] + (target_tvd - tvd_v[0]) / (tvd_v[1] - tvd_v[0]) * (val_v[1] - val_v[0]))
        return float(val_v[0])
    if target_tvd >= tvd_v[-1]:
        if len(tvd_v) >= 2 and tvd_v[-1] != tvd_v[-2]:
            return float(val_v[-2] + (target_tvd - tvd_v[-2]) / (tvd_v[-1] - tvd_v[-2]) * (val_v[-1] - val_v[-2]))
        return float(val_v[-1])

    # Normal interpolation
    return float(np.interp(target_tvd, tvd_v, val_v))


# ------------------------------------------------------------------
# Calculation helpers
# ------------------------------------------------------------------

def _f(val) -> float | None:
    """Parse a string to float, returning None on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _v(val, decimals=2, commas=False):
    """Format a float for formula display, or '?' if None."""
    if val is None:
        return "?"
    if commas:
        return f"{val:,.{decimals}f}"
    return f"{val:.{decimals}f}"


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

    # Pre-load PPFG data for PP / FG interpolation
    ppfg_tvd, ppfg_pp, ppfg_fg = _load_ppfg_arrays(well_id)
    has_ppfg = ppfg_tvd is not None

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

    # --- Auto-fill Shoe PP, Shoe FG from PPFG, and TOC from Well Sections ---
    if shoe_tvd_val is not None and has_ppfg:
        pp_val = _interp_at_tvd(shoe_tvd_val, ppfg_tvd, ppfg_pp)
        if pp_val is not None:
            st.session_state[f"{prefix}_shoe_pp"] = f"{pp_val:.2f}"
        fg_val = _interp_at_tvd(shoe_tvd_val, ppfg_tvd, ppfg_fg)
        if fg_val is not None:
            st.session_state[f"{prefix}_shoe_fg"] = f"{fg_val:.2f}"

    # Auto-fill TOC from well sections
    section_toc = section.toc or ""
    if section_toc:
        st.session_state[f"{prefix}_toc"] = section_toc

    # Auto-compute Lead Cement Interval = TOC − Tail Cement Interval
    toc_val = _f(st.session_state.get(f"{prefix}_toc"))
    tvd_tail_val = _f(st.session_state.get(f"{prefix}_tvd_tail"))
    if toc_val is not None and tvd_tail_val is not None:
        lead_interval = toc_val - tvd_tail_val
        st.session_state[f"{prefix}_tvd_lead"] = f"{lead_interval:.1f}"

    # Persist auto-filled values
    _save_design_quiet(design.id, prefix)

    # === SINGLE EXPANDER FOR ALL DESIGN DATA ===
    section_label = section.section_name or f"Section {section.order_index + 1}"
    with st.expander(f"{section_label} — Design Check", expanded=True):

        # --- Casing Properties (read-only from Well Sections) ---
        st.markdown("**Casing Properties**")
        _h = "From Well Sections"
        c1, c2, c3, c4 = st.columns(4)
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

        st.divider()

        # --- Depth & Pressure Data ---
        st.markdown("**Depth & Pressure Data**")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.text_input("Bottom TVD (ft)", value=f"{shoe_tvd_val:.1f}" if shoe_tvd_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input(
                "Shoe PP (ppg)", key=f"{prefix}_shoe_pp", on_change=save,
                help="Auto-filled from PPFG data (editable)" if has_ppfg else "Enter manually or load PPFG data",
            )
        with d2:
            st.text_input("Bottom MD (ft)", value=f"{shoe_md_val:.1f}" if shoe_md_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input("Shoe MW (ppg)", key=f"{prefix}_shoe_mw", on_change=save)
        with d3:
            st.text_input("Top TVD (ft)", value=f"{top_tvd_val:.1f}" if top_tvd_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input(
                "Shoe FG (ppg)", key=f"{prefix}_shoe_fg", on_change=save,
                disabled=has_ppfg and shoe_tvd_val is not None,
                help="Auto from PPFG data" if has_ppfg else "Enter manually or load PPFG data",
            )
        with d4:
            st.text_input("Top MD (ft)", value=f"{top_md_val:.1f}" if top_md_val else "",
                          disabled=True, help="From Well Sections")
            st.text_input("TOC (ft)", key=f"{prefix}_toc", on_change=save,
                          disabled=bool(section_toc),
                          help="Auto from Well Sections" if section_toc else "Enter manually or set in Well Sections")

        if not has_ppfg:
            st.caption("Load PPFG data in the **PPFG** tab to auto-fill Shoe PP and Shoe FG.")

        st.divider()

        # --- Collapse ---
        st.markdown("**Collapse**")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.text_input("SW Density (ppg)", key=f"{prefix}_rho_displace", on_change=save,
                          help="Seawater density (default 8.6)")
            st.text_input("Tail Cement (ppg)", key=f"{prefix}_rho_tail", on_change=save)
        with cc2:
            st.text_input("Lead Cement (ppg)", key=f"{prefix}_rho_lead", on_change=save)
            st.text_input("Tail Cement Interval (ft)", key=f"{prefix}_tvd_tail", on_change=save)
        with cc3:
            st.text_input("Lead Cement Interval (ft)", key=f"{prefix}_tvd_lead",
                          disabled=True, help="Auto: TOC − Tail Cement Interval")
            st.text_input("SW / Mud Interval (ft)", key=f"{prefix}_tvd_sw", on_change=save,
                          help="TVD of seawater/mud column above cement")

        # Collapse formula breakdown
        p_int, p_ext, c_load = _calc_collapse(prefix, shoe_tvd_val)
        rho_d = _f(st.session_state.get(f"{prefix}_rho_displace"))
        rho_t = _f(st.session_state.get(f"{prefix}_rho_tail"))
        tvd_t = _f(st.session_state.get(f"{prefix}_tvd_tail"))
        rho_l = _f(st.session_state.get(f"{prefix}_rho_lead"))
        tvd_l = _f(st.session_state.get(f"{prefix}_tvd_lead"))
        tvd_s = _f(st.session_state.get(f"{prefix}_tvd_sw"))

        st.markdown("**Calculations**")
        lines = []
        lines.append(f"P internal  = ρ_SW × 0.052 × Shoe TVD")
        lines.append(f"            = {_v(rho_d)} × 0.052 × {_v(shoe_tvd_val, 1)}")
        lines.append(f"            = {_v(p_int, 0, True)} psi")
        lines.append("")
        lines.append(f"P external  = (0.052 × ρ_tail × Tail Int) + (0.052 × ρ_lead × Lead Int) + (0.052 × ρ_SW × SW Int)")
        lines.append(f"            = (0.052 × {_v(rho_t)} × {_v(tvd_t, 1)}) + (0.052 × {_v(rho_l)} × {_v(tvd_l, 1)}) + (0.052 × {_v(rho_d)} × {_v(tvd_s, 1)})")
        if p_ext is not None:
            t1 = 0.052 * rho_t * tvd_t if None not in (rho_t, tvd_t) else None
            t2 = 0.052 * rho_l * tvd_l if None not in (rho_l, tvd_l) else None
            t3 = 0.052 * rho_d * tvd_s if None not in (rho_d, tvd_s) else None
            lines.append(f"            = {_v(t1, 0, True)} + {_v(t2, 0, True)} + {_v(t3, 0, True)}")
        lines.append(f"            = {_v(p_ext, 0, True)} psi")
        lines.append("")
        lines.append(f"Collapse Load = P external − P internal")
        lines.append(f"              = {_v(p_ext, 0, True)} − {_v(p_int, 0, True)}")
        lines.append(f"              = {_v(c_load, 0, True)} psi")
        st.code("\n".join(lines), language=None)

        st.divider()

        # --- Burst ---
        st.markdown("**Burst**")
        b1, b2 = st.columns(2)
        with b1:
            st.text_input("Applied EMW (ppg)", key=f"{prefix}_burst_emw", on_change=save,
                          help="Internal pressure equivalent mud weight")
        with b2:
            st.text_input("Formation Backup EMW (ppg)", key=f"{prefix}_backup_emw", on_change=save,
                          help="External formation pressure equivalent mud weight")

        # Burst formula breakdown
        bp_int, bp_ext, b_load = _calc_burst(prefix, shoe_tvd_val)
        emw = _f(st.session_state.get(f"{prefix}_burst_emw"))
        backup = _f(st.session_state.get(f"{prefix}_backup_emw"))

        st.markdown("**Calculations**")
        lines = []
        lines.append(f"P internal  = 0.052 × Applied EMW × Shoe TVD")
        lines.append(f"            = 0.052 × {_v(emw)} × {_v(shoe_tvd_val, 1)}")
        lines.append(f"            = {_v(bp_int, 0, True)} psi")
        lines.append("")
        lines.append(f"P external  = 0.052 × Backup EMW × Shoe TVD")
        lines.append(f"            = 0.052 × {_v(backup)} × {_v(shoe_tvd_val, 1)}")
        lines.append(f"            = {_v(bp_ext, 0, True)} psi")
        lines.append("")
        lines.append(f"Burst Load  = P internal − P external")
        lines.append(f"            = {_v(bp_int, 0, True)} − {_v(bp_ext, 0, True)}")
        lines.append(f"            = {_v(b_load, 0, True)} psi")
        st.code("\n".join(lines), language=None)

        st.divider()

        # --- Tension ---
        st.markdown("**Tension**")
        t1, t2 = st.columns(2)
        with t1:
            st.text_input("Mud Weight (ppg)",
                          value=f"{mud_wt_val}" if mud_wt_val else "",
                          disabled=True, help="From Well Sections")
        with t2:
            st.text_input("Overpull (lbs)", key=f"{prefix}_overpull", on_change=save)

        # Tension formula breakdown
        t_load = _calc_tension(prefix, csg_wt_val, shoe_md_val, top_md_val, mud_wt_val)
        length = (shoe_md_val - top_md_val) if shoe_md_val and top_md_val else None
        bf = ((65.5 - mud_wt_val) / 65.5) if mud_wt_val else None
        overpull = _f(st.session_state.get(f"{prefix}_overpull"))
        buoyed_wt = (csg_wt_val * length * bf) if None not in (csg_wt_val, length, bf) else None

        st.markdown("**Calculations**")
        lines = []
        lines.append(f"Length          = Shoe MD − Top MD")
        lines.append(f"                = {_v(shoe_md_val, 1)} − {_v(top_md_val, 1)}")
        lines.append(f"                = {_v(length, 0, True)} ft")
        lines.append("")
        lines.append(f"Buoyancy Factor = (65.5 − Mud Wt) / 65.5")
        lines.append(f"                = (65.5 − {_v(mud_wt_val)}) / 65.5")
        lines.append(f"                = {_v(bf, 4)}")
        lines.append("")
        lines.append(f"Tension Load    = Csg Wt × Length × BF + Overpull")
        lines.append(f"                = {_v(csg_wt_val)} × {_v(length, 0, True)} × {_v(bf, 4)} + {_v(overpull, 0, True)}")
        lines.append(f"                = {_v(buoyed_wt, 0, True)} + {_v(overpull, 0, True)}")
        lines.append(f"                = {_v(t_load, 0, True)} lbs")
        st.code("\n".join(lines), language=None)

        st.divider()

        # --- Safety Factors ---
        st.markdown("**Safety Factors**")
        _, _, c_load = _calc_collapse(prefix, shoe_tvd_val)
        _, _, b_load = _calc_burst(prefix, shoe_tvd_val)
        t_load = _calc_tension(prefix, csg_wt_val, shoe_md_val, top_md_val, mud_wt_val)

        collapse_sf = (collapse_rating / c_load) if collapse_rating and c_load and c_load != 0 else None
        burst_sf = (burst_rating / b_load) if burst_rating and b_load and b_load != 0 else None
        tension_sf = (tension_rating / t_load) if tension_rating and t_load and t_load != 0 else None

        lines = []
        lines.append(f"Collapse SF = Collapse Rating / Collapse Load  =  {_v(collapse_rating, 0, True)} / {_v(c_load, 0, True)}  =  {_v(collapse_sf, 2)}")
        lines.append(f"Burst SF    = Burst Rating / Burst Load        =  {_v(burst_rating, 0, True)} / {_v(b_load, 0, True)}  =  {_v(burst_sf, 2)}")
        lines.append(f"Tension SF  = Tension Rating / Tension Load    =  {_v(tension_rating, 0, True)} / {_v(t_load, 0, True)}  =  {_v(tension_sf, 2)}")
        st.code("\n".join(lines), language=None)

        sf1, sf2, sf3 = st.columns(3)
        with sf1:
            st.metric("Collapse SF", f"{collapse_sf:.2f}" if collapse_sf is not None else "—")
        with sf2:
            st.metric("Burst SF", f"{burst_sf:.2f}" if burst_sf is not None else "—")
        with sf3:
            st.metric("Tension SF", f"{tension_sf:.2f}" if tension_sf is not None else "—")


def _save_design_quiet(design_id: int, prefix: str):
    """Save without toast notification (used for auto-fill updates)."""
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
