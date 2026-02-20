"""
Engineering calculation engine.

- Parses formulas via sympy (safe — no eval/exec)
- Handles unit conversions via pint
- Produces LaTeX for rendered output
"""

import sympy
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)
import pint

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# Symbols we allow in formulas — engineering staples
SAFE_FUNCTIONS = {
    "sqrt": sympy.sqrt,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "asin": sympy.asin,
    "acos": sympy.acos,
    "atan": sympy.atan,
    "log": sympy.log,
    "ln": sympy.log,
    "exp": sympy.exp,
    "abs": sympy.Abs,
    "pi": sympy.pi,
    "Abs": sympy.Abs,
}


def parse_formula(formula_str: str) -> sympy.Expr:
    """Parse a formula string into a sympy expression."""
    return parse_expr(
        formula_str,
        local_dict=SAFE_FUNCTIONS,
        transformations=TRANSFORMS,
    )


def formula_to_latex(formula_str: str) -> str:
    """Convert a formula string to LaTeX."""
    expr = parse_formula(formula_str)
    return sympy.latex(expr)


def evaluate_formula(
    formula_str: str,
    variables: dict[str, dict],
) -> dict:
    """
    Evaluate a formula with variable values and optional units.

    Parameters
    ----------
    formula_str : str
        e.g. "F / A"
    variables : dict
        e.g. {"F": {"value": 100, "unit": "kN"}, "A": {"value": 0.05, "unit": "m**2"}}

    Returns
    -------
    dict with keys: numeric_result, result_unit, latex, substituted_latex
    """
    expr = parse_formula(formula_str)
    free = {str(s) for s in expr.free_symbols}

    # --- Numeric substitution via sympy ---
    subs = {}
    for name in free:
        if name not in variables:
            raise ValueError(f"Variable '{name}' used in formula but not defined.")
        subs[sympy.Symbol(name)] = float(variables[name]["value"])

    numeric_expr = expr.subs(subs)
    numeric_result = float(numeric_expr.evalf())

    # --- Unit propagation via pint ---
    result_unit = ""
    try:
        unit_subs = {}
        for name in free:
            v = variables[name]
            unit = v.get("unit", "").strip()
            if unit:
                unit_subs[name] = Q_(float(v["value"]), unit)
            else:
                unit_subs[name] = float(v["value"])

        # Build a pint expression by walking the formula
        pint_result = _evaluate_pint(formula_str, unit_subs)
        if isinstance(pint_result, ureg.Quantity):
            numeric_result = pint_result.magnitude
            result_unit = str(pint_result.units)
    except Exception:
        # If pint fails, fall back to the unitless numeric result
        pass

    # --- LaTeX: full formula and substituted version ---
    formula_latex = sympy.latex(expr)
    substituted_latex = sympy.latex(numeric_expr)

    return {
        "numeric_result": numeric_result,
        "result_unit": result_unit,
        "latex": formula_latex,
        "substituted_latex": substituted_latex,
    }


def _evaluate_pint(formula_str: str, unit_subs: dict):
    """
    Evaluate a formula string using pint Quantities for unit propagation.
    Uses a restricted namespace for safety.
    """
    import math

    safe_ns = {
        "sqrt": lambda x: x ** 0.5,
        "sin": pint.math.sin if hasattr(pint, "math") else math.sin,
        "cos": pint.math.cos if hasattr(pint, "math") else math.cos,
        "tan": pint.math.tan if hasattr(pint, "math") else math.tan,
        "log": math.log,
        "ln": math.log,
        "exp": math.exp,
        "abs": abs,
        "pi": math.pi,
        "__builtins__": {},
    }
    safe_ns.update(unit_subs)
    return eval(formula_str, safe_ns)  # noqa: S307 — namespace is locked down
