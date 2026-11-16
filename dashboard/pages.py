"""Page bodies. Each function renders one page for the visits currently in scope (sidebar filters)."""
from __future__ import annotations

import io
import zipfile

import pandas as pd
import streamlit as st

from . import charts as C
from . import data as D
from . import docs
from . import insights as I
from . import kpi as K
from . import theme as T

HEAD = {"wait": "Wait (min)", "occupancy": "Occupancy %", "readmit": "Readmit %", "noshow": "No-show %",
        "satisfaction": "Satisfaction", "success": "Success %"}


def ctx() -> dict:
    return st.session_state["_ctx"]


def label(key: str) -> str:
    return K.KPIS[key].label


def header(title: str, subtitle: str) -> None:
    c = ctx()
    a, b = c["filters"]["period"]
    n = c["active"]
    chips = [
        f"<b>{len(c['df']):,}</b> of {len(c['all']):,} visits",
        f"{D.period_label(a)} to {D.period_label(b)}",
        f"<b>{n}</b> filter{'s' if n != 1 else ''} active" if n else "No filters applied",
    ]
    T.hero(title, subtitle, chips)


def card(key: str, title: str, subtitle: str = ""):
    box = st.container(key=f"card_{key}")
    with box:
        T.card_header(title, subtitle)
    return box


def chart(fig_table, key: str) -> None:
    fig, table = fig_table
    C.show(fig, key=key)
    C.table_popover(table)


def html_table(frame: pd.DataFrame) -> str:
    """Text-heavy reference table with wrapping cells (st.dataframe truncates long text)."""
    head = "".join(f"<th>{T.esc(c)}</th>" for c in frame.columns)
    body = "".join("<tr>" + "".join(f"<td>{T.esc(v)}</td>" for v in row) + "</tr>" for row in frame.itertuples(index=False))
    return f'<div class="tbl-wrap"><table class="sc wrap"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def seg(label_: str, options: list[str], default: str, key: str) -> str:
    return st.segmented_control(label_, options, default=default, key=key, label_visibility="collapsed") or default


def grain_select(key: str) -> str:
    """Compact time-grain picker for half-width cards."""
    return st.selectbox("Time grain", ["Month", "Quarter", "Year"], index=1, key=key, label_visibility="collapsed",
                        format_func=lambda g: f"By {g.lower()}")


def kpi_select(label_: str, keys: list[str], key: str) -> str:
    return st.selectbox(label_, keys, format_func=label, key=key, label_visibility="collapsed")


def dim_select(key: str, default: str = "Department", exclude: tuple[str, ...] = ()) -> str:
    names = [n for n in D.DIMENSIONS if n not in exclude]
    name = st.selectbox("Compare by", names, index=names.index(default), key=key, label_visibility="collapsed")
    return D.DIMENSIONS[name]


# ================================================================================================
# Overview
# ================================================================================================
def scorecard_html(df: pd.DataFrame) -> str:
    sc = K.scorecard(df, "department")
    heads = ["Department", "Visits"]
    for key in K.TARGETED:
        k = K.KPIS[key]
        sign = "≤" if k.good == "low" else "≥"
        heads.append(f"{HEAD[key]} <span style='opacity:.65'>{sign}{K.target_of(k, df):g}</span>")
    heads.append("Targets")
    body = []
    for _, r in sc.iterrows():
        cells = [f"<td>{T.esc(D.short(r['label']))}</td>", f"<td>{int(r['visits']):,}</td>"]
        for key in K.TARGETED:
            cls = ' class="miss"' if r[f"{key}_ok"] is False else ""
            cells.append(f"<td{cls}>{K.fmt(key, r[key], with_unit=False)}</td>")
        m = int(r["missed"])
        status = (T.pill("All met", "good", "✓") if m == 0 else
                  T.pill("1 missed", "warn", "!") if m == 1 else T.pill(f"{m} missed", "crit", "⚠"))
        cells.append(f"<td>{status}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    tot = [f"<td>All in scope</td><td>{len(df):,}</td>"]
    missed = 0
    for key in K.TARGETED:
        k = K.KPIS[key]
        v = k.calc(df)
        ok = K.meets(k, v, K.target_of(k, df))
        missed += int(ok is False)
        tot.append(f"<td{' class=miss' if ok is False else ''}>{K.fmt(key, v, with_unit=False)}</td>")
    tot.append(f"<td>{6 - missed} of 6 met</td>")
    return ('<div class="tbl-wrap"><table class="sc"><thead><tr>' + "".join(f"<th>{h}</th>" for h in heads) +
            "</tr></thead><tbody>" + "".join(body) + '<tr class="tot">' + "".join(tot) + "</tr></tbody></table></div>")


def brief(df: pd.DataFrame) -> None:
    missed = []
    for key in K.TARGETED:
        k = K.KPIS[key]
        v, tgt = k.calc(df), K.target_of(k, df)
        if K.meets(k, v, tgt) is False:
            missed.append(f"{k.label.lower()} ({K.fmt(k, v)} against a target of {tgt:g})")
    text = f"{6 - len(missed)} of 6 targets are met in this selection."
    if missed:
        text += " Off target: " + "; ".join(missed) + "."
    sc = K.scorecard(df, "department")
    if len(sc) > 1 and sc.iloc[0]["missed"] > 0:
        text += f" {sc.iloc[0]['label']} misses the most targets ({int(sc.iloc[0]['missed'])} of 6)."
    with st.container(key="card_brief"):
        a, b = st.columns([5, 1], vertical_alignment="center")
        a.html(f'<div class="brief"><div class="brief-ic">{T.icon("pulse", 22, "#ffffff")}</div><div>'
               f'<div class="brief-t">Where things stand</div><div class="brief-s">{T.esc(text)}</div></div></div>')
        b.page_link(ctx()["pages"]["insights"], label="See insights", icon=":material/arrow_forward:")


def overview() -> None:
    df = ctx()["df"]
    header("Hospital operations overview",
           "Performance against the six operating targets, and where management should look first.")
    st.html(K.tiles(df, K.HEADLINE))
    brief(df)
    left, right = st.columns([1.9, 1])
    with left, card("ov_trend", "Performance over time", "Choose a KPI and a time grain. The dotted line is the target."):
        a, b = st.columns([1.6, 1])
        with a:
            key = kpi_select("KPI", ["visits", "wait", "occupancy", "readmit", "noshow", "satisfaction", "success",
                                     "cost", "total_cost", "high_strain"], "ov_kpi")
        with b:
            grain = seg("Time grain", ["Month", "Quarter", "Year"], "Quarter", "ov_grain")
        chart(C.trend(df, key, grain, height=300), "ov_trend_fig")
    with right, card("ov_donut", "Capacity status", "Share of visits by the capacity alert level in force."):
        chart(C.capacity_donut(df, height=352), "ov_donut_fig")
    with card("ov_score", "Department scorecard",
              "Every department against the six targets. Values marked in red miss the target; sorted by targets missed."):
        st.html(scorecard_html(df))


# ================================================================================================
# Patient flow
# ================================================================================================
def flow() -> None:
    df = ctx()["df"]
    header("Patient flow and wait times", "When patients arrive, how long they wait, and where appointments are lost.")
    st.html(K.tiles(df, ["visits", "wait", "wait_breach", "noshow", "completed"], compact=True, cols=5))
    a, b = st.columns(2)
    with a, card("fl_season", "Visits by month", "One line per year: shows the seasonal pattern and the year-on-year change."):
        chart(C.seasonality(df, "visits", height=330), "fl_season_fig")
    with b, card("fl_week", "Busiest times of the week", "Number of visits by day and shift. Darker cells are busier."):
        chart(C.heatmap(df, "visits", "day_of_week", "shift", min_n=1, height=330), "fl_week_fig")
    a, b = st.columns(2)
    with a, card("fl_wait", "Average wait by department", "Minutes before being seen. Dark bars are above the target."):
        chart(C.dim_bar(df, "wait", "department"), "fl_wait_fig")
    with b, card("fl_waitheat", "Wait time by department and shift", "Average minutes. Cells with fewer than 3 visits are blank."):
        chart(C.heatmap(df, "wait", "department", "shift", height=410), "fl_waitheat_fig")
    a, b = st.columns(2)
    with a, card("fl_adm", "How patients arrive", "Share of visits by admission type."):
        chart(C.share_bar(df, "admission_type"), "fl_adm_fig")
    with b, card("fl_noshow", "No-show rate", "Share of appointments missed. Pick a dimension to compare."):
        dim = dim_select("fl_noshow_dim", default="Department")
        chart(C.dim_bar(df, "noshow", dim, min_n=5), "fl_noshow_fig")


# ================================================================================================
# Capacity
# ================================================================================================
def capacity() -> None:
    df = ctx()["df"]
    header("Capacity and resources", "How full the units are, how hard resources are working, and what is causing strain.")
    st.html(K.tiles(df, ["occupancy", "occ_breach", "high_strain", "utilization", "los"], compact=True, cols=5))
    a, b = st.columns(2)
    with a, card("cp_occ", "Bed occupancy by department", "Average occupancy at the time of the visit. Dark bars are above the ceiling."):
        chart(C.dim_bar(df, "occupancy", "department"), "cp_occ_fig")
    with b, card("cp_mix", "Capacity status by department", "Share of each department's visits handled at each alert level."):
        chart(C.status_mix(df, "department"), "cp_mix_fig")
    a, b = st.columns(2)
    with a, card("cp_bn", "What is causing bottlenecks", "Share of visits flagged with each cause. A visit can have several."):
        chart(C.bottlenecks(df), "cp_bn_fig")
    with b, card("cp_trend", "Capacity trend", "Choose a measure and a time grain."):
        x, y = st.columns([1.6, 1])
        with x:
            key = kpi_select("Measure", ["occupancy", "occ_breach", "high_strain", "utilization", "los"], "cp_kpi")
        with y:
            grain = grain_select("cp_grain")
        chart(C.trend(df, key, grain, height=262), "cp_trend_fig")
    with card("cp_heat", "Occupancy by department and quarter",
              "Average bed occupancy (%). Darker cells are fuller; cells with fewer than 3 visits are blank."):
        chart(C.heatmap(df, "occupancy", "department", "quarter", height=420), "cp_heat_fig")


# ================================================================================================
# Quality
# ================================================================================================
def quality() -> None:
    df = ctx()["df"]
    header("Quality and outcomes", "Readmissions, treatment success and patient satisfaction, and which groups drive them.")
    st.html(K.tiles(df, ["readmit", "success", "satisfaction", "noshow"], compact=True))
    a, b = st.columns([1.25, 1])
    with a, card("ql_cmp", "Compare a quality measure", "Pick a measure and a dimension. Dark bars miss the target."):
        x, y = st.columns(2)
        with x:
            key = kpi_select("Measure", ["readmit", "success", "satisfaction", "noshow"], "ql_kpi")
        with y:
            dim = dim_select("ql_dim", default="Department")
        chart(C.dim_bar(df, key, dim, min_n=5), "ql_cmp_fig")
    with b, card("ql_out", "Visit outcomes", "Share of visits by recorded outcome."):
        chart(C.share_bar(df, "visit_outcome"), "ql_out_fig")
    with card("ql_wait", "What long waits are associated with",
              "The same three measures split by how long the patient waited. Dark bars miss the target."):
        cols = st.columns(3)
        for col, key in zip(cols, ["satisfaction", "success", "readmit"]):
            with col:
                st.caption(label(key))
                chart(C.dim_bar(df, key, "wait_band", min_n=5), f"ql_wait_{key}")
    a, b = st.columns(2)
    with a, card("ql_heat", "Readmission rate by department and severity", "Percent readmitted within 30 days. Cells with fewer than 5 visits are blank."):
        chart(C.heatmap(df, "readmit", "department", "severity_level", min_n=5, height=410), "ql_heat_fig")
    with b, card("ql_trend", "Quality trend", "Choose a measure and a time grain. The dotted line is the target."):
        x, y = st.columns([1.6, 1])
        with x:
            tkey = kpi_select("Measure", ["readmit", "success", "satisfaction", "noshow"], "ql_tkpi")
        with y:
            grain = grain_select("ql_grain")
        chart(C.trend(df, tkey, grain, height=318), "ql_trend_fig")


# ================================================================================================
# Cost
# ================================================================================================
def cost() -> None:
    df = ctx()["df"]
    header("Cost and resource use", "Where estimated cost concentrates and what drives the cost of a visit.")
    st.html(K.tiles(df, ["total_cost", "cost", "los", "utilization"], compact=True))
    a, b = st.columns([1.25, 1])
    with a, card("ct_share", "Share of visits versus share of cost",
                 "A long line means a department costs far more (or less) than its share of visits."):
        chart(C.cost_share_dumbbell(df, "department"), "ct_share_fig")
    with b, card("ct_sev", "Average cost per visit by severity", "Cost rises steeply with severity."):
        chart(C.dim_bar(df, "cost", "severity_level"), "ct_sev_fig")
    a, b = st.columns([1.25, 1])
    with a, card("ct_time", "Total cost over time", "Stacked by care setting."):
        grain = seg("Time grain", ["Quarter", "Year"], "Quarter", "ct_grain")
        chart(C.cost_over_time(df, grain, height=320), "ct_time_fig")
    with b, card("ct_cmp", "Compare cost", "Pick a cost measure and a dimension."):
        x, y = st.columns(2)
        with x:
            key = kpi_select("Measure", ["cost", "total_cost", "los"], "ct_kpi")
        with y:
            dim = dim_select("ct_dim", default="Admission type")
        chart(C.dim_bar(df, key, dim, min_n=5), "ct_cmp_fig")


# ================================================================================================
# Drill-down
# ================================================================================================
RECORD_COLS = {
    "visit_id": "Visit", "visit_date": "Date", "department": "Department", "admission_type": "Admission",
    "severity_level": "Severity", "shift": "Shift", "age_group": "Age group", "insurance_type": "Insurance",
    "er_wait_time_minutes": "Wait (min)", "length_of_stay_days": "Stay (days)", "bed_occupancy_rate": "Occupancy %",
    "estimated_cost_per_visit": "Cost", "patient_satisfaction_score": "Satisfaction", "visit_outcome": "Outcome",
    "capacity_status": "Capacity status", "bottleneck_reason": "Bottlenecks",
}


def _drill_to(setting: str | None, dept: str | None) -> None:
    st.session_state["drill_setting"], st.session_state["drill_dept"] = setting, dept
    st.session_state["drill_n"] = st.session_state.get("drill_n", 0) + 1


def _jump() -> None:
    choice = st.session_state["drill_jump"]
    if choice == "All departments":
        _drill_to(None, None)
    else:
        all_df = ctx()["all"]
        setting = all_df.loc[all_df["department"] == choice, "care_setting"].iloc[0]
        _drill_to(setting, choice)


def drill() -> None:
    df = ctx()["df"]
    ss = st.session_state
    header("Drill-down explorer", "Click a bar to drill from care setting to department to individual visits.")
    ss.setdefault("drill_setting", None)
    ss.setdefault("drill_dept", None)
    ss.setdefault("drill_n", 0)
    settings = [s for s in D.SETTING_ORDER if s in set(df["care_setting"])]
    if ss["drill_setting"] not in settings:
        ss["drill_setting"], ss["drill_dept"] = None, None
    if ss["drill_dept"] not in set(df["department"]):
        ss["drill_dept"] = None
    setting, dept = ss["drill_setting"], ss["drill_dept"]
    depts = sorted(df["department"].unique())

    with st.container(key="card_drill_nav"):
        a, b, c = st.columns([2.2, 1.3, 1.3], vertical_alignment="bottom")
        with a:
            st.caption("You are here")
            with st.container(horizontal=True, gap="small", vertical_alignment="center"):
                st.button("All care settings", icon=":material/home:", key="dr_home", type="tertiary" if setting else "secondary",
                          on_click=_drill_to, args=(None, None), disabled=setting is None)
                if setting:
                    st.button(setting, icon=":material/chevron_right:", key="dr_set", type="tertiary" if dept else "secondary",
                              on_click=_drill_to, args=(setting, None), disabled=dept is None)
                if dept:
                    st.button(dept, icon=":material/chevron_right:", key="dr_dept", disabled=True)
        with b:
            key = st.selectbox("Measure", ["visits", "wait", "occupancy", "readmit", "noshow", "satisfaction", "success",
                                           "cost", "total_cost", "los", "high_strain"], format_func=label, key="dr_kpi")
        with c:
            ss["drill_jump"] = dept or "All departments"
            st.selectbox("Jump to a department", ["All departments"] + depts, key="drill_jump", on_change=_jump)

    if dept is None:
        level_dim = "care_setting" if setting is None else "department"
        scope = df if setting is None else df[df["care_setting"] == setting]
        title = "Care settings" if setting is None else f"Departments in {setting}"
        left, right = st.columns([1.25, 1])
        with left, card("dr_level", f"{label(key)} by {'care setting' if setting is None else 'department'}",
                        "Click a bar to drill in."):
            fig, table = C.dim_bar(scope, key, level_dim)
            clicked = C.pick(fig, key=f"dr_pick_{ss['drill_n']}_{level_dim}_{key}")
            C.table_popover(table)
            if clicked:
                _drill_to(clicked, None) if setting is None else _drill_to(setting, clicked)
                st.rerun()
        with right, card("dr_side", title, "Scorecard for this level."):
            st.html(K.tiles(scope, ["visits", "wait", "occupancy", "readmit", "success", "cost"], compact=True, cols=4)
                    .replace('class="kpis"', 'class="kpis" style="grid-template-columns:repeat(2,minmax(0,1fr))"'))
        return

    scope = df[df["department"] == dept]
    st.html(K.tiles(scope, ["visits", "wait", "occupancy", "readmit", "satisfaction", "success", "cost", "los"], compact=True))
    left, right = st.columns(2)
    with left, card("dr_break", f"{dept}: {label(key).lower()} breakdown", "Choose how to split this department."):
        dim = dim_select("dr_dim", default="Severity", exclude=("Department", "Care setting"))
        chart(C.dim_bar(scope, key, dim, min_n=1), "dr_break_fig")
    with right, card("dr_trend", f"{dept}: {label(key).lower()} over time", "Quarterly, with the target where one exists."):
        chart(C.trend(scope, key, "Quarter", height=300), "dr_trend_fig")
    with card("dr_rows", f"{dept}: visit records", f"{len(scope):,} visits. Sort by any column, or search and download."):
        a, b = st.columns([3, 1], vertical_alignment="bottom")
        q = a.text_input("Search visit ID, outcome or bottleneck", key="dr_q", placeholder="for example V2026, Readmitted or Long LOS")
        rows = scope[list(RECORD_COLS)].sort_values("visit_date", ascending=False)
        if q:
            hay = rows[["visit_id", "visit_outcome", "bottleneck_reason", "severity_level", "admission_type"]].agg(" ".join, axis=1)
            rows = rows[hay.str.contains(q, case=False, regex=False)]
        b.download_button("Download these rows", rows.to_csv(index=False).encode(), file_name=f"visits_{dept.split()[0].lower()}.csv",
                          mime="text/csv", icon=":material/download:", width="stretch")
        st.dataframe(
            rows.rename(columns=RECORD_COLS), hide_index=True, height=380,
            column_config={
                "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Cost": st.column_config.NumberColumn(format="dollar"),
                "Occupancy %": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
                "Wait (min)": st.column_config.NumberColumn(format="%.1f"),
                "Satisfaction": st.column_config.NumberColumn(format="%.2f"),
            },
        )


# ================================================================================================
# Insights
# ================================================================================================
def insights() -> None:
    df = ctx()["df"]
    header("Insights and recommended actions",
           "What the data shows, the evidence behind it, why it matters, and what management should do.")
    items = I.build(df)
    if not items:
        st.info("There are too few visits in this selection to draw reliable insights. Widen the filters.")
        return
    scope_note = (f"{len(items)} insights apply to the {len(df):,} visits in scope. Every figure below is calculated "
                  "from the current selection, so it changes with the sidebar filters.")
    if len(items) < len(I.BUILDERS):
        scope_note += f" Clear the filters to see all {len(I.BUILDERS)}."
    st.html(f'<div class="note">{T.esc(scope_note)}</div>')
    cards = []
    for it in items:
        cards.append(
            f'<div class="in"><div class="in-h"><div class="in-n">{it["n"]}</div><div><div class="in-t">{T.esc(it["title"])}</div>'
            f'{T.pill(it["tag"], "info")}</div></div><dl>'
            f'<dt>Discovery</dt><dd>{T.esc(it["found"])}</dd>'
            f'<dt>Evidence</dt><dd>{T.esc(it["evidence"])}</dd>'
            f'<dt>Why it matters</dt><dd>{T.esc(it["why"])}</dd>'
            f'<dt>Action</dt><dd class="act">{T.esc(it["action"])}</dd></dl></div>'
        )
    st.html('<div class="ins">' + "".join(cards) + "</div>")
    with card("in_table", "Summary for management", "Insight and recommended action side by side."):
        rows = "".join(
            f'<tr><td>{it["n"]}</td><td>{T.pill(it["tag"], "info")}</td><td>{T.esc(it["title"])}</td>'
            f'<td>{T.esc(it["action"])}</td></tr>' for it in items)
        st.html('<div class="tbl-wrap"><table class="sc wrap ins"><thead><tr><th>#</th><th>Area</th><th>Business insight</th>'
                f'<th>Recommended action</th></tr></thead><tbody>{rows}</tbody></table></div>')
        full = pd.DataFrame([{"No": it["n"], "Area": it["tag"], "Insight": it["title"], "What was discovered": it["found"],
                              "Supporting data": it["evidence"], "Why it matters": it["why"],
                              "Recommended action": it["action"]} for it in items])
        st.download_button("Download insights (CSV)", full.to_csv(index=False).encode(), file_name="insights_and_actions.csv",
                           mime="text/csv", icon=":material/download:")


# ================================================================================================
# Data & methods
# ================================================================================================
@st.cache_data(show_spinner=False)
def _model_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(D.MODEL_DIR.glob("*.csv")):
            z.write(p, p.name)
    return buf.getvalue()


def methods() -> None:
    rep = D.load_report()
    raw = D.load_raw()
    clean = ctx()["all"]
    T.hero("Data and methods", "Where the numbers come from: the business case, data preparation, data model and KPI definitions.",
           [f"<b>{rep['before']['rows']:,}</b> records", f"<b>{rep['before']['columns']}</b> raw fields",
            f"{rep['date_range'][0]} to {rep['date_range'][1]}"], eyebrow="Documentation")
    t_biz, t_prep, t_model, t_kpi, t_dict, t_dl = st.tabs(
        ["Business case", "Data preparation", "Data model", "KPI definitions", "Data dictionary", "Downloads"])

    with t_biz:
        a, b = st.columns(2)
        with a, card("m_biz", "Business problem"):
            for k, v in docs.BUSINESS.items():
                st.markdown(f"**{k}.** {v}")
            st.markdown("**Specific objectives**")
            st.markdown("\n".join(f"{i}. {o}" for i, o in enumerate(docs.SPECIFIC_OBJECTIVES, 1)))
        with b:
            with card("m_q", "Business questions", "Each question is answered on one page of the dashboard."):
                st.html(html_table(pd.DataFrame(docs.BUSINESS_QUESTIONS, columns=["Business question", "Answered on"])))
            with card("m_users", "Intended users and decision-makers"):
                st.html(html_table(pd.DataFrame(docs.USERS, columns=["User", "What they decide with it"])))

    with t_prep:
        b4, af = rep["before"], rep["after"]
        st.html(
            '<div class="stat-row">'
            f'<div class="stat"><b>{b4["rows"]:,} → {af["rows"]:,}</b><span>records kept</span><br><i>no duplicates found</i></div>'
            f'<div class="stat"><b>{b4["missing_cells"]} → {af["missing_cells"]}</b><span>missing values</span><br><i>8 cost, 10 satisfaction</i></div>'
            f'<div class="stat"><b>{b4["distinct_department_labels"]} → {af["distinct_department_labels"]}</b><span>department labels</span><br><i>spelling and spacing fixed</i></div>'
            f'<div class="stat"><b>{b4["columns"]} → {af["columns"]}</b><span>columns</span><br><i>10 calculated fields added</i></div>'
            "</div>")
        with card("m_steps", "Cleaning and transformation log", "Every step is scripted in data_prep.py, so the result can be reproduced."):
            steps = pd.DataFrame(rep["steps"]).rename(columns={
                "step": "Step", "issue": "Issue found", "rows_affected": "Rows affected", "action": "What was done", "why": "Why"})
            st.html(html_table(steps))
        a, b = st.columns(2)
        with a, card("m_labels", "Inconsistent entries: department labels", "Raw spellings and the name each was mapped to."):
            lab = raw["department"].value_counts().rename_axis("Raw label").reset_index(name="Rows")
            lab["Cleaned to"] = lab["Raw label"].str.strip().str.lower().map({d.lower(): d for d in clean["department"].unique()})
            lab["Raw label"] = "'" + lab["Raw label"] + "'"
            lab["Changed"] = lab["Raw label"].str.strip("'") != lab["Cleaned to"]
            st.dataframe(lab.sort_values(["Cleaned to", "Rows"], ascending=[True, False])[["Raw label", "Cleaned to", "Rows", "Changed"]],
                         hide_index=True, height=330)
        with b:
            with card("m_rules", "Validation rules", "Number of rows failing each rule after cleaning."):
                rules = pd.DataFrame({"Rule": list(rep["rule_checks"]), "Rows failing": list(rep["rule_checks"].values())})
                rules["Result"] = rules["Rows failing"].map(lambda n: "Pass" if n == 0 else "Fail")
                st.dataframe(rules, hide_index=True, height=250)
            with card("m_limits", "Known limitations"):
                st.markdown("\n".join(f"- {x}" for x in rep["known_limitations"]))

    with t_model:
        a, b = st.columns([1.5, 1])
        with a, card("m_star", "Star schema", "One fact table at visit grain, eight dimensions, one bridge table."):
            st.graphviz_chart(docs.model_dot(rep["model_tables"]))
        with b:
            with card("m_tables", "Tables"):
                mt = pd.DataFrame([{"Table": k, "Rows": v["rows"], "Columns": v["columns"]} for k, v in rep["model_tables"].items()])
                st.dataframe(mt, hide_index=True, height=250)
            with card("m_rel", "Relationships"):
                st.dataframe(pd.DataFrame(docs.RELATIONSHIPS, columns=["From", "To", "Cardinality"]), hide_index=True, height=250)

    with t_kpi:
        with card("m_kpi", "KPI definitions", "Formula, purpose and interpretation of every KPI on the dashboard."):
            rows = []
            for k in K.KPIS.values():
                tgt = K.target_of(k, clean)
                rows.append({"KPI": k.label, "Formula": k.formula,
                             "Target": "" if tgt is None else f"{'≤' if k.good == 'low' else '≥'} {tgt:g}",
                             "Purpose": k.purpose, "Interpretation": k.interpretation})
            st.html(html_table(pd.DataFrame(rows)))

    with t_dict:
        with card("m_dict", "Data dictionary", "Fields in the cleaned dataset."):
            st.html(html_table(pd.DataFrame(docs.DICTIONARY, columns=["Field", "Type", "Description"])))

    with t_dl:
        with card("m_dl", "Project files", "The datasets required as deliverables."):
            a, b, c = st.columns(3)
            a.download_button("Raw dataset (CSV)", D.RAW_PATH.read_bytes(), file_name=D.RAW_PATH.name, mime="text/csv",
                              icon=":material/download:", width="stretch")
            b.download_button("Cleaned dataset (CSV)", D.CLEAN_PATH.read_bytes(), file_name=D.CLEAN_PATH.name, mime="text/csv",
                              icon=":material/download:", width="stretch")
            c.download_button("Star-schema tables (ZIP)", _model_zip(), file_name="data_model.zip", mime="application/zip",
                              icon=":material/download:", width="stretch")
        with card("m_prev", "Cleaned dataset preview", "First 100 rows."):
            st.dataframe(clean.head(100), hide_index=True, height=360)
