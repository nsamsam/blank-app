import json

import numpy as np
import pandas as pd
import streamlit as st

from db.connection import SessionLocal
from models.well import Well
from models.casing_section import CasingSection
from models.casing_design import CasingDesign
from models.ppfg_data import PpfgData


# ------------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------------

def _get_well(well_name: str) -> Well | None:
    session = SessionLocal()
    try:
        return session.query(Well).filter_by(name=well_name).first()
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


def _load_design(section_id: int) -> CasingDesign | None:
    session = SessionLocal()
    try:
        return session.query(CasingDesign).filter_by(section_id=section_id).first()
    finally:
        session.close()


def _load_ppfg_arrays(well_id: int):
    """Return (tvd_arr, pp_arr, fg_arr) from the PPFG data."""
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

    sample = rows[0] if rows else {}
    tvd_key = pp_key = fg_key = None
    for k in sample.keys():
        kl = k.strip().lower()
        if kl == "tvd":
            tvd_key = k
        elif kl == "pp":
            pp_key = k
        elif "frac" in kl and "grad" in kl:
            fg_key = k

    if tvd_key is None:
        tvd_key = "TVD" if "TVD" in cols else None
    if pp_key is None:
        pp_key = "PP" if "PP" in cols else None
    if fg_key is None:
        fg_key = "Frac Grad" if "Frac Grad" in cols else None
    if tvd_key is None:
        return None, None, None

    tvd_list, pp_list, fg_list = [], [], []
    for row in rows:
        try:
            tvd_val = float(row.get(tvd_key))
        except (TypeError, ValueError):
            continue
        tvd_list.append(tvd_val)
        try:
            pp_list.append(float(row.get(pp_key)) if pp_key else np.nan)
        except (TypeError, ValueError):
            pp_list.append(np.nan)
        try:
            fg_list.append(float(row.get(fg_key)) if fg_key else np.nan)
        except (TypeError, ValueError):
            fg_list.append(np.nan)

    if len(tvd_list) < 2:
        return None, None, None
    return np.array(tvd_list), np.array(pp_list), np.array(fg_list)


def _interp_at_tvd(target_tvd: float, tvd_arr, val_arr) -> float | None:
    if tvd_arr is None or val_arr is None:
        return None
    mask = ~np.isnan(val_arr)
    tvd_v = tvd_arr[mask]
    val_v = val_arr[mask]
    if len(tvd_v) < 2:
        return None
    order = np.argsort(tvd_v)
    tvd_v = tvd_v[order]
    val_v = val_v[order]
    return float(np.interp(target_tvd, tvd_v, val_v))


# ------------------------------------------------------------------
# Calculation helpers
# ------------------------------------------------------------------

def _f(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _fmt(val, decimals=1, commas=False):
    """Format a float or return '—'."""
    if val is None:
        return "—"
    if commas:
        return f"{val:,.{decimals}f}"
    return f"{val:.{decimals}f}"


def _calc_collapse_from_design(d: CasingDesign, shoe_tvd: float | None):
    rho_d = _f(d.rho_displace)
    rho_t = _f(d.rho_tail)
    tvd_t = _f(d.tvd_tail)
    rho_l = _f(d.rho_lead)
    tvd_l = _f(d.tvd_lead)
    tvd_s = _f(d.tvd_sw)
    if None in (rho_d, shoe_tvd):
        return None, None, None
    p_int = rho_d * 0.052 * shoe_tvd
    if None in (rho_t, tvd_t, rho_l, tvd_l, tvd_s):
        return p_int, None, None
    p_ext = (0.052 * rho_t * tvd_t) + (0.052 * rho_l * tvd_l) + (0.052 * rho_d * tvd_s)
    return p_int, p_ext, p_ext - p_int


def _calc_burst_from_design(d: CasingDesign, shoe_tvd: float | None):
    emw = _f(d.burst_emw)
    backup = _f(d.backup_emw)
    if None in (emw, backup, shoe_tvd):
        return None, None, None
    p_int = 0.052 * emw * shoe_tvd
    p_ext = 0.052 * backup * shoe_tvd
    return p_int, p_ext, p_int - p_ext


def _calc_tension_from_design(d: CasingDesign, csg_wt, shoe_md, top_md, mud_wt):
    overpull = _f(d.overpull)
    if None in (csg_wt, shoe_md, top_md, mud_wt, overpull):
        return None
    length = shoe_md - top_md
    if length <= 0:
        return None
    bf = (65.5 - mud_wt) / 65.5
    return csg_wt * length * bf + overpull


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------

def render(well_name: str = "Well 1"):
    well = _get_well(well_name)
    if well is None:
        st.warning("Well not found.")
        return

    st.subheader("Casing Design Report")

    sections = _load_sections(well.id)
    if not sections:
        st.info("No casing sections defined. Go to the **Well Sections** tab first.")
        return

    ppfg_tvd, ppfg_pp, ppfg_fg = _load_ppfg_arrays(well.id)

    # -------------------------------------------------------------------
    # Report header
    # -------------------------------------------------------------------
    st.markdown("---")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.markdown(f"**Well:** {well.name}")
        st.markdown(f"**Block:** {well.block or '—'}")
    with h2:
        st.markdown(f"**Rig:** {well.rig or '—'}")
        st.markdown(f"**Lease:** {well.lease or '—'}")
    with h3:
        st.markdown(f"**Date:** {well.date or '—'}")
        st.markdown(f"**Water Depth:** {well.water_depth or '—'} ft")
    with h4:
        st.markdown(f"**Rev:** {well.rev or '—'}")
    st.markdown("---")

    # -------------------------------------------------------------------
    # Summary table — all sections side by side
    # -------------------------------------------------------------------
    st.markdown("### Casing Summary")

    rows = []
    for sec in sections:
        design = _load_design(sec.id)
        shoe_tvd = _f(sec.shoe_tvd)
        shoe_md = _f(sec.shoe_md)
        top_tvd = _f(sec.top_tvd)
        top_md = _f(sec.top_md)
        mud_wt = _f(sec.mud_weight)
        csg_wt = _f(sec.casing_weight)
        collapse_r = _f(sec.collapse_rating)
        burst_r = _f(sec.burst_rating)
        tension_r = _f(sec.tension_rating)

        # PPFG lookups
        pp = _interp_at_tvd(shoe_tvd, ppfg_tvd, ppfg_pp) if shoe_tvd else None
        fg = _interp_at_tvd(shoe_tvd, ppfg_tvd, ppfg_fg) if shoe_tvd else None

        # Use design TOC, else section TOC
        toc = None
        if design:
            toc = _f(design.toc)
        if toc is None:
            toc = _f(sec.toc)
        cement_len = (shoe_tvd - toc) if shoe_tvd and toc else None

        # Loads & safety factors
        c_load = b_load = t_load = None
        c_sf = b_sf = t_sf = None
        if design:
            _, _, c_load = _calc_collapse_from_design(design, shoe_tvd)
            _, _, b_load = _calc_burst_from_design(design, shoe_tvd)
            t_load = _calc_tension_from_design(design, csg_wt, shoe_md, top_md, mud_wt)
            c_sf = (collapse_r / c_load) if collapse_r and c_load and c_load != 0 else None
            b_sf = (burst_r / b_load) if burst_r and b_load and b_load != 0 else None
            t_sf = (tension_r / t_load) if tension_r and t_load and t_load != 0 else None

        csg_length = (shoe_md - top_md) if shoe_md and top_md else None

        rows.append({
            "Section": sec.section_name or f"Section {sec.order_index + 1}",
            "Hole Size (in)": sec.hole_size or "—",
            "Casing OD (in)": sec.casing_od or "—",
            "Wt (ppf)": sec.casing_weight or "—",
            "Grade": sec.casing_grade or "—",
            "Thread": sec.thread or "—",
            "Top TVD (ft)": _fmt(top_tvd, 0),
            "Shoe TVD (ft)": _fmt(shoe_tvd, 0),
            "Top MD (ft)": _fmt(top_md, 0),
            "Shoe MD (ft)": _fmt(shoe_md, 0),
            "Length (ft)": _fmt(csg_length, 0, commas=True),
            "Mud Wt (ppg)": _fmt(mud_wt, 1),
            "Shoe PP (ppg)": _fmt(pp, 2),
            "Shoe FG (ppg)": _fmt(fg, 2),
            "TOC (ft)": _fmt(toc, 0),
            "Cement (ft)": _fmt(cement_len, 0),
        })

    df_summary = pd.DataFrame(rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------
    # Ratings & Loads table
    # -------------------------------------------------------------------
    st.markdown("### Ratings & Design Loads")

    load_rows = []
    for sec in sections:
        design = _load_design(sec.id)
        shoe_tvd = _f(sec.shoe_tvd)
        shoe_md = _f(sec.shoe_md)
        top_md = _f(sec.top_md)
        mud_wt = _f(sec.mud_weight)
        csg_wt = _f(sec.casing_weight)
        collapse_r = _f(sec.collapse_rating)
        burst_r = _f(sec.burst_rating)
        tension_r = _f(sec.tension_rating)

        c_load = b_load = t_load = None
        c_sf = b_sf = t_sf = None
        if design:
            _, _, c_load = _calc_collapse_from_design(design, shoe_tvd)
            _, _, b_load = _calc_burst_from_design(design, shoe_tvd)
            t_load = _calc_tension_from_design(design, csg_wt, shoe_md, top_md, mud_wt)
            c_sf = (collapse_r / c_load) if collapse_r and c_load and c_load != 0 else None
            b_sf = (burst_r / b_load) if burst_r and b_load and b_load != 0 else None
            t_sf = (tension_r / t_load) if tension_r and t_load and t_load != 0 else None

        load_rows.append({
            "Section": sec.section_name or f"Section {sec.order_index + 1}",
            "Collapse Rating (psi)": _fmt(collapse_r, 0, commas=True),
            "Collapse Load (psi)": _fmt(c_load, 0, commas=True),
            "Collapse SF": _fmt(c_sf, 2),
            "Burst Rating (psi)": _fmt(burst_r, 0, commas=True),
            "Burst Load (psi)": _fmt(b_load, 0, commas=True),
            "Burst SF": _fmt(b_sf, 2),
            "Tension Rating (lbs)": _fmt(tension_r, 0, commas=True),
            "Tension Load (lbs)": _fmt(t_load, 0, commas=True),
            "Tension SF": _fmt(t_sf, 2),
        })

    df_loads = pd.DataFrame(load_rows)
    st.dataframe(df_loads, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------
    # Safety factor highlights
    # -------------------------------------------------------------------
    st.markdown("### Safety Factor Summary")
    cols = st.columns(len(sections))
    for col, sec, lr in zip(cols, sections, load_rows):
        name = sec.section_name or f"Section {sec.order_index + 1}"
        with col:
            st.markdown(f"**{name}**")
            c_val = _f(lr["Collapse SF"])
            b_val = _f(lr["Burst SF"])
            t_val = _f(lr["Tension SF"])

            if c_val is not None:
                status = "Pass" if c_val >= 1.0 else "**FAIL**"
                st.markdown(f"Collapse: {c_val:.2f} — {status}")
            else:
                st.markdown("Collapse: —")

            if b_val is not None:
                status = "Pass" if b_val >= 1.0 else "**FAIL**"
                st.markdown(f"Burst: {b_val:.2f} — {status}")
            else:
                st.markdown("Burst: —")

            if t_val is not None:
                status = "Pass" if t_val >= 1.0 else "**FAIL**"
                st.markdown(f"Tension: {t_val:.2f} — {status}")
            else:
                st.markdown("Tension: —")
