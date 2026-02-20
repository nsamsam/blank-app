import streamlit as st
import json
import datetime

st.set_page_config(page_title="Eng Workbook", page_icon="📓", layout="wide")

# --- Session State Initialization ---
if "entries" not in st.session_state:
    st.session_state.entries = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# --- Sidebar Navigation ---
st.sidebar.title("📓 Eng Workbook")
page = st.sidebar.radio(
    "Navigate",
    ["Journal", "Calculator", "Task Tracker", "Reference"],
)

# ============================================================
# JOURNAL PAGE — timestamped engineering notes
# ============================================================
if page == "Journal":
    st.header("Journal")
    st.caption("Capture engineering notes, decisions, and observations.")

    with st.form("new_entry", clear_on_submit=True):
        title = st.text_input("Title")
        category = st.selectbox("Category", ["Note", "Decision", "Bug", "Idea", "Experiment"])
        body = st.text_area("Details", height=200)
        submitted = st.form_submit_button("Add Entry")
        if submitted and title:
            st.session_state.entries.insert(0, {
                "title": title,
                "category": category,
                "body": body,
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            })

    if st.session_state.entries:
        st.divider()
        filter_cat = st.multiselect(
            "Filter by category",
            ["Note", "Decision", "Bug", "Idea", "Experiment"],
            default=["Note", "Decision", "Bug", "Idea", "Experiment"],
        )
        for i, entry in enumerate(st.session_state.entries):
            if entry["category"] not in filter_cat:
                continue
            with st.expander(f"**{entry['title']}** — _{entry['category']}_  ({entry['timestamp']})"):
                st.markdown(entry["body"])
                if st.button("Delete", key=f"del_entry_{i}"):
                    st.session_state.entries.pop(i)
                    st.rerun()
    else:
        st.info("No entries yet. Add one above.")

# ============================================================
# CALCULATOR PAGE — quick engineering computations
# ============================================================
elif page == "Calculator":
    st.header("Calculator")
    st.caption("Run quick engineering calculations using Python expressions.")

    calc_tab, unit_tab = st.tabs(["Expression Evaluator", "Unit Converter"])

    with calc_tab:
        st.markdown(
            "Enter any Python math expression. "
            "The `math` module is available (e.g. `math.sqrt(2)`, `math.pi`)."
        )
        import math  # noqa: E402

        expr = st.text_input("Expression", placeholder="e.g. 3.14 * (25 ** 2)")
        if expr:
            try:
                allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
                allowed_names["abs"] = abs
                allowed_names["round"] = round
                allowed_names["min"] = min
                allowed_names["max"] = max
                result = eval(expr, {"__builtins__": {}}, allowed_names)  # noqa: S307
                st.success(f"Result: **{result}**")
            except Exception as e:
                st.error(f"Error: {e}")

    with unit_tab:
        st.subheader("Length")
        col1, col2, col3 = st.columns(3)
        length_val = col1.number_input("Value", value=1.0, key="len_val")
        from_unit = col2.selectbox("From", ["m", "cm", "mm", "in", "ft", "yd", "km", "mi"], key="len_from")
        to_unit = col3.selectbox("To", ["m", "cm", "mm", "in", "ft", "yd", "km", "mi"], index=3, key="len_to")

        # Convert everything to meters first
        to_m = {"m": 1, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "km": 1000, "mi": 1609.344}
        converted = length_val * to_m[from_unit] / to_m[to_unit]
        st.info(f"{length_val} {from_unit} = **{converted:.6g} {to_unit}**")

        st.subheader("Temperature")
        col1, col2, col3 = st.columns(3)
        temp_val = col1.number_input("Value", value=100.0, key="temp_val")
        temp_from = col2.selectbox("From", ["°C", "°F", "K"], key="temp_from")
        temp_to = col3.selectbox("To", ["°C", "°F", "K"], index=1, key="temp_to")

        # Convert to Celsius first
        if temp_from == "°C":
            c = temp_val
        elif temp_from == "°F":
            c = (temp_val - 32) * 5 / 9
        else:
            c = temp_val - 273.15

        if temp_to == "°C":
            temp_result = c
        elif temp_to == "°F":
            temp_result = c * 9 / 5 + 32
        else:
            temp_result = c + 273.15

        st.info(f"{temp_val} {temp_from} = **{temp_result:.4g} {temp_to}**")

        st.subheader("Data")
        col1, col2, col3 = st.columns(3)
        data_val = col1.number_input("Value", value=1.0, key="data_val")
        data_from = col2.selectbox("From", ["B", "KB", "MB", "GB", "TB", "PB"], key="data_from")
        data_to = col3.selectbox("To", ["B", "KB", "MB", "GB", "TB", "PB"], index=3, key="data_to")

        to_bytes = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4, "PB": 1024**5}
        data_result = data_val * to_bytes[data_from] / to_bytes[data_to]
        st.info(f"{data_val} {data_from} = **{data_result:.6g} {data_to}**")

# ============================================================
# TASK TRACKER PAGE
# ============================================================
elif page == "Task Tracker":
    st.header("Task Tracker")
    st.caption("Track engineering tasks and action items.")

    with st.form("new_task", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        task_text = col1.text_input("Task")
        priority = col2.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        task_submitted = st.form_submit_button("Add Task")
        if task_submitted and task_text:
            st.session_state.tasks.append({
                "text": task_text,
                "priority": priority,
                "done": False,
                "created": datetime.datetime.now().isoformat(timespec="seconds"),
            })

    if st.session_state.tasks:
        # Summary metrics
        total = len(st.session_state.tasks)
        done = sum(1 for t in st.session_state.tasks if t["done"])
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", total)
        col2.metric("Done", done)
        col3.metric("Remaining", total - done)

        st.divider()

        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_tasks = sorted(
            enumerate(st.session_state.tasks),
            key=lambda x: (x[1]["done"], priority_order.get(x[1]["priority"], 99)),
        )

        for idx, task in sorted_tasks:
            col1, col2, col3 = st.columns([0.5, 3, 0.5])
            new_done = col1.checkbox("Done", value=task["done"], key=f"task_done_{idx}", label_visibility="collapsed")
            if new_done != task["done"]:
                st.session_state.tasks[idx]["done"] = new_done
                st.rerun()
            label = f"~~{task['text']}~~" if task["done"] else task["text"]
            priority_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
            col2.markdown(f"{priority_colors.get(task['priority'], '')} {label}  \n<sub>{task['priority']} · {task['created']}</sub>", unsafe_allow_html=True)
            if col3.button("✕", key=f"del_task_{idx}"):
                st.session_state.tasks.pop(idx)
                st.rerun()
    else:
        st.info("No tasks yet. Add one above.")

# ============================================================
# REFERENCE PAGE — handy engineering cheat sheets
# ============================================================
elif page == "Reference":
    st.header("Reference")
    st.caption("Quick-reference tables for common engineering values.")

    tab1, tab2, tab3 = st.tabs(["HTTP Status Codes", "Big-O Cheat Sheet", "Common Ports"])

    with tab1:
        st.markdown("""
| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 301 | Moved Permanently |
| 302 | Found (Redirect) |
| 304 | Not Modified |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |
""")

    with tab2:
        st.markdown("""
| Algorithm | Time (Avg) | Time (Worst) | Space |
|-----------|-----------|-------------|-------|
| Array access | O(1) | O(1) | — |
| Binary search | O(log n) | O(log n) | O(1) |
| Linear search | O(n) | O(n) | O(1) |
| Hash table lookup | O(1) | O(n) | O(n) |
| Merge sort | O(n log n) | O(n log n) | O(n) |
| Quick sort | O(n log n) | O(n²) | O(log n) |
| Heap sort | O(n log n) | O(n log n) | O(1) |
| BFS / DFS | O(V + E) | O(V + E) | O(V) |
| Dijkstra | O(E log V) | O(E log V) | O(V) |
""")

    with tab3:
        st.markdown("""
| Port | Service |
|------|---------|
| 22 | SSH |
| 25 | SMTP |
| 53 | DNS |
| 80 | HTTP |
| 110 | POP3 |
| 143 | IMAP |
| 443 | HTTPS |
| 3306 | MySQL |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8080 | HTTP Alt |
| 8443 | HTTPS Alt |
| 27017 | MongoDB |
""")

# --- Footer ---
st.sidebar.divider()
st.sidebar.caption("Eng Workbook v1.0")
