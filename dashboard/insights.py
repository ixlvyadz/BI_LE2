"""Business insights, generated from whatever is in scope so the numbers always match the charts.

Every insight answers the four questions in the project brief:
what was discovered, what data supports it, why it matters, what management should do.
An insight is only returned when its condition holds for the current selection.
"""
from __future__ import annotations

import pandas as pd

from . import data as D
from . import kpi as K

MIN_N = 15  # smallest group we are willing to quote a rate for


def _v(df: pd.DataFrame, key: str) -> float:
    return K.KPIS[key].calc(df)


def _tgt(df: pd.DataFrame, key: str) -> float:
    return K.target_of(K.KPIS[key], df)


def _names(labels: list[str]) -> str:
    labels = [D.short(x) for x in labels]
    if len(labels) <= 1:
        return "".join(labels)
    return ", ".join(labels[:-1]) + " and " + labels[-1]


# 1 ---------------------------------------------------------------------------------------------
def wait_hotspot(df: pd.DataFrame) -> dict | None:
    tgt = _tgt(df, "wait")
    d = K.by_dim(df, "wait", "department", min_n=MIN_N).sort_values("value", ascending=False)
    if d.empty or d.iloc[0]["value"] <= tgt:
        return None
    top = d.iloc[0]
    g = df[df["department"] == top["label"]]
    name = D.short(top["label"])
    ev = (f"{name} averages {top['value']:.1f} minutes against a {tgt:g}-minute target, and "
          f"{_v(g, 'wait_breach'):.0f}% of its {len(g):,} visits wait longer than the target.")
    if len(d) > 1:
        nxt = d.iloc[1]
        ev += f" The next-longest department, {D.short(nxt['label'])}, averages {nxt['value']:.1f} minutes."
    sh = K.by_dim(g, "wait", "shift", min_n=10).sort_values("value", ascending=False)
    worst_shift = None
    if len(sh) > 1:
        worst_shift = sh.iloc[0]["label"]
        ev += f" Inside {name} the {worst_shift} shift is slowest at {sh.iloc[0]['value']:.1f} minutes."
    hi, lo = g[g["severity_level"].isin(["High", "Critical"])], g[g["severity_level"] == "Low"]
    inverted = len(hi) >= 10 and len(lo) >= 10 and _v(hi, "wait") > _v(lo, "wait")
    if inverted:
        ev += (f" High and Critical patients wait {_v(hi, 'wait'):.1f} minutes there, longer than Low-severity "
               f"patients ({_v(lo, 'wait'):.1f}).")
    action = f"Open a fast-track stream for low-acuity {name} cases"
    if worst_shift:
        action += f" and move triage and physician cover toward the {worst_shift} shift"
    action += "."
    if inverted:
        action += " Audit triage so the sickest patients are seen first."
    return {
        "tag": "Access",
        "title": f"{name} waits are {top['value'] / tgt:.1f}x the target",
        "found": f"Long waits are concentrated in one department: {name}.",
        "evidence": ev,
        "why": (f"Wait time is the main access-to-care measure, and {name} handles {len(g) / len(df):.0%} of the visits "
                "in scope, so this one unit produces most of the long-wait experience."),
        "action": action,
    }


# 2 ---------------------------------------------------------------------------------------------
def long_wait_impact(df: pd.DataFrame) -> dict | None:
    a, b = df[df["er_wait_time_minutes"] > 60], df[df["er_wait_time_minutes"] <= 60]
    if len(a) < MIN_N or len(b) < MIN_N or _v(a, "satisfaction") >= _v(b, "satisfaction"):
        return None
    bands = K.by_dim(b, "satisfaction", "wait_band", min_n=MIN_N)
    why = f"Only {len(a) / len(df):.0%} of visits cross 60 minutes, so a small group carries the damage."
    if len(bands) > 1:
        why = (f"Below 60 minutes satisfaction barely moves ({bands['value'].min():.2f} to {bands['value'].max():.2f} "
               f"across wait bands), so the damage sits in a small group: {len(a) / len(df):.0%} of visits.")
    return {
        "tag": "Quality",
        "title": "Past 60 minutes, satisfaction and outcomes drop sharply",
        "found": "Waiting itself is tolerated; waiting more than an hour is not.",
        "evidence": (f"The {len(a):,} visits that waited over 60 minutes scored {_v(a, 'satisfaction'):.2f} / 5 for "
                     f"satisfaction versus {_v(b, 'satisfaction'):.2f} for everyone else. Their treatment success was "
                     f"{_v(a, 'success'):.1f}% versus {_v(b, 'success'):.1f}%, and 30-day readmission "
                     f"{_v(a, 'readmit'):.1f}% versus {_v(b, 'readmit'):.1f}%."),
        "why": why + " This is an association, not proof of cause: sicker patients may also wait longer.",
        "action": ("Set an escalation trigger at 45 minutes (charge-nurse review) so no patient crosses 60, and report "
                   "'visits over 60 minutes' as its own KPI."),
    }


# 3 ---------------------------------------------------------------------------------------------
def capacity_pressure(df: pd.DataFrame) -> dict | None:
    tgt = _tgt(df, "occupancy")
    d = K.by_dim(df, "occupancy", "department", min_n=MIN_N).sort_values("value", ascending=False)
    over = d[d["value"] > tgt]
    if over.empty:
        return None
    top = over.iloc[0]
    g = df[df["department"] == top["label"]]
    name = D.short(top["label"])
    ev = (f"{name} runs at {top['value']:.1f}% average occupancy against the {tgt:g}% ceiling. "
          f"{_v(g, 'occ_breach'):.0f}% of its visits happened above the ceiling, {_v(g, 'high_strain'):.0f}% were "
          f"flagged High Strain, and the average stay is {_v(g, 'los'):.1f} days.")
    for _, r in over.iloc[1:3].iterrows():
        g2 = df[df["department"] == r["label"]]
        ev += (f" {D.short(r['label'])} is also over at {r['value']:.1f}%, with {_v(g2, 'occ_breach'):.0f}% of visits "
               "above the ceiling.")
    return {
        "tag": "Capacity",
        "title": f"{name} is running above the safe occupancy ceiling",
        "found": f"{len(over)} department{'s' if len(over) > 1 else ''} exceed{'s' if len(over) == 1 else ''} the "
                 f"{tgt:g}% bed-occupancy ceiling: {_names(over['label'].tolist())}.",
        "evidence": ev,
        "why": (f"A unit above {tgt:g}% has no room for a surge. {name} also records a {_v(g, 'readmit'):.0f}% "
                f"readmission rate and {_v(g, 'success'):.0f}% treatment success, against {_v(df, 'readmit'):.0f}% and "
                f"{_v(df, 'success'):.0f}% for all visits in scope."),
        "action": (f"Create step-down beds or a discharge lounge for {name}, review every stay longer than "
                   f"{_v(g, 'los'):.0f} days daily, and pre-authorise overflow once occupancy passes {tgt:g}%."),
    }


# 4 ---------------------------------------------------------------------------------------------
def cost_concentration(df: pd.DataFrame) -> dict | None:
    g = df.groupby("department").agg(visits=("visit_id", "count"), cost=("estimated_cost_per_visit", "sum"))
    if len(g) < 3 or g["cost"].sum() <= 0:
        return None
    g["vs"] = g["visits"] / g["visits"].sum() * 100
    g["cs"] = g["cost"] / g["cost"].sum() * 100
    g = g.sort_values("cs", ascending=False)
    top, top3 = g.iloc[0], g.iloc[:3]
    if top["cs"] < 1.5 * top["vs"]:
        return None
    name = D.short(g.index[0])
    sub = df[df["department"] == g.index[0]]
    action = f"Focus cost control on {_names(top3.index.tolist())} rather than spreading it across all departments."
    if _v(sub, "los") >= 1:
        per_day = _v(sub, "cost") / _v(sub, "los")
        action += (f" In {name}, each day removed from the {_v(sub, 'los'):.1f}-day average stay is worth roughly "
                   f"${per_day:,.0f} per visit.")
    return {
        "tag": "Cost",
        "title": f"{name} is {top['vs']:.0f}% of visits but {top['cs']:.0f}% of cost",
        "found": "Cost is concentrated in a few high-acuity departments.",
        "evidence": (f"{name} handles {top['vs']:.1f}% of visits and {top['cs']:.1f}% of estimated cost "
                     f"({K.fmt('total_cost', top['cost'])}), at {K.fmt('cost', _v(sub, 'cost'))} per visit against "
                     f"{K.fmt('cost', _v(df, 'cost'))} overall. The top three cost centres "
                     f"({_names(top3.index.tolist())}) account for {top3['cs'].sum():.0f}% of cost from "
                     f"{top3['vs'].sum():.0f}% of visits."),
        "why": ("A small change in length of stay or resource use in these units moves the hospital total far more "
                "than any saving in the high-volume, low-cost departments."),
        "action": action,
    }


# 5 ---------------------------------------------------------------------------------------------
def readmission_groups(df: pd.DataFrame) -> dict | None:
    tgt = _tgt(df, "readmit")
    overall = _v(df, "readmit")
    d = K.by_dim(df, "readmit", "department", min_n=MIN_N).sort_values("value", ascending=False)
    over = d[d["value"] > tgt]
    if over.empty:
        return None
    listed = ", ".join(f"{D.short(r['label'])} ({r['value']:.1f}%)" for _, r in over.head(3).iterrows())
    state = "meets" if K.meets(K.KPIS["readmit"], overall, tgt) else "misses"
    ev = f"The overall rate of {overall:.1f}% {state} the {tgt:g}% target, but these departments are above it: {listed}."
    groups = []
    old, young = df[df["age_group"] == "Senior (65+)"], df[df["age_group"] != "Senior (65+)"]
    if len(old) >= MIN_N and len(young) >= MIN_N and _v(old, "readmit") > _v(young, "readmit"):
        ev += f" Seniors (65+) return at {_v(old, 'readmit'):.1f}% compared with {_v(young, 'readmit'):.1f}% for younger patients."
        groups.append("seniors")
    hi = df[df["severity_level"].isin(["High", "Critical"])]
    lo = df[df["severity_level"].isin(["Low", "Moderate"])]
    if len(hi) >= MIN_N and len(lo) >= MIN_N and _v(hi, "readmit") > _v(lo, "readmit"):
        ev += f" High and Critical cases return at {_v(hi, 'readmit'):.1f}% against {_v(lo, 'readmit'):.1f}% for Low and Moderate."
        groups.append("High and Critical cases")
    who = " and ".join(groups) if groups else "patients"
    return {
        "tag": "Quality",
        "title": "Readmissions come from a few identifiable groups",
        "found": f"The hospital-wide readmission rate hides {len(over)} department{'s' if len(over) > 1 else ''} above target.",
        "evidence": ev,
        "why": ("Because the risk groups can be identified before discharge, readmissions here are preventable work "
                "rather than random variation, and each one re-uses a bed in units that are already full."),
        "action": (f"Add a discharge checklist and a 72-hour follow-up call for {who} leaving "
                   f"{_names(over['label'].head(2).tolist())}."),
    }


# 6 ---------------------------------------------------------------------------------------------
def success_gap(df: pd.DataFrame) -> dict | None:
    tgt = _tgt(df, "success")
    overall = _v(df, "success")
    sh = K.by_dim(df, "success", "shift", min_n=MIN_N).sort_values("value")
    if overall >= tgt and (sh.empty or sh.iloc[0]["value"] >= tgt):
        return None
    missed = [k for k in K.TARGETED if K.meets(K.KPIS[k], _v(df, k), _tgt(df, k)) is False]
    ev = f"Treatment success is {overall:.1f}% against a target of {tgt:g}%"
    ev += ", the only one of the six targets missed." if missed == ["success"] else "."
    worst = best = None
    if len(sh) > 1:
        worst, best = sh.iloc[0], sh.iloc[-1]
        ev += (f" The {worst['label']} shift achieves {worst['value']:.1f}% while the {best['label']} shift reaches "
               f"{best['value']:.1f}%.")
    crit = df[df["severity_level"] == "Critical"]
    if len(crit) >= MIN_N:
        ev += f" Critical cases succeed {_v(crit, 'success'):.1f}% of the time."
    dep = K.by_dim(df, "success", "department", min_n=MIN_N).sort_values("value")
    low = dep[dep["value"] < tgt].head(2)
    if len(low):
        ev += " Lowest departments: " + ", ".join(f"{D.short(r['label'])} ({r['value']:.1f}%)" for _, r in low.iterrows()) + "."
    if overall < tgt:
        title = f"Treatment success is {tgt - overall:.1f} points under target"
    else:
        title = f"The {worst['label']} shift is below the treatment-success target"
    action = "Review unsuccessful cases by department and severity each month."
    if worst is not None:
        action = (f"Audit unsuccessful {worst['label']}-shift cases, check senior clinician cover on that shift, and "
                  f"compare its handover practice with the {best['label']} shift.")
    return {
        "tag": "Quality",
        "title": title,
        "found": "Treatment success falls short, and the shortfall is uneven across shifts, severity levels and departments.",
        "evidence": ev,
        "why": ("Treatment success is the core quality measure. A gap between shifts points to staffing mix or handover "
                "as something to check, although case mix can also differ between shifts."),
        "action": action,
    }


# 7 ---------------------------------------------------------------------------------------------
def no_show_pockets(df: pd.DataFrame) -> dict | None:
    tgt = _tgt(df, "noshow")
    d = K.by_dim(df, "noshow", "department", min_n=MIN_N).sort_values("value", ascending=False)
    over = d[d["value"] > tgt]
    if over.empty:
        return None
    top = over.iloc[0]
    name = D.short(top["label"])
    ev = (f"{name} loses {top['value']:.1f}% of appointments to no-shows against a {tgt:g}% target "
          f"({_v(df, 'noshow'):.1f}% across all visits in scope).")
    if len(over) > 1:
        ev += " Also above target: " + ", ".join(f"{D.short(r['label'])} ({r['value']:.1f}%)" for _, r in over.iloc[1:3].iterrows()) + "."
    day = K.by_dim(df, "noshow", "day_of_week", min_n=MIN_N).sort_values("value", ascending=False)
    worst_day = None
    if len(day) > 1 and day.iloc[0]["value"] > tgt:
        worst_day = day.iloc[0]["label"]
        ev += f" {worst_day} is the worst day at {day.iloc[0]['value']:.1f}%."
    ins = K.by_dim(df, "noshow", "insurance_type", min_n=MIN_N).sort_values("value", ascending=False)
    if len(ins) > 1 and ins.iloc[0]["value"] > tgt:
        ev += f" {ins.iloc[0]['label']} patients miss {ins.iloc[0]['value']:.1f}% of appointments."
    slots = f"{name} and {worst_day} sessions" if worst_day else f"{name} sessions"
    return {
        "tag": "Demand",
        "title": f"No-shows are concentrated in {name}, not hospital-wide",
        "found": "The overall no-show rate looks fine, but specific clinics and days lose far more slots.",
        "evidence": ev,
        "why": (f"Each no-show is an unused clinician slot. {int(df['no_show'].sum()):,} visits in scope were no-shows, "
                "and they cluster where a reminder is cheapest to send."),
        "action": f"Send SMS reminders 48 and 24 hours ahead for {slots}, and overbook those sessions by the observed no-show rate.",
    }


# 8 ---------------------------------------------------------------------------------------------
def volume_cost_trend(df: pd.DataFrame) -> dict | None:
    months = df.groupby("year")["month_num"].nunique()
    years = sorted(int(y) for y, n in months.items() if n == 12)  # only compare complete years
    if len(years) < 2:
        return None
    a, b = df[df["year"] == years[0]], df[df["year"] == years[-1]]
    if len(a) < 2 * MIN_N or len(b) < 2 * MIN_N:
        return None
    dv = (len(b) - len(a)) / len(a) * 100
    dc = (_v(b, "cost") - _v(a, "cost")) / _v(a, "cost") * 100
    ev = (f"Visits went from {len(a):,} in {years[0]} to {len(b):,} in {years[-1]} ({dv:+.1f}%), while average cost per "
          f"visit moved from {K.fmt('cost', _v(a, 'cost'))} to {K.fmt('cost', _v(b, 'cost'))} ({dc:+.0f}%) and High-Strain "
          f"visits from {_v(a, 'high_strain'):.1f}% to {_v(b, 'high_strain'):.1f}%.")
    full = df[df["year"].isin(years)]
    q = full.groupby(full["quarter"].str[-2:]).size() / len(years)
    busiest = q.idxmax()
    qy = full.groupby(["year", full["quarter"].str[-2:]]).size().unstack(fill_value=0)
    every = bool((qy.idxmax(axis=1) == busiest).all())
    ev += (f" {busiest} is the busiest quarter {'in every year' if every else 'on average'} "
           f"({q.max():.0f} visits a year versus {q.drop(busiest).mean():.0f} in the other quarters).")
    if dv < 0 < dc:
        title, found = "Fewer visits, but each one costs more", "Volume is falling while cost per visit rises."
        why = ("Total cost is growing without volume growth, which points to higher acuity or longer stays "
               "rather than more patients.")
    elif dv > 0 and dc > 0:
        title, found = "Volume and cost per visit are both rising", "Demand and unit cost are growing together."
        why = "Growth on both sides compounds: the budget needs to scale faster than visit counts alone suggest."
    else:
        title, found = "Volume and cost per visit are moving apart", "Visit counts and unit cost follow different trends."
        why = "Visit counts alone no longer predict cost, so planning has to look at case mix."
    return {
        "tag": "Demand",
        "title": title,
        "found": found,
        "evidence": ev,
        "why": why,
        "action": (f"Budget on cost per visit and acuity mix instead of visit counts, and schedule extra beds and staff "
                   f"for {busiest} before it starts."),
    }


BUILDERS = [wait_hotspot, long_wait_impact, capacity_pressure, cost_concentration, readmission_groups,
            success_gap, no_show_pockets, volume_cost_trend]


def build(df: pd.DataFrame) -> list[dict]:
    out = []
    if len(df) < 2 * MIN_N:
        return out
    for fn in BUILDERS:
        r = fn(df)
        if r:
            r["n"] = len(out) + 1
            out.append(r)
    return out
