"""KPI catalogue (formula, purpose, interpretation, target) and the calculations behind every tile."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from . import theme


@dataclass(frozen=True)
class KPI:
    key: str
    label: str
    unit: str            # "", "min", "%", "/ 5", "days", "$"
    decimals: int
    calc: Callable[[pd.DataFrame], float]
    icon: str
    target_col: str | None   # column holding the target value
    good: str | None         # "low"  -> at or below target is good, "high" -> at or above is good
    formula: str
    purpose: str
    interpretation: str


def _mean(col: str) -> Callable[[pd.DataFrame], float]:
    return lambda d: float(d[col].mean()) if len(d) else float("nan")


def _rate(col: str) -> Callable[[pd.DataFrame], float]:
    return lambda d: float(d[col].mean() * 100) if len(d) else float("nan")


KPIS: dict[str, KPI] = {k.key: k for k in [
    KPI("visits", "Patient visits", "", 0, lambda d: float(len(d)), "users", None, None,
        "COUNT(visit_id)",
        "Measures demand on the hospital and is the denominator of every rate.",
        "Rising volume with flat capacity signals pressure; compare by month, department and shift to plan staffing."),
    KPI("wait", "Average wait time", "min", 1, _mean("er_wait_time_minutes"), "clock", "target_er_wait_time", "low",
        "SUM(er_wait_time_minutes) / COUNT(visit_id)",
        "Tracks how quickly patients are seen, the main access-to-care measure.",
        "At or below 35 minutes meets the target. Higher values point to triage or staffing bottlenecks."),
    KPI("occupancy", "Bed occupancy rate", "%", 1, _mean("bed_occupancy_rate"), "bed", "target_bed_occupancy_rate", "low",
        "AVERAGE(bed_occupancy_rate)",
        "Shows how full the units are when patients are treated.",
        "85% is treated as the safe ceiling: above it there is little room for surges; far below it beds are under-used."),
    KPI("readmit", "30-day readmission rate", "%", 1, _rate("readmitted_30_days"), "repeat", "target_readmission_rate", "low",
        "SUM(readmitted_30_days) / COUNT(visit_id) x 100",
        "Quality-of-care indicator: patients returning within 30 days of discharge.",
        "At or below 12% meets the target. Higher rates suggest early discharge or weak follow-up."),
    KPI("noshow", "No-show rate", "%", 1, _rate("no_show"), "calendar", "target_no_show_rate", "low",
        "SUM(no_show) / COUNT(visit_id) x 100",
        "Measures appointment slots lost because patients did not attend.",
        "At or below 10% meets the target. Higher rates waste clinician time and delay other patients."),
    KPI("satisfaction", "Patient satisfaction", "/ 5", 2, _mean("patient_satisfaction_score"), "smile",
        "target_satisfaction_score", "high",
        "AVERAGE(patient_satisfaction_score)",
        "Summarises the patient's experience on a 1-5 scale.",
        "4.2 or above meets the target. A fall usually follows longer waits or poorer outcomes."),
    KPI("success", "Treatment success rate", "%", 1, _rate("treatment_success"), "check",
        "target_treatment_success_rate", "high",
        "SUM(treatment_success) / COUNT(visit_id) x 100",
        "Share of visits where treatment was recorded as successful.",
        "88% or above meets the target. Lower values need review by department, shift and severity."),
    KPI("cost", "Average cost per visit", "$", 0, _mean("estimated_cost_per_visit"), "wallet", None, None,
        "SUM(estimated_cost_per_visit) / COUNT(visit_id)",
        "Shows how resource-intensive a typical visit is.",
        "No target in the data; compare departments and severities, and watch the trend against volume."),
    KPI("total_cost", "Total estimated cost", "$", 0, lambda d: float(d["estimated_cost_per_visit"].sum()), "wallet", None, None,
        "SUM(estimated_cost_per_visit)",
        "Total cost of care delivered in the selected scope.",
        "Used with visit share to see where cost concentrates."),
    KPI("los", "Average length of stay", "days", 1, _mean("length_of_stay_days"), "layers", None, None,
        "AVERAGE(length_of_stay_days)",
        "Indicates bed-days consumed per visit; the main driver of occupancy.",
        "Longer stays tie up beds. Compare within a department over time rather than across departments."),
    KPI("wait_breach", "Visits over wait target", "%", 1, _rate("wait_over_target"), "alert", None, None,
        "COUNT(visits where er_wait_time_minutes > 35) / COUNT(visit_id) x 100",
        "Shows how many patients actually experience a long wait, which an average can hide.",
        "Lower is better. A high share with an acceptable average means the problem is concentrated."),
    KPI("occ_breach", "Visits above 85% occupancy", "%", 1, _rate("occupancy_over_target"), "alert", None, None,
        "COUNT(visits where bed_occupancy_rate > 85) / COUNT(visit_id) x 100",
        "Share of visits handled while the unit was over the occupancy ceiling.",
        "Lower is better. Persistently high values mean a structural bed shortage."),
    KPI("utilization", "Resource utilization index", "/ 100", 1, _mean("resource_utilization_index"), "gauge", None, None,
        "AVERAGE(resource_utilization_index)",
        "Composite 0-100 index of staff, equipment and room use per visit.",
        "Values near 100 mean the unit is running with no slack."),
    KPI("high_strain", "High-strain visits", "%", 1, _rate("high_strain"), "pulse", None, None,
        "COUNT(visits where capacity_status = 'High Strain') / COUNT(visit_id) x 100",
        "Share of visits delivered while capacity status was High Strain (red alert).",
        "Lower is better; it flags where escalation plans are being triggered."),
    KPI("completed", "Appointments completed", "%", 1, _rate("appointment_completed"), "check", None, None,
        "SUM(appointment_completed) / COUNT(visit_id) x 100",
        "Share of visits completed as planned.",
        "Higher is better; the gap to 100% is no-shows plus visits needing a follow-up."),
]}

HEADLINE = ["visits", "wait", "occupancy", "readmit", "noshow", "satisfaction", "success", "cost"]
TARGETED = ["wait", "occupancy", "readmit", "noshow", "satisfaction", "success"]


def target_of(k: KPI, df: pd.DataFrame) -> float | None:
    if not k.target_col or df.empty:
        return None
    return float(df[k.target_col].iloc[0])


def meets(k: KPI, value: float, target: float | None) -> bool | None:
    if target is None or value != value:
        return None
    value = round(value, 6)  # guard against float noise such as 12.000000000000002 vs a 12% target
    return value <= target if k.good == "low" else value >= target


def fmt(k: KPI | str, v: float, with_unit: bool = True) -> str:
    k = KPIS[k] if isinstance(k, str) else k
    if v is None or v != v:
        return "n/a"
    if k.unit == "$":
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.2f}M"
        if abs(v) >= 100_000:
            return f"${v / 1_000:.0f}K"
        return f"${v:,.0f}"
    s = f"{v:,.{k.decimals}f}"
    if not with_unit or not k.unit:
        return s
    return f"{s}%" if k.unit == "%" else f"{s} {k.unit}"


def series(df: pd.DataFrame, key: str, grain: str = "Quarter") -> pd.DataFrame:
    """KPI value per period. grain: Year | Quarter | Month."""
    k = KPIS[key]
    col = {"Year": "year", "Quarter": "quarter", "Month": "month_start"}[grain]
    rows = [(p, k.calc(g), len(g)) for p, g in df.groupby(col, sort=True)]
    out = pd.DataFrame(rows, columns=["period", "value", "n"])
    if grain == "Year":
        out["period"] = out["period"].astype(str)
    return out


def by_dim(df: pd.DataFrame, key: str, dim: str, min_n: int = 1) -> pd.DataFrame:
    """KPI value per member of a dimension, with the visit count behind it."""
    k = KPIS[key]
    rows = [(str(m), k.calc(g), len(g)) for m, g in df.groupby(dim, sort=False) if len(g) >= min_n]
    return pd.DataFrame(rows, columns=["label", "value", "n"])


def year_delta(df: pd.DataFrame, key: str, min_n: int = 20):
    """Latest year in scope vs the year before, like for like (only months present in both years).

    Returns (difference, latest_year, previous_year, full_year) or None.
    """
    k = KPIS[key]
    years = sorted(y for y, g in df.groupby("year") if len(g) >= min_n)
    if len(years) < 2:
        return None
    cur, prev = years[-1], years[-2]
    a, b = df[df["year"] == cur], df[df["year"] == prev]
    common = set(a["month_num"]) & set(b["month_num"])
    a, b = a[a["month_num"].isin(common)], b[b["month_num"].isin(common)]
    if len(a) < min_n or len(b) < min_n:
        return None
    va, vb = k.calc(a), k.calc(b)
    if va != va or vb != vb:
        return None
    return va - vb, int(cur), int(prev), len(common) == 12


def scorecard(df: pd.DataFrame, dim: str = "department") -> pd.DataFrame:
    """One row per member with the six targeted KPIs, visits and how many targets are missed."""
    rows = []
    for m, g in df.groupby(dim, sort=False):
        r = {"label": str(m), "visits": len(g)}
        missed = 0
        for key in TARGETED:
            k = KPIS[key]
            v = k.calc(g)
            ok = meets(k, v, target_of(k, g))
            r[key] = v
            r[f"{key}_ok"] = ok
            missed += int(ok is False)
        r["missed"] = missed
        rows.append(r)
    out = pd.DataFrame(rows)
    return out.sort_values(["missed", "visits"], ascending=[False, False]).reset_index(drop=True) if len(out) else out


# ---- HTML tiles ------------------------------------------------------------------------------
def tile_html(df: pd.DataFrame, key: str, compact: bool = False, spark: bool = True, label: str | None = None) -> str:
    k = KPIS[key]
    v = k.calc(df)
    tgt = target_of(k, df)
    ok = meets(k, v, tgt)
    

    if k.unit == "$":
        value_html = theme.esc(fmt(k, v))
    else:
        unit = "" if not k.unit else f"<small>{theme.esc(k.unit)}</small>"
        value_html = f"{theme.esc(fmt(k, v, with_unit=False))}{unit}"

    foot = []
    if ok is not None:
        sign = "≤" if k.good == "low" else "≥"
        tgt_txt = f"{tgt:g}" + ("%" if k.unit == "%" else "")
        if ok:
            foot.append(theme.pill(f"On target {sign} {tgt_txt}", "good", "✓"))
        else:
            gap = abs(v - tgt)
            word = "over" if k.good == "low" else "under"
            foot.append(theme.pill(f"{gap:.{max(k.decimals, 1)}f} {word} target {tgt_txt}", "crit", "⚠"))
    if not compact:
        d = year_delta(df, key)
        if d:
            diff, cur, prev, full_year = d
            ref = f"vs {prev}" if full_year else f"vs same months {prev}"
            if round(diff, k.decimals) == 0:
                foot.append(f'<span class="kpi-d">● No change {ref}</span>')
            else:
                arrow = "▲" if diff > 0 else "▼"
                if k.unit == "$":
                    txt = f"{'+' if diff >= 0 else '-'}${abs(diff):,.0f}"
                else:
                    txt = f"{diff:+,.{k.decimals}f}" + (" pts" if k.unit == "%" else "")
                cls = ""
                if k.good:
                    improving = (diff < 0) == (k.good == "low")
                    cls = ("down" if diff < 0 else "up") + ("-good" if improving else "-bad")
                foot.append(f'<span class="kpi-d {cls}">{arrow} {theme.esc(txt)} {ref}</span>')

    spark_html = ""
    if spark and not compact:
        s = series(df, key, "Quarter")
        spark_html = theme.sparkline(s["value"].tolist())

    classes = "kpi" + (" alert" if ok is False else "") + (" compact" if compact else "")
    return (
        f'<div class="{classes}"><div class="kpi-top"><span class="kpi-ic">{theme.icon(k.icon, color=theme.BLUE_DEEP if ok is False else "#ffffff")}</span>'
        f'<span class="kpi-l">{theme.esc(label or k.label)}</span></div>'
        f'<div class="kpi-v">{value_html}</div>{spark_html}'
        f'<div class="kpi-f">{"".join(foot)}</div></div>'
    )


def tiles(df: pd.DataFrame, keys: list[str], compact: bool = False, cols: int = 4) -> str:
    cls = "kpis c5" if cols == 5 else "kpis"
    return f'<div class="{cls}">' + "".join(tile_html(df, k, compact=compact) for k in keys) + "</div>"
