import streamlit as st
import math

st.set_page_config(page_title="Engineering Calculations", layout="wide")

st.title("Engineering Calculations")
st.write("A collection of common engineering calculators.")

calc_type = st.sidebar.selectbox(
    "Select Calculator",
    [
        "Beam Bending (Simply Supported)",
        "Pipe Flow (Hazen-Williams)",
        "Ohm's Law & Power",
        "Heat Transfer (Conduction)",
        "Unit Conversions",
        "Stress & Strain",
        "Bolt Torque",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info("Select a calculator from the dropdown above.")

# ---------------------------------------------------------------------------
# Beam Bending – Simply Supported, Uniform Distributed Load
# ---------------------------------------------------------------------------
if calc_type == "Beam Bending (Simply Supported)":
    st.header("Simply Supported Beam – Uniform Distributed Load")
    st.write("Calculates max deflection, max bending moment, and max shear for a simply supported beam with a uniform distributed load (UDL).")

    col1, col2 = st.columns(2)
    with col1:
        w = st.number_input("Distributed load, w (kN/m)", min_value=0.0, value=10.0, step=0.1)
        L = st.number_input("Span length, L (m)", min_value=0.01, value=6.0, step=0.1)
    with col2:
        E = st.number_input("Modulus of elasticity, E (GPa)", min_value=0.01, value=200.0, step=1.0)
        I = st.number_input("Moment of inertia, I (cm⁴)", min_value=0.01, value=8356.0, step=1.0)

    if st.button("Calculate", key="beam"):
        E_pa = E * 1e9           # GPa -> Pa
        I_m4 = I * 1e-8          # cm⁴ -> m⁴
        w_nm = w * 1e3            # kN/m -> N/m

        M_max = (w_nm * L**2) / 8          # N·m
        V_max = (w_nm * L) / 2             # N
        delta_max = (5 * w_nm * L**4) / (384 * E_pa * I_m4)  # m

        st.subheader("Results")
        r1, r2, r3 = st.columns(3)
        r1.metric("Max Bending Moment", f"{M_max / 1e3:.2f} kN·m")
        r2.metric("Max Shear Force", f"{V_max / 1e3:.2f} kN")
        r3.metric("Max Deflection", f"{delta_max * 1e3:.4f} mm")

        st.caption("Formulas: M_max = wL²/8 · V_max = wL/2 · δ_max = 5wL⁴/(384EI)")

# ---------------------------------------------------------------------------
# Pipe Flow – Hazen-Williams
# ---------------------------------------------------------------------------
elif calc_type == "Pipe Flow (Hazen-Williams)":
    st.header("Pipe Flow – Hazen-Williams Equation")
    st.write("Estimates flow velocity and discharge in a pressure pipe.")

    col1, col2 = st.columns(2)
    with col1:
        C = st.number_input("Hazen-Williams coefficient, C", min_value=1.0, value=130.0, step=1.0)
        D = st.number_input("Pipe inside diameter (mm)", min_value=1.0, value=200.0, step=1.0)
    with col2:
        S = st.number_input("Hydraulic slope, S (m/m)", min_value=0.0001, value=0.005, step=0.0001, format="%.4f")

    if st.button("Calculate", key="pipe"):
        R = (D / 1000) / 4   # hydraulic radius for full pipe = D/4
        V = 0.849 * C * (R ** 0.63) * (S ** 0.54)   # m/s
        A = math.pi * (D / 1000 / 2) ** 2
        Q = V * A  # m³/s

        st.subheader("Results")
        r1, r2, r3 = st.columns(3)
        r1.metric("Flow Velocity", f"{V:.3f} m/s")
        r2.metric("Flow Rate", f"{Q:.6f} m³/s")
        r3.metric("Flow Rate", f"{Q * 1000:.3f} L/s")

# ---------------------------------------------------------------------------
# Ohm's Law & Electrical Power
# ---------------------------------------------------------------------------
elif calc_type == "Ohm's Law & Power":
    st.header("Ohm's Law & Electrical Power")

    solve_for = st.radio("Solve for:", ["Voltage (V)", "Current (I)", "Resistance (R)"], horizontal=True)

    col1, col2 = st.columns(2)

    if solve_for == "Voltage (V)":
        with col1:
            I_val = st.number_input("Current, I (A)", min_value=0.0, value=5.0, step=0.1)
        with col2:
            R_val = st.number_input("Resistance, R (Ω)", min_value=0.0, value=10.0, step=0.1)
        if st.button("Calculate", key="ohm"):
            V_val = I_val * R_val
            P_val = V_val * I_val
            r1, r2 = st.columns(2)
            r1.metric("Voltage", f"{V_val:.3f} V")
            r2.metric("Power", f"{P_val:.3f} W")

    elif solve_for == "Current (I)":
        with col1:
            V_val = st.number_input("Voltage, V (V)", min_value=0.0, value=120.0, step=1.0)
        with col2:
            R_val = st.number_input("Resistance, R (Ω)", min_value=0.01, value=10.0, step=0.1)
        if st.button("Calculate", key="ohm"):
            I_val = V_val / R_val
            P_val = V_val * I_val
            r1, r2 = st.columns(2)
            r1.metric("Current", f"{I_val:.3f} A")
            r2.metric("Power", f"{P_val:.3f} W")

    else:
        with col1:
            V_val = st.number_input("Voltage, V (V)", min_value=0.0, value=120.0, step=1.0)
        with col2:
            I_val = st.number_input("Current, I (A)", min_value=0.01, value=5.0, step=0.1)
        if st.button("Calculate", key="ohm"):
            R_val = V_val / I_val
            P_val = V_val * I_val
            r1, r2 = st.columns(2)
            r1.metric("Resistance", f"{R_val:.3f} Ω")
            r2.metric("Power", f"{P_val:.3f} W")

# ---------------------------------------------------------------------------
# Heat Transfer – Conduction (Fourier's Law)
# ---------------------------------------------------------------------------
elif calc_type == "Heat Transfer (Conduction)":
    st.header("Steady-State Heat Conduction (Fourier's Law)")
    st.write("Q = k · A · ΔT / d")

    col1, col2 = st.columns(2)
    with col1:
        k = st.number_input("Thermal conductivity, k (W/m·K)", min_value=0.001, value=50.0, step=0.1)
        A_area = st.number_input("Cross-sectional area, A (m²)", min_value=0.001, value=1.0, step=0.01)
    with col2:
        dT = st.number_input("Temperature difference, ΔT (°C or K)", min_value=0.0, value=100.0, step=1.0)
        d = st.number_input("Thickness, d (m)", min_value=0.001, value=0.05, step=0.001)

    if st.button("Calculate", key="heat"):
        Q = k * A_area * dT / d
        st.subheader("Results")
        st.metric("Heat Transfer Rate, Q", f"{Q:.2f} W")
        if Q > 1000:
            st.write(f"= {Q / 1000:.4f} kW")

# ---------------------------------------------------------------------------
# Unit Conversions
# ---------------------------------------------------------------------------
elif calc_type == "Unit Conversions":
    st.header("Common Engineering Unit Conversions")

    category = st.selectbox("Category", ["Length", "Force", "Pressure", "Temperature", "Mass"])

    value = st.number_input("Value to convert", value=1.0, format="%.6f")

    if category == "Length":
        conversions = {
            "m → ft": value * 3.28084,
            "ft → m": value * 0.3048,
            "m → in": value * 39.3701,
            "in → m": value * 0.0254,
            "km → mi": value * 0.621371,
            "mi → km": value * 1.60934,
        }
    elif category == "Force":
        conversions = {
            "N → lbf": value * 0.224809,
            "lbf → N": value * 4.44822,
            "kN → kip": value * 0.224809,
            "kip → kN": value * 4.44822,
        }
    elif category == "Pressure":
        conversions = {
            "Pa → psi": value * 0.000145038,
            "psi → Pa": value * 6894.76,
            "MPa → ksi": value * 0.145038,
            "ksi → MPa": value * 6.89476,
            "bar → psi": value * 14.5038,
            "psi → bar": value * 0.0689476,
            "atm → Pa": value * 101325,
        }
    elif category == "Temperature":
        conversions = {
            "°C → °F": value * 9 / 5 + 32,
            "°F → °C": (value - 32) * 5 / 9,
            "°C → K": value + 273.15,
            "K → °C": value - 273.15,
        }
    else:  # Mass
        conversions = {
            "kg → lb": value * 2.20462,
            "lb → kg": value * 0.453592,
            "kg → slug": value * 0.0685218,
            "slug → kg": value * 14.5939,
        }

    st.subheader("Results")
    for label, result in conversions.items():
        st.write(f"**{label}**: {result:.6g}")

# ---------------------------------------------------------------------------
# Stress & Strain
# ---------------------------------------------------------------------------
elif calc_type == "Stress & Strain":
    st.header("Stress, Strain & Deformation")

    col1, col2 = st.columns(2)
    with col1:
        F = st.number_input("Axial force, F (kN)", min_value=0.0, value=100.0, step=1.0)
        A_cs = st.number_input("Cross-sectional area, A (mm²)", min_value=0.01, value=500.0, step=1.0)
    with col2:
        L0 = st.number_input("Original length, L₀ (mm)", min_value=0.01, value=1000.0, step=1.0)
        E_mod = st.number_input("Young's modulus, E (GPa)", min_value=0.01, value=200.0, step=1.0)

    if st.button("Calculate", key="stress"):
        sigma = (F * 1e3) / (A_cs * 1e-6) / 1e6   # MPa
        epsilon = sigma / (E_mod * 1e3)              # strain (MPa / MPa)
        delta_L = epsilon * L0                        # mm

        st.subheader("Results")
        r1, r2, r3 = st.columns(3)
        r1.metric("Stress (σ)", f"{sigma:.2f} MPa")
        r2.metric("Strain (ε)", f"{epsilon:.6f}")
        r3.metric("Deformation (δ)", f"{delta_L:.4f} mm")

# ---------------------------------------------------------------------------
# Bolt Torque
# ---------------------------------------------------------------------------
elif calc_type == "Bolt Torque":
    st.header("Bolt Torque Calculator")
    st.write("T = K · d · F  (short-form torque equation)")

    col1, col2 = st.columns(2)
    with col1:
        K_factor = st.number_input("Nut factor, K (dimensionless)", min_value=0.01, value=0.20, step=0.01,
                                   help="Typical: 0.20 for dry steel, 0.15 for lubricated")
        d_bolt = st.number_input("Nominal bolt diameter, d (mm)", min_value=1.0, value=16.0, step=1.0)
    with col2:
        F_clamp = st.number_input("Desired clamp force, F (kN)", min_value=0.0, value=50.0, step=1.0)

    if st.button("Calculate", key="bolt"):
        T = K_factor * (d_bolt / 1000) * (F_clamp * 1e3)  # N·m
        st.subheader("Results")
        r1, r2 = st.columns(2)
        r1.metric("Required Torque", f"{T:.2f} N·m")
        r2.metric("Required Torque", f"{T * 0.7376:.2f} ft·lbf")

# Footer
st.markdown("---")
st.caption("Engineering Calculations App • Verify all results independently before use in design.")
