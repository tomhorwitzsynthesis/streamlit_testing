# utils/date_utils.py
import streamlit as st
from datetime import datetime
from calendar import month_name

# Manually define which months are available
AVAILABLE_MONTHS = [
    (2025, 1), (2025, 2), (2025, 3), (2025, 4), (2025, 5)
]

def get_selected_date_range():
    selected = st.session_state.get("selected_months", [])
    if not selected:
        st.sidebar.error("No months selected.")
        st.stop()

    selected.sort()
    start_year, start_month = selected[0]
    end_year, end_month = selected[-1]

    start_date = datetime(start_year, start_month, 1)
    if end_month == 12:
        end_date = datetime(end_year + 1, 1, 1)
    else:
        end_date = datetime(end_year, end_month + 1, 1)

    return start_date, end_date

def init_month_selector():
    st.sidebar.markdown("### Select Months to Include")
    selected = []

    for year, month in AVAILABLE_MONTHS:
        label = f"{month_name[month]} {year}"
        if st.sidebar.checkbox(label, value=True):
            selected.append((year, month))

    if not selected:
        st.sidebar.error("Please select at least one month.")
        st.stop()

    st.session_state["selected_months"] = selected
