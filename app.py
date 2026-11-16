"""
HealthOps BI - Interactive Business Intelligence dashboard for hospital operations
CS 313 Business Intelligence, Final Learning Evidence

Run locally:   streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from dashboard import data as D
from dashboard import pages as P
from dashboard import theme as T

ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="HealthOps BI | Hospital operations dashboard", page_icon=":material/monitor_heart:",
                   layout="wide", initial_sidebar_state="expanded")
T.inject_css()
st.logo(str(ROOT / "assets" / "logo.svg"), icon_image=str(ROOT / "assets" / "icon.svg"), size="large")

df_all = D.load_data()
MONTHS = sorted(df_all["month"].unique())
FULL = (MONTHS[0], MONTHS[-1])
DEFAULTS = {"f_period": FULL, "f_setting": [], "f_department": [], "f_severity": [], "f_shift": [], "f_day": "All",
            "f_admission": [], "f_insurance": [], "f_age": []}
for k, v in DEFAULTS.items():
    if k != "f_period":  # the range slider takes its default from value= so it is always registered as a range
        st.session_state.setdefault(k, v)


def reset_filters() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


# ---- pages -------------------------------------------------------------------------------------
PAGES = {
    "overview": st.Page(P.overview, title="Overview", icon=":material/space_dashboard:", url_path="overview", default=True),
    "flow": st.Page(P.flow, title="Patient flow", icon=":material/schedule:", url_path="patient-flow"),
    "capacity": st.Page(P.capacity, title="Capacity", icon=":material/hotel:", url_path="capacity"),
    "quality": st.Page(P.quality, title="Quality", icon=":material/verified:", url_path="quality"),
    "cost": st.Page(P.cost, title="Cost", icon=":material/payments:", url_path="cost"),
    "drill": st.Page(P.drill, title="Drill-down", icon=":material/account_tree:", url_path="drill-down"),
    "insights": st.Page(P.insights, title="Insights & actions", icon=":material/lightbulb:", url_path="insights"),
    "methods": st.Page(P.methods, title="Data & methods", icon=":material/description:", url_path="data-methods"),
}
nav = st.navigation({
    "Monitor": [PAGES[k] for k in ("overview", "flow", "capacity", "quality", "cost")],
    "Analyse": [PAGES[k] for k in ("drill", "insights")],
    "Reference": [PAGES["methods"]],
})

# ---- sidebar slicers (shared by every page) -------------------------------------------------------
with st.sidebar:
    st.html('<div class="side-title">Filters</div>')
    period = st.select_slider("Period", options=MONTHS, value=FULL, key="f_period", format_func=D.period_label)
    if not (isinstance(period, (tuple, list)) and len(period) == 2):
        period = FULL
    st.multiselect("Care setting", D.SETTING_ORDER, key="f_setting", placeholder="All care settings")
    in_setting = df_all[df_all["care_setting"].isin(st.session_state["f_setting"])] if st.session_state["f_setting"] else df_all
    dept_options = sorted(in_setting["department"].unique())
    st.session_state["f_department"] = [d for d in st.session_state["f_department"] if d in dept_options]
    st.multiselect("Department", dept_options, key="f_department", placeholder="All departments")
    st.pills("Severity", D.SEVERITY_ORDER, selection_mode="multi", key="f_severity")
    st.pills("Shift", D.SHIFT_ORDER, selection_mode="multi", key="f_shift")
    st.segmented_control("Days", ["All", "Weekday", "Weekend"], key="f_day")
    with st.expander("More filters"):
        st.multiselect("Admission type", sorted(df_all["admission_type"].unique()), key="f_admission", placeholder="All admission types")
        st.multiselect("Insurance", sorted(df_all["insurance_type"].unique()), key="f_insurance", placeholder="All insurers")
        st.multiselect("Age group", D.AGE_ORDER, key="f_age", placeholder="All age groups")

    filters = {
        "period": tuple(period), "setting": st.session_state["f_setting"],
        "department": st.session_state["f_department"], "severity": st.session_state["f_severity"],
        "shift": st.session_state["f_shift"], "day": st.session_state["f_day"] or "All",
        "admission": st.session_state["f_admission"], "insurance": st.session_state["f_insurance"],
        "age": st.session_state["f_age"],
    }
    df = D.apply_filters(df_all, filters)
    active = D.count_active(filters, FULL)
    share = len(df) / len(df_all) * 100
    st.html(f'<div class="side-count"><b>{len(df):,}</b> <span>of {len(df_all):,} visits in scope</span>'
            f'<div class="side-bar"><i style="width:{share:.1f}%"></i></div></div>')
    st.button("Reset all filters", icon=":material/restart_alt:", on_click=reset_filters, disabled=active == 0, width="stretch")
    st.caption("Filters apply to every page. Simulated, anonymised data: January 2024 to December 2026.")

st.session_state["_ctx"] = {"all": df_all, "df": df, "filters": filters, "active": active, "pages": PAGES}

if df.empty and nav != PAGES["methods"]:
    T.hero("No visits match these filters", "Widen the period or remove a filter to see the dashboard.", ["0 visits in scope"])
    st.button("Reset all filters", icon=":material/restart_alt:", on_click=reset_filters, key="reset_main", type="primary")
    st.stop()

nav.run()
