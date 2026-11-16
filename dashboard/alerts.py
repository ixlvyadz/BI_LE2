"""Attention panel: every point in the current selection that needs management attention.

Rules (all calculated from the visits in scope, so the list follows the sidebar filters):
  1. A hospital-wide KPI misses its target.
  2. A department misses a target (at least MIN_N visits).
  3. Half or more of a department's visits were handled under High Strain.
  4. A shift misses the wait or treatment-success target.
  5. The latest quarter in scope is off target.
  6. A meaningful share of visits waited longer than 60 minutes.
Severity: "critical" when the gap to target is large (see _severity), otherwise "warning".
"""
from __future__ import annotations

import pandas as pd

from . import data as D
from . import kpi as K

MIN_N = 15
PAGE = {"wait": "Patient flow", "noshow": "Patient flow", "occupancy": "Capacity", "readmit": "Quality",
        "satisfaction": "Quality", "success": "Quality"}
NOUN = {"wait": "wait time", "occupancy": "bed occupancy", "readmit": "readmission rate", "noshow": "no-show rate",
        "satisfaction": "patient satisfaction", "success": "treatment success"}


def _gap(k: K.KPI, v: float, tgt: float) -> float:
    """Relative distance from target, positive when off target."""
    return (v - tgt) / tgt if k.good == "low" else (tgt - v) / tgt


def _severity(k: K.KPI, gap: float) -> str:
    limit = 0.25 if k.good == "low" else 0.10   # "higher is better" KPIs sit close to their target, so 10% is already large
    return "critical" if gap >= limit else "warning"


def _item(sev: str, page: str, title: str, detail: str, score: float, value: str = "",
          kind: str = "overall", key: str = "", member: str = "") -> dict:
    """kind / key / member say what the alert is about, so the dashboard can open the right view when it is clicked."""
    return {"sev": sev, "page": page, "title": title, "detail": detail, "score": float(score), "value": value,
            "kind": kind, "key": key, "member": member}


def _vs(k: K.KPI, v: float, tgt: float) -> str:
    word = "above" if k.good == "low" else "below"
    unit = " points" if k.unit == "%" else " min" if k.unit == "min" else ""
    return f"{K.fmt(k, v)} against a target of {tgt:g}, {abs(v - tgt):.{max(k.decimals, 1)}f}{unit} {word}"


def build(df: pd.DataFrame) -> list[dict]:
    out: list[dict] = []
    if len(df) < MIN_N:
        return out

    for key in K.TARGETED:
        k = K.KPIS[key]
        tgt = K.target_of(k, df)

        # 1. hospital-wide
        v = k.calc(df)
        if K.meets(k, v, tgt) is False:
            g = _gap(k, v, tgt)
            out.append(_item(_severity(k, g), PAGE[key], f"Overall {NOUN[key]} is off target",
                             f"{_vs(k, v, tgt)} across {len(df):,} visits.", g + 1, K.fmt(k, v), "overall", key))

        # 2. by department
        for _, r in K.by_dim(df, key, "department", min_n=MIN_N).iterrows():
            if K.meets(k, r["value"], tgt) is False:
                g = _gap(k, r["value"], tgt)
                out.append(_item(_severity(k, g), PAGE[key], f"{D.short(r['label'])}: {NOUN[key]} off target",
                                 f"{_vs(k, r['value'], tgt)} ({int(r['n']):,} visits).", g, K.fmt(k, r["value"]),
                                 "department", key, r["label"]))

        # 4. by shift (access and outcome only)
        if key in ("wait", "success"):
            for _, r in K.by_dim(df, key, "shift", min_n=2 * MIN_N).iterrows():
                if K.meets(k, r["value"], tgt) is False:
                    g = _gap(k, r["value"], tgt)
                    out.append(_item(_severity(k, g), PAGE[key], f"{r['label']} shift: {NOUN[key]} off target",
                                     f"{_vs(k, r['value'], tgt)} ({int(r['n']):,} visits).", g, K.fmt(k, r["value"]),
                                     "shift", key, r["label"]))

        # 5. latest quarter
        quarters = sorted(df["quarter"].unique())
        if len(quarters) > 1:
            last = df[df["quarter"] == quarters[-1]]
            if len(last) >= MIN_N:
                v = k.calc(last)
                if K.meets(k, v, tgt) is False:
                    g = _gap(k, v, tgt)
                    out.append(_item(_severity(k, g), PAGE[key], f"Latest quarter ({quarters[-1]}): {NOUN[key]} off target",
                                     f"{_vs(k, v, tgt)} ({len(last):,} visits).", g, K.fmt(k, v), "quarter", key, quarters[-1]))

    # 3. units running under High Strain
    for _, r in K.by_dim(df, "high_strain", "department", min_n=MIN_N).iterrows():
        if r["value"] >= 50:
            out.append(_item("critical", "Capacity", f"{D.short(r['label'])}: most visits handled under High Strain",
                             f"{r['value']:.0f}% of its {int(r['n']):,} visits carried a red capacity alert.",
                             r["value"] / 100 + 0.5, f"{r['value']:.0f}%", "department", "high_strain", r["label"]))

    # 6. very long waits
    long_wait = df[df["er_wait_time_minutes"] > 60]
    share = len(long_wait) / len(df) * 100
    if len(long_wait) >= 5 and share >= 5:
        out.append(_item("critical" if share >= 15 else "warning", "Patient flow", "Patients waiting more than 60 minutes",
                         f"{len(long_wait):,} visits ({share:.1f}%) waited over an hour; their satisfaction averages "
                         f"{long_wait['patient_satisfaction_score'].mean():.2f} / 5.", share / 100 + 0.2, f"{len(long_wait):,}", "longwait", "wait"))

    rank = {"critical": 0, "warning": 1}
    return sorted(out, key=lambda a: (rank[a["sev"]], -a["score"]))
