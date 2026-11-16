"""Plotly chart builders. Every chart shares one layout style, one palette and one hover format."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import data as D
from . import kpi as K
from . import theme as T

CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False, "doubleClick": False}
HOVER = dict(bgcolor=T.INK, bordercolor=T.INK, font=dict(family=T.FONT, size=13, color="#ffffff"), align="left")


def _style(fig: go.Figure, height: int, legend: bool = False, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margin or dict(l=6, r=18, t=10, b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=T.FONT, size=13, color=T.INK2),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12.5, color=T.INK2), itemclick=False, itemdoubleclick=False, traceorder="normal"),
        hoverlabel=HOVER, barcornerradius=8, dragmode=False, separators=".,",
    )
    fig.update_xaxes(zeroline=False, linecolor=T.AXIS, ticks="", tickfont=dict(color=T.MUTED, size=12),
                     automargin=True, fixedrange=True, showgrid=False)
    fig.update_yaxes(zeroline=False, showline=False, ticks="", tickfont=dict(color=T.MUTED, size=12), ticklabelstandoff=8,
                     automargin=True, fixedrange=True, gridcolor=T.GRID, gridwidth=1)
    return fig


def show(fig: go.Figure, key: str | None = None):
    return st.plotly_chart(fig, theme=None, config=CONFIG, key=key)


def pick(fig: go.Figure, key: str) -> str | None:
    """Render a bar chart whose bars can be clicked. Returns the full label of the clicked bar, else None."""
    fig.update_layout(clickmode="event+select")
    fig.update_traces(selector=dict(type="bar"), unselected=dict(marker=dict(opacity=1)))
    ev = st.plotly_chart(fig, theme=None, config=CONFIG, key=key, on_select="rerun", selection_mode="points")
    pts = ev["selection"]["points"] if ev and ev.get("selection") else []
    if not pts:
        return None
    cd = pts[0].get("customdata")
    return str(cd[0]) if cd else str(pts[0].get("y"))


def table_popover(frame: pd.DataFrame, label: str = "View data") -> None:
    """Table-view twin of a chart, so no value is reachable only through a tooltip."""
    with st.popover(label, icon=":material/table_rows:"):
        st.dataframe(frame, hide_index=True)


def _target_label(k: K.KPI, tgt: float) -> str:
    return f"Target {tgt:g}" + ("%" if k.unit == "%" else (" min" if k.unit == "min" else ""))


# ---- ranked / ordered horizontal bars ----------------------------------------------------------
def dim_bar(df: pd.DataFrame, key: str, dim: str, show_target: bool = True, min_n: int = 1,
            highlight: str | None = None, max_rows: int = 12) -> tuple[go.Figure, pd.DataFrame]:
    """One bar per member of `dim` for KPI `key`. Bars off target are marked with the status colour."""
    k = K.KPIS[key]
    d = K.by_dim(df, key, dim, min_n=min_n)
    if dim in D.ORDINAL:
        order = [m for m in D.ORDINAL[dim] if m in set(d["label"])]
        d = d.set_index("label").loc[order].reset_index()
    else:
        d = d.sort_values("value", ascending=False).head(max_rows).reset_index(drop=True)
    tgt = K.target_of(k, df) if show_target else None
    d["ok"] = [K.meets(k, v, tgt) for v in d["value"]]
    d["text"] = [K.fmt(k, v) for v in d["value"]]
    d["short"] = d["label"].map(D.short)

    fig = go.Figure()
    cats = d["short"].tolist()[::-1]  # first row on top
    hover = "<b>%{customdata[0]}</b><br>" + k.label + ": %{customdata[1]}<br>Visits: %{customdata[2]:,}<extra></extra>"

    def add(mask, color, name):
        sub = d[mask]
        if sub.empty:
            return
        fig.add_bar(
            y=sub["short"], x=sub["value"], orientation="h", name=name, marker=dict(color=color), width=0.56,
            text=sub["text"], textposition="outside", textfont=dict(color=T.INK, size=12.5), cliponaxis=False,
            customdata=sub[["label", "text", "n"]].values, hovertemplate=hover,
        )

    if tgt is not None and k.good:
        add(d["ok"] != False, T.ON_TARGET, "Within target")  # noqa: E712
        add(d["ok"] == False, T.OFF_TARGET, "Off target")     # noqa: E712
    elif highlight:
        add(d["label"] == highlight, T.BLUE, highlight)
        add(d["label"] != highlight, T.BLUE_SOFT, "Other")
    else:
        add(pd.Series(True, index=d.index), T.BLUE, k.label)

    vmax = max(float(d["value"].max()) if len(d) else 1.0, tgt or 0)
    legend = bool(tgt is not None and k.good and d["ok"].eq(False).any())
    height = max(210, 64 + 34 * len(d)) + (22 if legend else 0)
    _style(fig, height=height, legend=legend, margin=dict(l=6, r=22, t=(52 if legend else 26) if tgt else 10, b=6))
    fig.update_layout(barmode="overlay")
    if legend:  # lift the legend above the target label so the two never collide
        fig.update_layout(legend=dict(y=1 + 26 / max(height - 58, 1)))
    fig.update_yaxes(categoryorder="array", categoryarray=cats, showgrid=False, tickfont=dict(color=T.INK, size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=T.GRID, showline=False, range=[0, vmax * 1.2 or 1],
                     tickprefix="$" if k.unit == "$" else "", ticksuffix="%" if k.unit == "%" else "")
    if tgt is not None:
        fig.add_vline(x=tgt, line=dict(color=T.INK2, width=1.5, dash="dot"),
                      annotation=dict(text=_target_label(k, tgt), font=dict(size=11.5, color=T.INK2), yanchor="bottom"),
                      annotation_position="top")
    table = d[["label", "value", "n"]].rename(columns={"label": dim.replace("_", " ").title(), "value": k.label, "n": "Visits"})
    table[k.label] = table[k.label].round(max(k.decimals, 1))
    return fig, table


# ---- trend over time ---------------------------------------------------------------------------
def trend(df: pd.DataFrame, key: str, grain: str = "Quarter", height: int = 300) -> tuple[go.Figure, pd.DataFrame]:
    k = K.KPIS[key]
    s = K.series(df, key, grain)
    tgt = K.target_of(k, df)
    s["text"] = [K.fmt(k, v) for v in s["value"]]
    is_month = grain == "Month"
    xfmt = "%{x|%b %Y}" if is_month else "%{x}"
    fig = go.Figure()
    fig.add_scatter(
        x=s["period"], y=s["value"], mode="lines" if is_month else "lines+markers",
        line=dict(color=T.BLUE, width=3, shape="spline", smoothing=0.6),
        marker=dict(size=8, color=T.BLUE, line=dict(color="#ffffff", width=2)),
        fill="tozeroy" if key in ("visits", "total_cost") else None, fillcolor="rgba(107,225,239,0.22)",
        customdata=s[["text", "n"]].values, name=k.label,
        hovertemplate=f"<b>{xfmt}</b><br>{k.label}: %{{customdata[0]}}<br>Visits: %{{customdata[1]:,}}<extra></extra>",
    )
    if len(s):
        last = s.iloc[-1]
        fig.add_scatter(x=[last["period"]], y=[last["value"]], mode="markers+text", text=[last["text"]],
                        textposition="top center", textfont=dict(color=T.INK, size=12.5),
                        marker=dict(size=10, color=T.BLUE, line=dict(color="#ffffff", width=2)),
                        hoverinfo="skip", cliponaxis=False)
    _style(fig, height=height, margin=dict(l=6, r=44, t=24, b=6))
    lo, hi = (float(s["value"].min()), float(s["value"].max())) if len(s) else (0.0, 1.0)
    if tgt is not None:
        lo, hi = min(lo, tgt), max(hi, tgt)
        fig.add_hline(y=tgt, line=dict(color=T.INK2, width=1.5, dash="dot"),
                      annotation=dict(text=_target_label(k, tgt), font=dict(size=11.5, color=T.INK2)),
                      annotation_position="top left")
    pad = (hi - lo) * 0.25 or max(abs(hi) * 0.1, 1.0)
    if key in ("visits", "total_cost"):
        fig.update_yaxes(range=[0, hi * 1.2 or 1])
    else:
        fig.update_yaxes(range=[lo - pad, hi + pad])
    fig.update_yaxes(tickprefix="$" if k.unit == "$" else "", ticksuffix="%" if k.unit == "%" else "",
                     tickformat="~s" if k.unit == "$" else None, nticks=6)
    if is_month:
        fig.update_xaxes(tickformat="%b\n%Y", dtick="M3")
    else:
        fig.update_xaxes(type="category", tickangle=0)
        if grain == "Quarter" and len(s):  # "Q1 / 2024" on the first quarter of each year, "Q2".. after: no collisions
            labels = [str(p) for p in s["period"]]
            text = [f"{p[-2:]}<br>{p[:4]}" if (i == 0 or p.endswith("Q1")) else p[-2:] for i, p in enumerate(labels)]
            fig.update_xaxes(tickmode="array", tickvals=labels, ticktext=text)
    table = s[["period", "value", "n"]].rename(columns={"period": grain, "value": k.label, "n": "Visits"})
    if is_month:
        table[grain] = table[grain].dt.strftime("%Y-%m")
    table[k.label] = table[k.label].round(max(k.decimals, 1))
    return fig, table


def seasonality(df: pd.DataFrame, key: str = "visits", height: int = 300) -> tuple[go.Figure, pd.DataFrame]:
    """Month of year on the x-axis, one line per year: shows the seasonal pattern and year-on-year change."""
    k = K.KPIS[key]
    rows = [(int(y), int(m), k.calc(g), len(g)) for (y, m), g in df.groupby(["year", "month_num"])]
    d = pd.DataFrame(rows, columns=["year", "month_num", "value", "n"])
    fig = go.Figure()
    for y in sorted(d["year"].unique()):
        s = d[d["year"] == y].set_index("month_num").reindex(range(1, 13))
        txt = [K.fmt(k, v) if v == v else "" for v in s["value"]]
        fig.add_scatter(
            x=D.MONTH_ORDER, y=s["value"], mode="lines+markers", name=str(y), connectgaps=False,
            line=dict(color=T.YEAR_COLORS.get(y, T.MUTED), width=2.2),
            marker=dict(size=7, color=T.YEAR_COLORS.get(y, T.MUTED), line=dict(color="#ffffff", width=1.5)),
            customdata=txt, hovertemplate=f"<b>%{{x}} {y}</b><br>{k.label}: %{{customdata}}<extra></extra>",
        )
        valid = s["value"].dropna()
        if len(valid):
            m_last = int(valid.index[-1])
            fig.add_annotation(x=D.MONTH_ORDER[m_last - 1], y=float(valid.iloc[-1]), text=str(y), showarrow=False,
                               xanchor="left", xshift=8, font=dict(size=12, color=T.INK))
    _style(fig, height=height, legend=True, margin=dict(l=6, r=40, t=30, b=6))
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=D.MONTH_ORDER)
    fig.update_yaxes(rangemode="tozero" if key == "visits" else "normal",
                     ticksuffix="%" if k.unit == "%" else "", tickprefix="$" if k.unit == "$" else "")
    table = d.pivot(index="month_num", columns="year", values="value").round(1).reset_index()
    table.insert(0, "Month", table.pop("month_num").map(lambda m: D.MONTH_ORDER[m - 1]))
    table.columns = [str(c) for c in table.columns]
    return fig, table


# ---- part-to-whole -----------------------------------------------------------------------------
def capacity_donut(df: pd.DataFrame, height: int = 300) -> tuple[go.Figure, pd.DataFrame]:
    c = df["capacity_status"].value_counts().reindex(D.STATUS_ORDER).fillna(0).astype(int)
    c = c[c > 0]
    fig = go.Figure(go.Pie(
        labels=c.index, values=c.values, hole=0.68, sort=False, direction="clockwise", rotation=0,
        marker=dict(colors=[T.STATUS_COLORS[s] for s in c.index], line=dict(color="#ffffff", width=3)),
        textposition="outside", texttemplate="%{label}<br><b>%{percent:.0%}</b>", textfont=dict(size=12.5, color=T.INK),
        hovertemplate="<b>%{label}</b><br>%{value:,} visits (%{percent:.1%})<extra></extra>", automargin=True,
    ))
    _style(fig, height=height, margin=dict(l=24, r=24, t=24, b=24))
    fig.add_annotation(text=f"<b style='font-size:26px;color:{T.INK}'>{int(c.sum()):,}</b><br>"
                            f"<span style='font-size:12.5px;color:{T.INK2}'>visits</span>",
                       showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    table = pd.DataFrame({"Capacity status": c.index, "Visits": c.values,
                          "Share %": (c.values / max(int(c.sum()), 1) * 100).round(1)})
    return fig, table


def status_mix(df: pd.DataFrame, dim: str = "department") -> tuple[go.Figure, pd.DataFrame]:
    """100% stacked bars: share of visits in each capacity status, per member of `dim`."""
    ct = pd.crosstab(df[dim], df["capacity_status"]).reindex(columns=D.STATUS_ORDER, fill_value=0)
    share = ct.div(ct.sum(axis=1), axis=0) * 100
    if dim in D.ORDINAL:
        share = share.reindex([m for m in D.ORDINAL[dim] if m in share.index])
    else:
        share = share.sort_values(["High Strain", "Moderate Risk"], ascending=False)
    cats = [D.short(i) for i in share.index]
    fig = go.Figure()
    for s in D.STATUS_ORDER:
        vals = share[s].values
        fig.add_bar(
            y=cats, x=vals, orientation="h", name=s, width=0.6,
            marker=dict(color=T.STATUS_COLORS[s], line=dict(color="#ffffff", width=2)),
            text=[f"{v:.0f}%" if v >= 11 else "" for v in vals], textposition="inside", insidetextanchor="middle",
            textfont=dict(color="#ffffff" if s == "High Strain" else T.INK, size=12),
            customdata=list(zip([str(i) for i in share.index], ct[s].reindex(share.index).values)),
            hovertemplate="<b>%{customdata[0]}</b><br>" + s + ": %{x:.1f}% (%{customdata[1]:,} visits)<extra></extra>",
        )
    _style(fig, height=max(210, 70 + 34 * len(share)), legend=True, margin=dict(l=6, r=18, t=30, b=6))
    fig.update_layout(barmode="stack", barcornerradius=0, uniformtext=dict(minsize=11, mode="hide"))
    fig.update_yaxes(categoryorder="array", categoryarray=cats[::-1], showgrid=False, tickfont=dict(color=T.INK, size=12.5))
    fig.update_xaxes(range=[0, 100], ticksuffix="%", showgrid=True, gridcolor=T.GRID, showline=False)
    table = share.round(1).reset_index().rename(columns={dim: dim.replace("_", " ").title()})
    return fig, table


# ---- heatmap -----------------------------------------------------------------------------------
def heatmap(df: pd.DataFrame, key: str, rows: str, cols: str, min_n: int = 3, height: int = 300) -> tuple[go.Figure, pd.DataFrame]:
    k = K.KPIS[key]
    r_order = [m for m in D.ORDINAL.get(rows, sorted(df[rows].unique())) if m in set(df[rows])]
    c_order = [m for m in D.ORDINAL.get(cols, sorted(df[cols].unique())) if m in set(df[cols])]
    z, txt, cnt = [], [], []
    for r in r_order:
        zr, tr, nr = [], [], []
        for c in c_order:
            g = df[(df[rows] == r) & (df[cols] == c)]
            v = k.calc(g) if len(g) >= min_n else None
            zr.append(v)
            tr.append(K.fmt(k, v, with_unit=False) + ("%" if k.unit == "%" else "") if v is not None else "–")
            nr.append(len(g))
        z.append(zr); txt.append(tr); cnt.append(nr)
    fig = go.Figure(go.Heatmap(
        z=z, x=[D.short(c) for c in c_order], y=[D.short(r) for r in r_order], text=txt, texttemplate="%{text}",
        textfont=dict(size=12.5), customdata=cnt, colorscale=[[i / (len(T.SEQ_BLUES) - 1), c] for i, c in enumerate(T.SEQ_BLUES)],
        xgap=4, ygap=4, hoverongaps=False,
        colorbar=dict(thickness=10, len=0.85, outlinewidth=0, tickfont=dict(size=11, color=T.MUTED),
                      ticksuffix="%" if k.unit == "%" else "", title=dict(text="", side="right")),
        hovertemplate="<b>%{y} · %{x}</b><br>" + k.label + ": %{text}<br>Visits: %{customdata:,}<extra></extra>",
    ))
    _style(fig, height=height, margin=dict(l=6, r=6, t=10, b=6))
    fig.update_xaxes(side="bottom", showline=False, tickfont=dict(color=T.INK, size=12.5), type="category")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=T.INK, size=12.5), type="category")
    table = pd.DataFrame(z, index=r_order, columns=c_order).round(1).reset_index().rename(columns={"index": rows.replace("_", " ").title()})
    return fig, table


# ---- dumbbell: share of visits vs share of cost --------------------------------------------------
def cost_share_dumbbell(df: pd.DataFrame, dim: str = "department") -> tuple[go.Figure, pd.DataFrame]:
    g = df.groupby(dim).agg(visits=("visit_id", "count"), cost=("estimated_cost_per_visit", "sum"))
    g["visit_share"] = g["visits"] / g["visits"].sum() * 100
    g["cost_share"] = g["cost"] / g["cost"].sum() * 100
    g = g.sort_values("cost_share", ascending=False)
    cats = [D.short(i) for i in g.index]
    fig = go.Figure()
    xs, ys = [], []
    for c, a, b in zip(cats, g["visit_share"], g["cost_share"]):
        xs += [a, b, None]; ys += [c, c, None]
    fig.add_scatter(x=xs, y=ys, mode="lines", line=dict(color=T.AXIS, width=3), hoverinfo="skip", showlegend=False)
    full = [str(i) for i in g.index]
    fig.add_scatter(x=g["visit_share"], y=cats, mode="markers", name="Share of visits",
                    marker=dict(size=13, color=T.BLUE_SOFT, line=dict(color="#ffffff", width=2)),
                    customdata=list(zip(full, g["visits"])),
                    hovertemplate="<b>%{customdata[0]}</b><br>Share of visits: %{x:.1f}% (%{customdata[1]:,})<extra></extra>")
    fig.add_scatter(x=g["cost_share"], y=cats, mode="markers+text", name="Share of cost",
                    marker=dict(size=13, color=T.BLUE_DEEP, line=dict(color="#ffffff", width=2)),
                    text=[f"{v:.0f}%" for v in g["cost_share"]],
                    textposition=["middle right" if b >= a else "middle left" for a, b in zip(g["visit_share"], g["cost_share"])],
                    textfont=dict(size=12.5, color=T.INK), cliponaxis=False,
                    customdata=list(zip(full, g["cost"])),
                    hovertemplate="<b>%{customdata[0]}</b><br>Share of cost: %{x:.1f}% ($%{customdata[1]:,.0f})<extra></extra>")
    hi = float(max(g["visit_share"].max(), g["cost_share"].max())) if len(g) else 1.0
    _style(fig, height=max(230, 74 + 34 * len(g)), legend=True, margin=dict(l=6, r=26, t=30, b=6))
    fig.update_yaxes(categoryorder="array", categoryarray=cats[::-1], showgrid=False, tickfont=dict(color=T.INK, size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=T.GRID, showline=False, ticksuffix="%", range=[-hi * 0.06, hi * 1.14])
    table = g.reset_index().rename(columns={dim: dim.replace("_", " ").title(), "visits": "Visits", "cost": "Total cost",
                                            "visit_share": "Share of visits %", "cost_share": "Share of cost %"}).round(1)
    return fig, table


# ---- stacked columns over time -------------------------------------------------------------------
def cost_over_time(df: pd.DataFrame, grain: str = "Quarter", height: int = 320) -> tuple[go.Figure, pd.DataFrame]:
    col = {"Year": "year", "Quarter": "quarter", "Month": "month"}[grain]
    p = df.pivot_table(index=col, columns="care_setting", values="estimated_cost_per_visit", aggfunc="sum", fill_value=0)
    p = p.reindex(columns=[s for s in D.SETTING_ORDER if s in p.columns])
    x = [str(i) for i in p.index]
    fig = go.Figure()
    for s in p.columns:
        fig.add_bar(x=x, y=p[s], name=s, marker=dict(color=T.SETTING_COLORS[s], line=dict(color="#ffffff", width=1.5)),
                    hovertemplate="<b>%{x}</b><br>" + s + ": $%{y:,.0f}<extra></extra>")
    _style(fig, height=height, legend=True, margin=dict(l=6, r=18, t=30, b=6))
    fig.update_layout(barmode="stack", bargap=0.45 if grain != "Month" else 0.25)
    fig.update_xaxes(type="category", tickangle=0 if grain != "Month" else -60)
    if grain == "Quarter":
        text = [f"{p[-2:]}<br>{p[:4]}" if (i == 0 or p.endswith("Q1")) else p[-2:] for i, p in enumerate(x)]
        fig.update_xaxes(tickmode="array", tickvals=x, ticktext=text)
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    table = p.round(0).reset_index().rename(columns={col: grain})
    table[grain] = table[grain].astype(str)
    return fig, table


# ---- bottleneck reasons --------------------------------------------------------------------------
def bottlenecks(df: pd.DataFrame) -> tuple[go.Figure, pd.DataFrame]:
    b = df[["visit_id", "bottleneck_reason"]].assign(reason=df["bottleneck_reason"].str.split(";")).explode("reason")
    b["reason"] = b["reason"].str.strip()
    c = b["reason"].value_counts()
    d = pd.DataFrame({"reason": c.index, "visits": c.values, "share": c.values / max(len(df), 1) * 100})
    none = d["reason"] == "No Major Bottleneck"
    d = pd.concat([d[~none].sort_values("share", ascending=False), d[none]]).reset_index(drop=True)
    fig = go.Figure(go.Bar(
        y=d["reason"], x=d["share"], orientation="h", width=0.56,
        marker=dict(color=[T.AXIS if r == "No Major Bottleneck" else T.BLUE for r in d["reason"]]),
        text=[f"{s:.0f}%" for s in d["share"]], textposition="outside", textfont=dict(color=T.INK, size=12.5), cliponaxis=False,
        customdata=d["visits"], hovertemplate="<b>%{y}</b><br>%{x:.1f}% of visits (%{customdata:,})<extra></extra>",
    ))
    _style(fig, height=max(210, 64 + 34 * len(d)))
    fig.update_yaxes(categoryorder="array", categoryarray=d["reason"].tolist()[::-1], showgrid=False,
                     tickfont=dict(color=T.INK, size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=T.GRID, showline=False, ticksuffix="%",
                     range=[0, float(d["share"].max()) * 1.18 if len(d) else 1])
    table = d.rename(columns={"reason": "Bottleneck", "visits": "Visits flagged", "share": "% of visits"}).round(1)
    return fig, table


# ---- simple share bars (outcomes, admission mix) ---------------------------------------------------
def share_bar(df: pd.DataFrame, dim: str) -> tuple[go.Figure, pd.DataFrame]:
    c = df[dim].value_counts()
    if dim in D.ORDINAL:
        c = c.reindex([m for m in D.ORDINAL[dim] if m in c.index])
    d = pd.DataFrame({"label": c.index.astype(str), "visits": c.values, "share": c.values / max(len(df), 1) * 100})
    fig = go.Figure(go.Bar(
        y=[D.short(v) for v in d["label"]], x=d["share"], orientation="h", width=0.56, marker=dict(color=T.BLUE),
        text=[f"{s:.0f}%" for s in d["share"]], textposition="outside", textfont=dict(color=T.INK, size=12.5), cliponaxis=False,
        customdata=list(zip(d["label"], d["visits"])),
        hovertemplate="<b>%{customdata[0]}</b><br>%{x:.1f}% of visits (%{customdata[1]:,})<extra></extra>",
    ))
    _style(fig, height=max(210, 64 + 34 * len(d)))
    fig.update_yaxes(categoryorder="array", categoryarray=[D.short(v) for v in d["label"]][::-1], showgrid=False,
                     tickfont=dict(color=T.INK, size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=T.GRID, showline=False, ticksuffix="%",
                     range=[0, float(d["share"].max()) * 1.18 if len(d) else 1])
    table = d.rename(columns={"label": dim.replace("_", " ").title(), "visits": "Visits", "share": "% of visits"}).round(1)
    return fig, table
