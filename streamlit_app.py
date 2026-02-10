import streamlit as st
import pandas as pd

st.set_page_config(page_title="Engineering Calculations", layout="wide")
st.title("Engineering Calculations")

tab1, = st.tabs(["Casing Design"])

# ── Tab 1: Casing Design ─────────────────────────────────────────────────
with tab1:
    st.header("Casing Design Summary")

    # Build the data matching the spreadsheet
    data = {
        "No.": ["", "", "0", "1A", "3", "4", "5", "6", "7"],
        "Name": [
            "Structural Casing",
            "Structural Casing",
            "Structural Casing",
            "Surface Casing",
            "Production Casing",
            "Intermediate Liner",
            "Production Liner",
            "Production Liner",
            "",
        ],
        "Hole size (in)": [
            "Driven", "Driven", "Driven", "28.00", "17,500", "14,500", "10,625", "8,500", ""
        ],
        "Csg OD (in)": [
            "36", "36", "36", "22", "", "12,250", "12,250", "9,875", ""
        ],
        "Weight (ppf)": [
            "726", "552", "374", "224", "13.625", "11.875", "9.875", "7.75", ""
        ],
        "Grade": [
            "X-56", "X-65", "X-56", "X-80", "88.2", "71.8", "62.8", "46.1", ""
        ],
        "Conn.": [
            "0-60MT", "0-90 QT/MT", "0-90 QT/MT", "XLW", "HCQ-125", "TN125HC", "QI25HCE", "Q125", ""
        ],
        "Csg ID": [
            "32.00", "33.00", "34.00", "20.00", "SLI-II", "513", "513", "513", ""
        ],
        "Length": [
            "140.00'", "47.00'", "120.00'", "2,973", "12.35", "10.63", "8.63", "6.56", ""
        ],
        "MD Setting Depth (ft)": [
            "6,497'", "6,544'", "6,664'", "3,339'", "3,436", "4,650", "6,043", "", ""
        ],
        "TVD Setting Depth (ft)": [
            "6,497'", "6,544'", "6,664'", "9,339'", "9,800'", "14,150'", "19,893'", "21,174'", ""
        ],
        "TVDSS Setting Depth (ft)": [
            "6,394'", "6,441'", "6,561'", "9,236'", "9,697'", "17,295'", "15,900'", "17,010'", ""
        ],
        "TVDBML Setting Depth (ft)": [
            "128'", "128'", "295'", "2,970'", "3,431'", "5,531'", "17,597'", "16,907'", ""
        ],
        "TOL MD (ft)": [
            "6,357", "6,497'", "6,544'", "6,366'", "6,366'", "13,850'", "9,531'", "10,641'", ""
        ],
        "TOL TVDSS (ft)": [
            "6,357", "6,497'", "6,544'", "6,263'", "6,364'", "12,618'", "13,850'", "19,593'", ""
        ],
        "TOL TVD (ft)": [
            "6,251'", "6,394'", "6,441'", "-3'", "6,261'", "12,533'", "12,618'", "15,698'", ""
        ],
        "TOL TVD BML": [
            "127'", "128'", "175'", "", "", "", "", "15,595'", ""
        ],
        "MIYP (psi) [1]": [
            "", "", "", "6,850", "11,030", "14,240", "", "16,790", ""
        ],
        "MIYP (psi) [2]": [
            "", "", "", "#N/A", "6.77", "5.73", "", "16,590", ""
        ],
        "Collapse (psi)": [
            "", "", "", "2,836", "4,400", "13,420", "", "", ""
        ],
        "Collapse (SF)": [
            "", "", "", "2.39", "5.45", "9.63", "", "1017", ""
        ],
        "Ten. (Kips)": [
            "", "", "", "5311", "3191", "2270", "", "", ""
        ],
        "Ten. (SF)": [
            "", "", "", "6.64", "6.37", "5.01", "", "179", ""
        ],
        "BHT": [
            "38", "38", "38", "58", "126", "160", "", "", ""
        ],
        "PP": [
            "8.5", "8.5", "8.5", "#N/A", "9.17", "11.37", "", "10.99", ""
        ],
        "FG": [
            "8.6", "8.6", "8.7", "11.30", "11.30", "13.29", "", "13.32", ""
        ],
        "Final MW": [
            "", "", "", "13,500'", "13,500'", "13,400", "", "14.40", ""
        ],
        "TOC MD": [
            "NA", "NA", "", "12,450", "12,450", "10,400", "", "20,000'", ""
        ],
        "TOC TVD": [
            "NA", "NA", "6,366'", "4,339'", "4,339'", "10389", "", "15975", ""
        ],
        "MAWP (psi)": [
            "", "", "#N/A", "#N/A", "57.9'", "", "", "#REF!", ""
        ],
        "Incl (°)": [
            "", "", "", "5.3'", "57.9'", "", "", "", ""
        ],
        "BOP Test (psi)": [
            "", "", "", "600", "888", "450", "", "20.0'", ""
        ],
        "BOP Test SDM": [
            "*", "*", "", "10.5", "11.8", "", "", "", ""
        ],
        "MASP (psi)": [
            "", "", "", "1,097", "192", "192", "", "", ""
        ],
        "BOP Test (psi) [2]": [
            "", "", "", "13.4", "13.4", "", "", "", ""
        ],
        "Test Weight": [
            "#N/A", "#N/A", "", "11.3", "#N/A", "12,000", "", "", ""
        ],
        "Comp Depth (Kips)": [
            "", "", "", "", "", "11652", "", "", ""
        ],
        "Drill to Depth MD": [
            "", "", "", "", "", "", "", "", ""
        ],
        "Drill to Depth TVD": [
            "", "", "", "", "", "", "", "", ""
        ],
    }

    df = pd.DataFrame(data)

    # Highlight rows by casing type
    def highlight_rows(row):
        name = row["Name"]
        if name == "Structural Casing":
            return ["background-color: #FFFFCC"] * len(row)  # light yellow
        elif name == "Surface Casing":
            return ["background-color: #FFFFCC"] * len(row)  # light yellow
        elif name == "Production Casing":
            return ["background-color: #FFFFFF"] * len(row)
        elif name == "Intermediate Liner":
            return ["background-color: #FFFFFF"] * len(row)
        elif name == "Production Liner":
            return ["background-color: #FFCCCC"] * len(row)  # light pink
        else:
            return [""] * len(row)

    styled_df = df.style.apply(highlight_rows, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400,
        hide_index=True,
    )

    st.markdown("---")

    # Editable section
    st.subheader("Edit Casing Data")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=400,
        hide_index=True,
        num_rows="dynamic",
        key="casing_editor",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Export to CSV"):
            csv = edited_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="casing_design.csv",
                mime="text/csv",
            )

st.markdown("---")
st.caption("Engineering Calculations App • Verify all results independently before use in design.")
