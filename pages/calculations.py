import json
import streamlit as st
from db.connection import SessionLocal
from models.workbook import Project
from models.calculation import Calculation
from engine.calc import evaluate_formula, formula_to_latex


def render():
    st.title("Engineering Calculations")

    session = SessionLocal()
    try:
        projects = session.query(Project).order_by(Project.name).all()
        if not projects:
            st.warning("Create a project first.")
            return

        tab_new, tab_saved = st.tabs(["New Calculation", "Saved Calculations"])

        # ==================================================================
        # TAB: New Calculation
        # ==================================================================
        with tab_new:
            project = st.selectbox(
                "Project", projects, format_func=lambda p: p.name, key="calc_proj"
            )
            title = st.text_input("Calculation Title", key="calc_title")
            description = st.text_area("Description / context", height=80, key="calc_desc")

            st.subheader("Variables")
            st.caption("Define each variable used in your formula.")

            # Dynamic variable rows stored in session state
            if "calc_vars" not in st.session_state:
                st.session_state.calc_vars = [{"name": "", "value": "", "unit": ""}]

            vars_to_remove = None
            for i, v in enumerate(st.session_state.calc_vars):
                cols = st.columns([2, 2, 2, 1])
                v["name"] = cols[0].text_input("Name", value=v["name"], key=f"vn_{i}")
                v["value"] = cols[1].text_input("Value", value=v["value"], key=f"vv_{i}")
                v["unit"] = cols[2].text_input("Unit", value=v["unit"], key=f"vu_{i}",
                                                placeholder="e.g. kN, m**2, psi")
                if cols[3].button("X", key=f"vdel_{i}"):
                    vars_to_remove = i

            if vars_to_remove is not None:
                st.session_state.calc_vars.pop(vars_to_remove)
                st.rerun()

            if st.button("+ Add Variable"):
                st.session_state.calc_vars.append({"name": "", "value": "", "unit": ""})
                st.rerun()

            st.subheader("Formula")
            st.caption("Use variable names from above. Examples: `F / A`, `sqrt(x**2 + y**2)`, `P * L**3 / (3 * E * I)`")
            formula_str = st.text_input("Formula expression", key="calc_formula")

            # Live LaTeX preview
            if formula_str.strip():
                try:
                    latex = formula_to_latex(formula_str)
                    st.latex(latex)
                except Exception as e:
                    st.error(f"Could not parse formula: {e}")

            # --- Compute ---
            if st.button("Compute", type="primary"):
                if not title or not formula_str.strip():
                    st.error("Title and formula are required.")
                else:
                    variables = {}
                    for v in st.session_state.calc_vars:
                        n = v["name"].strip()
                        if not n:
                            continue
                        try:
                            variables[n] = {
                                "value": float(v["value"]),
                                "unit": v["unit"].strip(),
                            }
                        except ValueError:
                            st.error(f"Variable '{n}' must have a numeric value.")
                            return

                    try:
                        result = evaluate_formula(formula_str, variables)
                    except Exception as e:
                        st.error(f"Calculation error: {e}")
                        return

                    # Show result
                    st.success("Result")
                    res_display = f"{result['numeric_result']:.6g}"
                    if result["result_unit"]:
                        res_display += f"  {result['result_unit']}"
                    st.metric("Answer", res_display)

                    st.latex(f"{result['latex']} = {result['substituted_latex']} = {result['numeric_result']:.6g}")

                    # Save to DB
                    calc = Calculation(
                        project_id=project.id,
                        title=title,
                        description=description,
                        formula=formula_str,
                        result_value=f"{result['numeric_result']:.6g}",
                        result_unit=result["result_unit"],
                        formula_latex=result["latex"],
                    )
                    calc.set_variables(variables)
                    session.add(calc)
                    session.commit()
                    st.info("Calculation saved.")

        # ==================================================================
        # TAB: Saved Calculations
        # ==================================================================
        with tab_saved:
            filter_proj = st.selectbox(
                "Filter by project", [None] + projects,
                format_func=lambda p: "All" if p is None else p.name,
                key="calc_filter",
            )
            query = session.query(Calculation).order_by(Calculation.created_at.desc())
            if filter_proj:
                query = query.filter(Calculation.project_id == filter_proj.id)
            calcs = query.limit(50).all()

            if not calcs:
                st.info("No calculations saved yet.")
            for c in calcs:
                with st.expander(f"{c.title}  —  {c.result_value} {c.result_unit}"):
                    st.caption(f"{c.created_at:%Y-%m-%d %H:%M}")
                    if c.description:
                        st.write(c.description)
                    st.markdown("**Formula**")
                    if c.formula_latex:
                        st.latex(c.formula_latex)
                    else:
                        st.code(c.formula)
                    st.markdown("**Variables**")
                    variables = c.get_variables()
                    for vname, vdata in variables.items():
                        unit_str = f" {vdata.get('unit', '')}" if vdata.get("unit") else ""
                        st.write(f"- **{vname}** = {vdata['value']}{unit_str}")
                    st.markdown(f"**Result:** {c.result_value} {c.result_unit}")
    finally:
        session.close()
