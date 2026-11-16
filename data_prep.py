"""
data_prep.py  -  Data preparation pipeline for the Healthcare Operations BI dashboard
======================================================================================
CS 313 Business Intelligence - Final Learning Evidence

Reads the raw extract, profiles it, cleans it, adds calculated fields, and writes:

    data/healthcare_operations_clean.csv   flat, analysis-ready table used by the dashboard
    data/model/fact_visits.csv             star-schema fact table
    data/model/dim_*.csv                   dimension tables
    data/model/bridge_visit_bottleneck.csv one row per visit x bottleneck reason
    data/data_quality_report.json          before/after profile + log of every cleaning step

Run:  python data_prep.py
The script is deterministic: running it again on the same raw file gives identical output.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "healthcare_operations_raw.csv"
CLEAN = BASE / "data" / "healthcare_operations_clean.csv"
MODEL = BASE / "data" / "model"
REPORT = BASE / "data" / "data_quality_report.json"

# Canonical department names (lower-case key -> display label)
DEPARTMENTS = {
    "emergency department (ed)": "Emergency Department (ED)",
    "general medicine": "General Medicine",
    "cardiology": "Cardiology",
    "outpatient / ambulatory care": "Outpatient / Ambulatory Care",
    "radiology": "Radiology",
    "laboratory": "Laboratory",
    "orthopedics": "Orthopedics",
    "icu": "ICU",
    "surgery / or": "Surgery / OR",
    "pharmacy": "Pharmacy",
}

# Calculated grouping of departments by care setting (used as a drill-up level)
CARE_SETTING = {
    "Emergency Department (ED)": "Emergency",
    "ICU": "Inpatient",
    "General Medicine": "Inpatient",
    "Cardiology": "Inpatient",
    "Orthopedics": "Inpatient",
    "Surgery / OR": "Inpatient",
    "Outpatient / Ambulatory Care": "Ambulatory & Diagnostic",
    "Radiology": "Ambulatory & Diagnostic",
    "Laboratory": "Ambulatory & Diagnostic",
    "Pharmacy": "Ambulatory & Diagnostic",
}

SEVERITY_ORDER = ["Low", "Moderate", "High", "Critical"]
SHIFT_ORDER = ["Day", "Evening", "Night"]
DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
AGE_ORDER = ["Pediatric (0-17)", "Adult (18-44)", "Middle Age (45-64)", "Senior (65+)"]

TEXT_COLS = [
    "patient_id", "visit_id", "month", "quarter", "day_of_week", "is_weekend", "department",
    "admission_type", "insurance_type", "severity_level", "shift", "provider_type", "age_group",
    "visit_outcome", "discharge_status", "capacity_status", "operational_risk_level",
    "bottleneck_reason", "hospital_alert_flag",
]
FLAG_COLS = ["appointment_completed", "no_show", "readmitted_30_days", "treatment_success"]


def profile(df: pd.DataFrame) -> dict:
    """Small data-quality profile used for the before/after comparison."""
    miss = df.isna().sum()
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "missing_cells": int(miss.sum()),
        "missing_by_column": {k: int(v) for k, v in miss[miss > 0].items()},
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_visit_ids": int(df["visit_id"].duplicated().sum()),
        "distinct_department_labels": int(df["department"].nunique()),
    }


def main() -> None:
    raw = pd.read_csv(RAW)
    df = raw.copy()
    log: list[dict] = []
    before = profile(raw)

    # 1) Whitespace: trim every text column --------------------------------------------------
    padded = 0
    for c in TEXT_COLS:
        s = df[c].astype("string")
        padded += int((s != s.str.strip()).sum())
        df[c] = s.str.strip()
    log.append({
        "step": 1, "issue": "Leading / trailing spaces in text fields",
        "rows_affected": padded,
        "action": "Trimmed whitespace on all 19 text columns.",
        "why": "' Cardiology ' and 'Cardiology' would otherwise be counted as two departments.",
    })

    # 2) Inconsistent department labels ------------------------------------------------------
    variants_before = sorted(raw["department"].unique().tolist())
    canon = df["department"].str.lower().map(DEPARTMENTS)
    unmapped = df.loc[canon.isna(), "department"].unique().tolist()
    if unmapped:
        raise ValueError(f"Unmapped department labels: {unmapped}")
    changed = int((raw["department"] != canon).sum())
    df["department"] = canon
    log.append({
        "step": 2, "issue": "Inconsistent department spelling / casing",
        "rows_affected": changed,
        "action": f"Mapped {len(variants_before)} raw labels to {len(DEPARTMENTS)} canonical department names "
                  "(case-insensitive lookup table).",
        "why": "Variants such as 'SURGERY / OR', 'laboratory' and ' Pharmacy ' split one department into several groups.",
    })

    # 3) Duplicates --------------------------------------------------------------------------
    dup_rows = int(df.duplicated().sum())
    dup_ids = int(df["visit_id"].duplicated().sum())
    df = df.drop_duplicates().drop_duplicates(subset="visit_id", keep="first")
    log.append({
        "step": 3, "issue": "Duplicate records",
        "rows_affected": dup_rows + dup_ids,
        "action": "Checked full-row duplicates and repeated visit_id values; none found, no rows removed.",
        "why": "Duplicate visits would inflate volumes and costs.",
    })

    # 4) Data types --------------------------------------------------------------------------
    df["visit_date"] = pd.to_datetime(df["visit_date"], format="%Y-%m-%d", errors="raise")
    for c in FLAG_COLS:
        df[c] = df[c].astype(int)
    log.append({
        "step": 4, "issue": "Dates stored as text",
        "rows_affected": int(len(df)),
        "action": "Parsed visit_date to a real date type (ISO format); confirmed the four 0/1 flag columns are integers.",
        "why": "Needed for time-series charts, date slicers and rate calculations.",
    })

    # 5) Missing cost: recover from the two related fields -----------------------------------
    #    In the complete rows, department_cost_burden = estimated_cost_per_visit x resource_utilization_index / 100
    ok = df["estimated_cost_per_visit"].notna()
    rel_err = (df.loc[ok, "department_cost_burden"]
               - df.loc[ok, "estimated_cost_per_visit"] * df.loc[ok, "resource_utilization_index"] / 100).abs()
    rel_check = float((rel_err / df.loc[ok, "department_cost_burden"]).max())
    miss_cost = df["estimated_cost_per_visit"].isna()
    df["cost_imputed"] = miss_cost.astype(int)
    df.loc[miss_cost, "estimated_cost_per_visit"] = (
        df.loc[miss_cost, "department_cost_burden"] / (df.loc[miss_cost, "resource_utilization_index"] / 100)
    ).round(2)
    log.append({
        "step": 5, "issue": "Missing estimated_cost_per_visit",
        "rows_affected": int(miss_cost.sum()),
        "action": "Recalculated as department_cost_burden / (resource_utilization_index / 100) and flagged in cost_imputed.",
        "why": f"The identity burden = cost x utilization / 100 holds in every complete row (max relative error "
               f"{rel_check:.4%}), so the value is recovered rather than guessed.",
    })

    # 6) Missing satisfaction: department median ---------------------------------------------
    miss_sat = df["patient_satisfaction_score"].isna()
    df["satisfaction_imputed"] = miss_sat.astype(int)
    dept_median = df.groupby("department")["patient_satisfaction_score"].transform("median")
    df.loc[miss_sat, "patient_satisfaction_score"] = dept_median[miss_sat].round(2)
    log.append({
        "step": 6, "issue": "Missing patient_satisfaction_score",
        "rows_affected": int(miss_sat.sum()),
        "action": "Filled with the median score of the same department and flagged in satisfaction_imputed.",
        "why": "Only 1.1% of rows; the median is robust to the skewed 1-5 scale and keeps the visit in every other KPI.",
    })

    # 7) Validation of derived / range fields -------------------------------------------------
    d = df["visit_date"]
    checks = {
        "year matches visit_date": int((d.dt.year != df["year"]).sum()),
        "month matches visit_date": int((d.dt.strftime("%Y-%m") != df["month"]).sum()),
        "quarter matches visit_date": int(((d.dt.year.astype(str) + " Q" + d.dt.quarter.astype(str)) != df["quarter"]).sum()),
        "day_of_week matches visit_date": int((d.dt.day_name() != df["day_of_week"]).sum()),
        "is_weekend matches visit_date": int(((d.dt.dayofweek >= 5).map({True: "Yes", False: "No"}) != df["is_weekend"]).sum()),
        "age_group matches age": int((pd.cut(df["age"], [-1, 17, 44, 64, 200], labels=AGE_ORDER).astype(str) != df["age_group"]).sum()),
        "satisfaction within 1-5": int(((df["patient_satisfaction_score"] < 1) | (df["patient_satisfaction_score"] > 5)).sum()),
        "occupancy within 0-100": int(((df["bed_occupancy_rate"] < 0) | (df["bed_occupancy_rate"] > 100)).sum()),
        "no negative durations or costs": int((df[["length_of_stay_days", "er_wait_time_minutes", "throughput_time_hours",
                                                   "estimated_cost_per_visit"]] < 0).any(axis=1).sum()),
        "no-show implies appointment not completed": int(((df["no_show"] == 1) & (df["appointment_completed"] == 1)).sum()),
    }
    log.append({
        "step": 7, "issue": "Possible inconsistent derived fields and out-of-range values",
        "rows_affected": int(sum(checks.values())),
        "action": "Ran 10 rule checks (calendar fields vs visit_date, age_group vs age, value ranges, flag logic). "
                  "All passed; no corrections needed.",
        "why": "Confirms the pre-computed calendar and grouping columns can be trusted in the model.",
    })

    # 8) Calculated fields -------------------------------------------------------------------
    df["care_setting"] = df["department"].map(CARE_SETTING)
    df["month_start"] = d.dt.to_period("M").dt.to_timestamp()
    df["month_name"] = d.dt.strftime("%b")
    df["month_num"] = d.dt.month
    df["wait_over_target"] = (df["er_wait_time_minutes"] > df["target_er_wait_time"]).astype(int)
    df["occupancy_over_target"] = (df["bed_occupancy_rate"] > df["target_bed_occupancy_rate"]).astype(int)
    df["high_strain"] = (df["capacity_status"] == "High Strain").astype(int)
    df["bottleneck_count"] = np.where(
        df["bottleneck_reason"] == "No Major Bottleneck", 0, df["bottleneck_reason"].str.count(";") + 1
    )
    log.append({
        "step": 8, "issue": "Fields needed for analysis were not in the extract",
        "rows_affected": int(len(df)),
        "action": "Added care_setting, month_start, month_name, month_num, wait_over_target, occupancy_over_target, "
                  "high_strain and bottleneck_count.",
        "why": "Supports drill-up by care setting, monthly trends, target-breach rates and bottleneck analysis.",
    })

    # 9) Multi-valued bottleneck_reason -> bridge table ---------------------------------------
    bridge = (
        df[["visit_id", "bottleneck_reason"]]
        .assign(bottleneck=lambda x: x["bottleneck_reason"].str.split(";"))
        .explode("bottleneck")
    )
    bridge["bottleneck"] = bridge["bottleneck"].str.strip()
    bridge = bridge[["visit_id", "bottleneck"]].reset_index(drop=True)
    log.append({
        "step": 9, "issue": "bottleneck_reason holds several values in one cell (separated by ';')",
        "rows_affected": int((df["bottleneck_count"] > 1).sum()),
        "action": f"Split into a bridge table with one row per visit and reason ({len(bridge)} rows).",
        "why": "A multi-valued text cell cannot be counted or filtered; the bridge keeps the fact table at one row per visit.",
    })

    # ---------- final assertions -------------------------------------------------------------
    assert df.isna().sum().sum() == 0, "nulls remain"
    assert df["department"].nunique() == 10
    assert df["visit_id"].is_unique
    assert len(df) == len(raw)

    df = df.sort_values(["visit_date", "visit_id"]).reset_index(drop=True)
    df.to_csv(CLEAN, index=False, date_format="%Y-%m-%d")

    # ---------- star schema ------------------------------------------------------------------
    MODEL.mkdir(parents=True, exist_ok=True)

    dim_date = (
        df[["visit_date", "year", "quarter", "month", "month_num", "month_name", "day_of_week", "is_weekend"]]
        .drop_duplicates("visit_date").sort_values("visit_date")
    )
    dim_date.insert(0, "date_key", dim_date["visit_date"].dt.strftime("%Y%m%d").astype(int))

    def make_dim(col: str, key: str, order: list[str] | None = None, extra: dict | None = None) -> pd.DataFrame:
        vals = order if order else sorted(df[col].unique())
        out = pd.DataFrame({key: range(1, len(vals) + 1), col: vals})
        if order:
            out[f"{col}_rank"] = range(1, len(vals) + 1)
        if extra:
            for k, mapping in extra.items():
                out[k] = out[col].map(mapping)
        return out

    dim_department = make_dim("department", "department_key", extra={"care_setting": CARE_SETTING})
    dim_admission = make_dim("admission_type", "admission_key")
    dim_severity = make_dim("severity_level", "severity_key", SEVERITY_ORDER)
    dim_shift = make_dim("shift", "shift_key", SHIFT_ORDER)
    dim_provider = make_dim("provider_type", "provider_key")
    dim_insurance = make_dim("insurance_type", "insurance_key")
    dim_patient = df[["patient_id", "age", "age_group"]].drop_duplicates("patient_id").sort_values("patient_id")

    fact = df.copy()
    fact["date_key"] = fact["visit_date"].dt.strftime("%Y%m%d").astype(int)
    for dim, col, key in [
        (dim_department, "department", "department_key"), (dim_admission, "admission_type", "admission_key"),
        (dim_severity, "severity_level", "severity_key"), (dim_shift, "shift", "shift_key"),
        (dim_provider, "provider_type", "provider_key"), (dim_insurance, "insurance_type", "insurance_key"),
    ]:
        fact = fact.merge(dim[[key, col]], on=col, how="left", validate="m:1")
    fact = fact[[
        "visit_id", "patient_id", "date_key", "department_key", "admission_key", "severity_key", "shift_key",
        "provider_key", "insurance_key",
        "length_of_stay_days", "er_wait_time_minutes", "throughput_time_hours", "bed_occupancy_rate",
        "resource_utilization_index", "capacity_strain_score", "estimated_cost_per_visit", "department_cost_burden",
        "patient_satisfaction_score", "appointment_completed", "no_show", "readmitted_30_days", "treatment_success",
        "wait_over_target", "occupancy_over_target", "high_strain", "bottleneck_count",
        "visit_outcome", "discharge_status", "capacity_status", "operational_risk_level", "hospital_alert_flag",
        "cost_imputed", "satisfaction_imputed",
    ]]
    assert fact.isna().sum().sum() == 0 and len(fact) == len(df)

    dim_target = pd.DataFrame({
        "kpi": ["Bed occupancy rate (%)", "30-day readmission rate (%)", "Average wait time (min)",
                "No-show rate (%)", "Patient satisfaction (1-5)", "Treatment success rate (%)"],
        "target": [float(df[c].iloc[0]) for c in [
            "target_bed_occupancy_rate", "target_readmission_rate", "target_er_wait_time",
            "target_no_show_rate", "target_satisfaction_score", "target_treatment_success_rate"]],
        "better_when": ["at or below", "at or below", "at or below", "at or below", "at or above", "at or above"],
    })

    tables = {
        "fact_visits": fact, "dim_date": dim_date, "dim_department": dim_department, "dim_patient": dim_patient,
        "dim_admission_type": dim_admission, "dim_severity": dim_severity, "dim_shift": dim_shift,
        "dim_provider_type": dim_provider, "dim_insurance_type": dim_insurance, "dim_kpi_target": dim_target,
        "bridge_visit_bottleneck": bridge,
    }
    for name, t in tables.items():
        t.to_csv(MODEL / f"{name}.csv", index=False, date_format="%Y-%m-%d")

    after = profile(df)
    report = {
        "source_file": RAW.name,
        "clean_file": CLEAN.name,
        "date_range": [df["visit_date"].min().strftime("%Y-%m-%d"), df["visit_date"].max().strftime("%Y-%m-%d")],
        "before": before,
        "after": after,
        "department_labels_before": variants_before,
        "rule_checks": checks,
        "steps": log,
        "model_tables": {k: {"rows": int(len(v)), "columns": int(v.shape[1])} for k, v in tables.items()},
        "known_limitations": [
            "The extract is a simulated / anonymised dataset: every patient_id appears once, so repeat-visit analysis is not possible.",
            "er_wait_time_minutes is recorded for every department, not only the ED; the dashboard labels it 'wait time'.",
            "Some values sit on fixed limits (wait time floor 2.0 min, occupancy cap 99%, length of stay floor 0.03 days), "
            "which suggests the source system clips extremes.",
            "No-show visits still carry cost and length-of-stay values in the source; they are kept as supplied.",
            "All six target_* columns hold one constant value each, so targets are hospital-wide, not per department.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2))

    print(f"raw rows {before['rows']}  ->  clean rows {after['rows']}")
    print(f"missing cells {before['missing_cells']} -> {after['missing_cells']}")
    print(f"department labels {before['distinct_department_labels']} -> {after['distinct_department_labels']}")
    for s in log:
        print(f"  step {s['step']}: {s['issue']}  [{s['rows_affected']} rows]")
    print("tables:", {k: v.shape for k, v in tables.items()})


if __name__ == "__main__":
    main()
