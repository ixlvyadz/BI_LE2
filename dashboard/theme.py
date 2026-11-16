"""Design tokens, global CSS and small HTML building blocks shared by every page."""
from __future__ import annotations

import base64
import html as _html

import streamlit as st

# ---- colour tokens ---------------------------------------------------------------------------
# Palette: #216FB3 blue, #183847 navy, #3287B3 mid blue, #6BE1EF cyan, #CEF0CD mint.
# Status colours (good / watch / off-target) stay separate so "red" always means a missed target.
BLUE = "#216FB3"
BLUE_DARK = "#1a5a94"
BLUE_DEEP = "#183847"
BLUE_MID = "#3287B3"
BLUE_SOFT = "#6BE1EF"
MINT = "#CEF0CD"
BLUE_WASH = "#e2f5f8"
ORANGE = "#183847"   # second categorical hue (navy)
AQUA = "#6BE1EF"     # third categorical hue (cyan)
SEQ_BLUES = ["#f3fbf4", "#CEF0CD", "#a3e8e0", "#6BE1EF", "#4fb5d2", "#3287B3", "#216FB3", "#183847"]

GOOD = "#2f9e6b"
WARN = "#f2b33d"
SERIOUS = "#ec835a"
CRIT = "#e05563"

INK = "#183847"
INK2 = "#4a6572"
MUTED = "#7f97a1"
GRID = "rgba(24,56,71,0.09)"
AXIS = "rgba(24,56,71,0.22)"
BG = "#eef7f9"
CARD = "#ffffff"

FONT = '"Source Sans", "Source Sans 3", "Source Sans Pro", system-ui, -apple-system, "Segoe UI", sans-serif'

# entity -> colour maps (colour follows the entity, never its rank)
SETTING_COLORS = {"Inpatient": BLUE, "Emergency": BLUE_DEEP, "Ambulatory & Diagnostic": BLUE_SOFT}
YEAR_COLORS = {2024: BLUE_SOFT, 2025: BLUE, 2026: BLUE_DEEP}
STATUS_COLORS = {"Stable": MINT, "Moderate Risk": BLUE_SOFT, "High Strain": BLUE_DEEP}
ON_TARGET = BLUE_SOFT    # bars that meet the target
OFF_TARGET = BLUE_DEEP   # bars that miss the target

HERO_ART_OPACITY = 0.38   # hero artwork: 0 = invisible, 1 = solid. Adjust the transparency here.

# ---- icons (simple original line icons, 24x24) -----------------------------------------------
_ICON_PATHS = {
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 19c.6-3.4 3-5 6-5s5.4 1.6 6 5"/><circle cx="17.5" cy="9" r="2.4"/><path d="M17 14c2.3.1 3.7 1.6 4.2 4"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "bed": '<path d="M3 18V7"/><path d="M3 15h18v3"/><path d="M21 15v-2.5A3.5 3.5 0 0 0 17.5 9H11v6"/><circle cx="7" cy="11.5" r="1.8"/>',
    "repeat": '<path d="M4 11a8 8 0 0 1 13.7-4.7L20 8.5"/><path d="M20 4.5v4h-4"/><path d="M20 13a8 8 0 0 1-13.7 4.7L4 15.5"/><path d="M4 19.5v-4h4"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/><path d="m10 13.5 4 4m0-4-4 4"/>',
    "smile": '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 14c.9 1.3 2.1 2 3.5 2s2.6-.7 3.5-2"/><path d="M9 9.8v.4M15 9.8v.4"/>',
    "check": '<circle cx="12" cy="12" r="8.5"/><path d="m8.3 12.3 2.5 2.5 4.9-5.3"/>',
    "wallet": '<rect x="3" y="6" width="18" height="13" rx="3"/><path d="M3 10h18"/><path d="M15.5 14.5h2.5"/>',
    "pulse": '<path d="M3 12.5h4l2.2-6 4 12 2.6-8 1.4 2H21"/>',
    "alert": '<path d="M12 4.5 3.5 19h17L12 4.5Z"/><path d="M12 10v4.2M12 16.7v.3"/>',
    "gauge": '<path d="M4.5 17a8.5 8.5 0 1 1 15 0"/><path d="m12 13 3.5-4"/><circle cx="12" cy="13" r="1.2"/>',
    "layers": '<path d="m12 4 8.5 4.5L12 13 3.5 8.5 12 4Z"/><path d="m3.5 12.5 8.5 4.5 8.5-4.5"/><path d="m3.5 16.5 8.5 4.5 8.5-4.5"/>',
}


def svg_img(svg: str, cls: str = "", width: int | None = None, height: int | None = None) -> str:
    """Inline SVG as an <img> data URI (st.html strips raw <svg> elements)."""
    b64 = base64.b64encode(svg.encode()).decode()
    size = (f' width="{width}"' if width else "") + (f' height="{height}"' if height else "")
    return f'<img class="{cls}" alt="" aria-hidden="true"{size} src="data:image/svg+xml;base64,{b64}">'


def icon(name: str, size: int = 20, color: str = "#ffffff") -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_ICON_PATHS[name]}</svg>'
    )
    return svg_img(svg, "ic", size, size)


def esc(text) -> str:
    return _html.escape(str(text))


# ---- global CSS ------------------------------------------------------------------------------
CSS = f"""
<style>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");
:root {{
  --bg:{BG}; --ink:{INK}; --ink2:{INK2}; --muted:{MUTED}; --line:rgba(24,56,71,.10);
  --blue:{BLUE}; --blue-dark:{BLUE_DARK}; --blue-deep:{BLUE_DEEP}; --mid:{BLUE_MID}; --cyan:{BLUE_SOFT}; --mint:{MINT};
  --blue-wash:rgba(107,225,239,.20);
  --good:#1d6b45; --good-bg:rgba(206,240,205,.85); --warn:#8a5a00; --warn-bg:rgba(255,236,186,.9);
  --crit:#b3283a; --crit-bg:rgba(253,226,229,.92);
  --radius:22px;
  --glass:linear-gradient(145deg, rgba(255,255,255,.74) 0%, rgba(255,255,255,.42) 100%);
  --glass-border:1px solid rgba(255,255,255,.78);
  --glass-blur:blur(18px) saturate(165%);
  --shadow:0 10px 34px rgba(24,56,71,.10), inset 0 1px 0 rgba(255,255,255,.85);
  --shadow-up:0 18px 44px rgba(24,56,71,.16), inset 0 1px 0 rgba(255,255,255,.9);
}}

/* ---------- page background: soft colour glows for the glass to sit on ---------- */
.stApp {{
  background:
    radial-gradient(720px 520px at 0% 0%, rgba(107,225,239,.50), rgba(107,225,239,0) 62%),
    radial-gradient(640px 460px at 88% 4%, rgba(206,240,205,.70), rgba(206,240,205,0) 64%),
    radial-gradient(900px 640px at 100% 100%, rgba(33,111,179,.36), rgba(33,111,179,0) 62%),
    radial-gradient(620px 520px at 22% 96%, rgba(50,135,179,.22), rgba(50,135,179,0) 64%),
    var(--bg);
  background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1520px; }}

/* ---------- sidebar: frosted panel ---------- */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, rgba(255,255,255,.66) 0%, rgba(255,255,255,.40) 100%);
  -webkit-backdrop-filter: blur(22px) saturate(170%); backdrop-filter: blur(22px) saturate(170%);
  border-right: 1px solid rgba(255,255,255,.8);
  box-shadow: 6px 0 34px rgba(24,56,71,.08);
}}
[data-testid="stSidebar"] > div {{ background: transparent; }}
[data-testid="stSidebarNavLink"] {{ border-radius:14px; margin:2px 0; transition: background .18s ease, transform .18s ease; }}
[data-testid="stSidebarNavLink"]:hover {{ background: rgba(107,225,239,.22); transform: translateX(2px); }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
  background: linear-gradient(100deg, {BLUE} 0%, {BLUE_MID} 70%, #48a9cf 100%);
  box-shadow: 0 8px 20px rgba(33,111,179,.32), inset 0 1px 0 rgba(255,255,255,.28);
}}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {{ color:#ffffff !important; font-weight:600; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(24,56,71,.10); }}
.side-title {{ font-size:.72rem; letter-spacing:.11em; text-transform:uppercase; color:var(--mid); font-weight:700; margin:.2rem 0 .1rem; }}
.side-count {{
  background: linear-gradient(140deg, {BLUE_DEEP} 0%, #1d5a8c 62%, {BLUE} 100%); color:#fff;
  border:1px solid rgba(107,225,239,.35); border-radius:18px; padding:14px 16px; margin:.2rem 0 .6rem;
  box-shadow: 0 12px 26px rgba(24,56,71,.22);
}}
.side-count b {{ font-size:1.45rem; color:#ffffff; }}
.side-count span {{ color:rgba(255,255,255,.80); font-size:.85rem; }}
.side-bar {{ height:6px; background:rgba(255,255,255,.18); border-radius:99px; margin-top:10px; overflow:hidden; }}
.side-bar i {{ display:block; height:100%; background:linear-gradient(90deg, {BLUE_SOFT}, {MINT}); border-radius:99px; }}

/* ---------- inputs: translucent controls ---------- */
[data-baseweb="select"] > div, [data-testid="stTextInput"] [data-baseweb="input"], [data-testid="stTextInput"] input {{
  background: rgba(255,255,255,.58) !important; border-color: rgba(255,255,255,.9) !important; border-radius:14px !important;
  box-shadow: 0 2px 10px rgba(24,56,71,.06), inset 0 1px 0 rgba(255,255,255,.9);
}}
.stButton > button, .stDownloadButton > button, div[data-testid="stPopover"] button, [data-testid="stExpander"] details {{
  background: rgba(255,255,255,.55); border:1px solid rgba(255,255,255,.9); border-radius:14px;
  -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(24,56,71,.06); transition: all .18s ease;
}}
.stButton > button:hover:not(:disabled), .stDownloadButton > button:hover, div[data-testid="stPopover"] button:hover {{
  background: rgba(255,255,255,.85); border-color: {BLUE_SOFT}; color: {BLUE_DARK}; transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(33,111,179,.16);
}}
[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {{ box-shadow: 0 0 0 5px rgba(107,225,239,.35); }}

/* ---------- glass cards: every st.container(key="card_...") ---------- */
[class*="st-key-card_"] {{
  background: var(--glass); border: var(--glass-border); border-radius: var(--radius);
  -webkit-backdrop-filter: var(--glass-blur); backdrop-filter: var(--glass-blur);
  box-shadow: var(--shadow); padding:20px 22px 16px; transition: box-shadow .22s ease, transform .22s ease;
}}
[class*="st-key-card_"]:hover {{ box-shadow: var(--shadow-up); }}
.card-h {{ display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:2px; }}
.card-t {{ font-size:1.04rem; font-weight:700; color:var(--ink); line-height:1.25; padding-left:12px; position:relative; }}
.card-t::before {{ content:""; position:absolute; left:0; top:.18em; bottom:.18em; width:4px; border-radius:4px;
                  background:linear-gradient(180deg, {BLUE}, {BLUE_SOFT}); }}
.card-s {{ font-size:.86rem; color:var(--ink2); margin-top:3px; line-height:1.35; padding-left:12px; }}

/* ---------- hero ---------- */
.hero {{
  position:relative; overflow:hidden; border-radius:26px; padding:24px 28px; color:#fff; margin-bottom:4px;
  background:
    radial-gradient(420px 240px at 94% 0%, rgba(107,225,239,.55), rgba(107,225,239,0) 70%),
    radial-gradient(340px 220px at 66% 130%, rgba(206,240,205,.32), rgba(206,240,205,0) 70%),
    linear-gradient(118deg, {BLUE_DEEP} 0%, {BLUE} 52%, {BLUE_MID} 100%);
  border:1px solid rgba(255,255,255,.28);
  box-shadow:0 18px 44px rgba(24,56,71,.28), inset 0 1px 0 rgba(255,255,255,.22);
}}
.hero h1 {{ font-size:1.7rem; font-weight:700; margin:0; padding:0; color:#fff; letter-spacing:-.01em; }}
.hero p {{ margin:.3rem 0 0; color:rgba(255,255,255,.88); font-size:.98rem; max-width:62ch; }}
.hero-art {{ position:absolute; right:0; top:0; height:100%; width:auto; max-width:68%; opacity:{HERO_ART_OPACITY}; pointer-events:none;
            -webkit-mask-image:linear-gradient(90deg, transparent 0%, #000 38%); mask-image:linear-gradient(90deg, transparent 0%, #000 38%); }}
.hero-row {{ position:relative; z-index:1; display:flex; justify-content:space-between; align-items:flex-end; gap:18px; flex-wrap:wrap; }}
.chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
.chip {{ background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.34); border-radius:99px; padding:6px 13px;
        font-size:.84rem; color:#fff; white-space:nowrap; -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.25); }}
.chip b {{ font-weight:700; color:{MINT}; }}
.eyebrow {{ font-size:.74rem; letter-spacing:.12em; text-transform:uppercase; color:{BLUE_SOFT}; font-weight:700; margin-bottom:4px; }}

/* ---------- KPI tiles ---------- */
.kpis {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:16px; }}
.kpis.c5 {{ grid-template-columns:repeat(5, minmax(0,1fr)); }}
@media (max-width:1100px) {{ .kpis, .kpis.c5 {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} }}
.kpi {{
  background: var(--glass); border: var(--glass-border); border-radius: var(--radius);
  -webkit-backdrop-filter: var(--glass-blur); backdrop-filter: var(--glass-blur); box-shadow: var(--shadow);
  padding:18px 20px 15px; position:relative; overflow:hidden; min-height:142px; display:flex; flex-direction:column;
  transition: transform .22s ease, box-shadow .22s ease;
}}
.kpi::before {{ content:""; position:absolute; left:20px; right:20px; top:0; height:3px; border-radius:0 0 6px 6px;
               background:linear-gradient(90deg, {BLUE}, {BLUE_SOFT}); }}
.kpi::after {{ content:""; position:absolute; right:-46px; bottom:-56px; width:150px; height:150px; border-radius:50%;
              background:radial-gradient(circle, rgba(107,225,239,.30), rgba(107,225,239,0) 68%); pointer-events:none; }}
.kpi:hover {{ transform: translateY(-4px); box-shadow: var(--shadow-up); }}
.kpi.compact {{ min-height:0; }}
.kpi-top {{ display:flex; align-items:center; gap:11px; position:relative; z-index:1; }}
.kpi-ic {{ width:38px; height:38px; border-radius:13px; display:grid; place-items:center; flex:none;
          background:linear-gradient(135deg, {BLUE} 0%, {BLUE_MID} 55%, {BLUE_SOFT} 100%);
          box-shadow:0 8px 16px rgba(33,111,179,.30), inset 0 1px 0 rgba(255,255,255,.35); }}
.kpi-l {{ font-size:.88rem; color:var(--ink2); font-weight:600; line-height:1.2; }}
.kpi-v {{ font-size:2.05rem; font-weight:700; color:var(--ink); line-height:1.1; margin-top:12px; letter-spacing:-.02em; position:relative; z-index:1; }}
.kpi-v small {{ font-size:.95rem; font-weight:600; color:var(--ink2); margin-left:4px; letter-spacing:0; }}
.kpi-f {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-top:auto; padding-top:10px; position:relative; z-index:1; }}
.kpi-d {{ font-size:.8rem; color:var(--ink2); white-space:nowrap; }}
.kpi-d.up-good, .kpi-d.down-good {{ color:#1d6b45; }} .kpi-d.up-bad, .kpi-d.down-bad {{ color:#b3283a; }}
.kpi-spark {{ position:absolute; right:16px; top:50px; opacity:.95; z-index:1; }}

/* KPI off target: dark glass tile so it stands out without leaving the palette */
.kpi.alert {{
  background: linear-gradient(150deg, {BLUE_DEEP} 0%, #1d5a8c 62%, {BLUE} 100%);
  border:1px solid rgba(107,225,239,.40); box-shadow:0 16px 38px rgba(24,56,71,.30), inset 0 1px 0 rgba(255,255,255,.18);
}}
.kpi.alert::before {{ background:linear-gradient(90deg, {BLUE_SOFT}, {MINT}); }}
.kpi.alert::after {{ background:radial-gradient(circle, rgba(107,225,239,.38), rgba(107,225,239,0) 68%); }}
.kpi.alert .kpi-ic {{ background:linear-gradient(135deg, {BLUE_SOFT}, {MINT}); box-shadow:0 8px 16px rgba(0,0,0,.22); }}
.kpi.alert .kpi-l {{ color:rgba(255,255,255,.84); }}
.kpi.alert .kpi-v {{ color:#ffffff; }}
.kpi.alert .kpi-v small {{ color:rgba(255,255,255,.75); }}
.kpi.alert .kpi-d, .kpi.alert .kpi-d.up-good, .kpi.alert .kpi-d.down-good {{ color:{MINT}; }}
.kpi.alert .kpi-d.up-bad, .kpi.alert .kpi-d.down-bad {{ color:#ffc9cf; }}
.kpi.alert .pill-crit {{ background:#ffffff; color:#b3283a; }}

/* ---------- pills ---------- */
.pill {{ display:inline-flex; align-items:center; gap:5px; border-radius:99px; padding:3px 10px; font-size:.78rem; font-weight:600; white-space:nowrap; }}
.pill-good {{ background:var(--good-bg); color:var(--good); }}
.pill-warn {{ background:var(--warn-bg); color:var(--warn); }}
.pill-crit {{ background:var(--crit-bg); color:var(--crit); }}
.pill-info {{ background:rgba(107,225,239,.30); color:var(--blue-dark); }}
.pill-mute {{ background:rgba(24,56,71,.07); color:var(--ink2); }}

/* ---------- brief banner ---------- */
.brief {{ display:flex; gap:14px; align-items:center; }}
.brief-ic {{ width:44px; height:44px; border-radius:14px; display:grid; place-items:center; flex:none;
            background:linear-gradient(135deg, {BLUE_DEEP}, {BLUE}); box-shadow:0 8px 18px rgba(24,56,71,.28); }}
.brief-t {{ font-weight:700; color:var(--ink); font-size:1rem; }}
.brief-s {{ color:var(--ink2); font-size:.92rem; line-height:1.4; }}

/* ---------- tables ---------- */
.tbl-wrap {{ overflow-x:auto; }}
table.sc {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.9rem; }}
table.sc th {{ text-align:right; font-size:.72rem; letter-spacing:.07em; text-transform:uppercase; color:var(--blue-dark);
              background:rgba(107,225,239,.22); padding:10px 10px; font-weight:700; white-space:nowrap; }}
table.sc th:first-child {{ text-align:left; border-radius:12px 0 0 12px; }} table.sc th:last-child {{ border-radius:0 12px 12px 0; text-align:left; }}
table.sc td {{ padding:9px 10px; border-bottom:1px solid var(--line); text-align:right; color:var(--ink); font-variant-numeric:tabular-nums; white-space:nowrap; }}
table.sc td:first-child {{ text-align:left; font-weight:600; }} table.sc td:last-child {{ text-align:left; }}
table.sc tbody tr {{ transition: background .15s ease; }}
table.sc tbody tr:hover td {{ background:rgba(255,255,255,.55); }}
table.sc tr:last-child td {{ border-bottom:none; }}
table.sc td.miss {{ color:var(--crit); font-weight:700; }}
table.sc td.miss::before {{ content:"\\25CF"; font-size:.55rem; vertical-align:middle; margin-right:5px; }}
table.sc td .sub {{ display:block; color:var(--muted); font-size:.76rem; font-weight:400; }}
table.sc tr.tot td {{ background:rgba(33,111,179,.08); font-weight:700; }}
table.sc.wrap th, table.sc.wrap td {{ text-align:left; white-space:normal; vertical-align:top; line-height:1.4; }}
table.sc.wrap td:first-child {{ min-width:0; }}
table.sc.ins td:nth-child(3) {{ font-weight:600; min-width:220px; }} table.sc.ins td:first-child {{ color:var(--muted); min-width:0; }}

/* ---------- insight cards ---------- */
.ins {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:16px; }}
@media (max-width:1100px) {{ .ins {{ grid-template-columns:1fr; }} }}
.in {{ background:var(--glass); border:var(--glass-border); border-radius:var(--radius); box-shadow:var(--shadow);
      -webkit-backdrop-filter: var(--glass-blur); backdrop-filter: var(--glass-blur); padding:20px 22px;
      transition: transform .22s ease, box-shadow .22s ease; }}
.in:hover {{ transform: translateY(-3px); box-shadow: var(--shadow-up); }}
.in-h {{ display:flex; gap:12px; align-items:flex-start; margin-bottom:10px; }}
.in-n {{ width:32px; height:32px; border-radius:11px; color:#fff; display:grid; place-items:center; font-weight:700; flex:none;
        background:linear-gradient(135deg, {BLUE}, {BLUE_SOFT}); box-shadow:0 6px 14px rgba(33,111,179,.28); }}
.in-t {{ font-weight:700; font-size:1.02rem; color:var(--ink); line-height:1.3; }}
.in dl {{ margin:0; display:grid; grid-template-columns:118px 1fr; row-gap:8px; column-gap:12px; font-size:.9rem; }}
.in dt {{ color:var(--mid); font-weight:700; font-size:.72rem; letter-spacing:.07em; text-transform:uppercase; padding-top:2px; }}
.in dd {{ margin:0; color:var(--ink); line-height:1.45; }}
.in dd.act {{ background:linear-gradient(120deg, rgba(107,225,239,.26), rgba(206,240,205,.55)); border:1px solid rgba(255,255,255,.8);
             border-radius:12px; padding:9px 11px; color:var(--blue-deep); font-weight:600; }}

/* ---------- generic ---------- */
.note {{ color:var(--ink2); font-size:.86rem; line-height:1.45; }}
.crumb {{ color:var(--ink2); font-size:.9rem; }}
.crumb b {{ color:var(--ink); }}
.stat-row {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px; }}
.stat {{ background:var(--glass); border:var(--glass-border); border-radius:18px; padding:14px 16px; box-shadow:var(--shadow);
        -webkit-backdrop-filter: var(--glass-blur); backdrop-filter: var(--glass-blur); }}
.stat b {{ display:block; font-size:1.4rem; color:var(--ink); }}
.stat span {{ color:var(--ink2); font-size:.84rem; }}
.stat i {{ font-style:normal; color:var(--muted); font-size:.8rem; }}
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{ border-radius:12px 12px 0 0; padding:8px 14px; }}
[data-testid="stDataFrame"] {{ border-radius:14px; overflow:hidden; box-shadow:0 2px 12px rgba(24,56,71,.06); }}

/* ================= sidebar typography and controls ================= */
[data-testid="stSidebar"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] span:not([data-testid="stIconMaterial"]),
[data-testid="stSidebar"] label, [data-testid="stSidebar"] button, [data-testid="stSidebar"] input {{
  font-family: "Plus Jakarta Sans", "Poppins", "Segoe UI", system-ui, -apple-system, sans-serif;
}}
[data-testid="stSidebarHeader"] {{ padding-top:1.1rem; padding-bottom:.9rem; margin-bottom:.4rem; border-bottom:1px solid rgba(24,56,71,.08); }}
[data-testid="stSidebarLogo"] {{ height:2.6rem; }}

/* navigation */
[data-testid="stNavSectionHeader"] {{ margin-top:.9rem; padding-left:.35rem; }}
[data-testid="stNavSectionHeader"], [data-testid="stNavSectionHeader"] * {{
  font-size:.68rem !important; font-weight:800 !important; letter-spacing:.16em; text-transform:uppercase; color:{BLUE_MID} !important;
}}
[data-testid="stSidebarNavLink"] {{ padding:.5rem .7rem; gap:.65rem; }}
[data-testid="stSidebarNavLink"] span {{ font-size:.93rem; font-weight:500; color:{INK}; letter-spacing:.005em; }}
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{ font-size:1.2rem; color:{BLUE_MID}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] span:not([data-testid="stIconMaterial"]) {{ font-weight:700 !important; }}
[data-testid="stSidebarNavSeparator"] {{ border-color:rgba(24,56,71,.08); margin:.9rem 0 .7rem; }}

/* filter block */
.side-title {{ display:flex; align-items:center; gap:.5rem; font-size:.68rem; font-weight:800; letter-spacing:.16em; color:{BLUE_MID}; }}
.side-title::after {{ content:""; flex:1; height:1px; background:linear-gradient(90deg, rgba(50,135,179,.45), rgba(50,135,179,0)); }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
  font-size:.74rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:{INK2};
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{ min-height:2.6rem; font-size:.9rem; }}
[data-testid="stSidebar"] [data-baseweb="tag"] {{ background:linear-gradient(100deg, {BLUE}, {BLUE_MID}) !important; border-radius:9px !important; }}
[data-testid="stSidebar"] [data-baseweb="tag"] span, [data-testid="stSidebar"] [data-baseweb="tag"] svg {{ color:#fff !important; fill:#fff !important; }}
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"] {{ font-size:.8rem; font-weight:700; color:{BLUE} !important; }}

/* pills (severity, shift) and segmented control (days) */
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button {{
  background:rgba(255,255,255,.60); border:1px solid rgba(255,255,255,.95); border-radius:999px;
  padding:.3rem .85rem; font-size:.84rem; font-weight:600; color:{INK2};
  box-shadow:0 2px 8px rgba(24,56,71,.06); transition:all .16s ease;
}}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button p {{ font-size:.84rem; font-weight:600; }}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button:hover {{ border-color:{BLUE_SOFT}; color:{BLUE_DARK}; transform:translateY(-1px); }}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-pressed="true"],
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-checked="true"] {{
  background:linear-gradient(100deg, {BLUE} 0%, {BLUE_MID} 100%); border-color:transparent; color:#fff;
  box-shadow:0 6px 14px rgba(33,111,179,.30);
}}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-pressed="true"] *,
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-checked="true"] * {{ color:#fff !important; }}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] [role="radiogroup"] {{ gap:.35rem; }}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[role="radio"] {{ border-radius:999px !important; padding:.3rem .6rem; }}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[role="radio"] p {{ font-size:.8rem; }}

/* expander, reset button, footnote */
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {{ font-size:.86rem; font-weight:600; color:{INK}; }}
[data-testid="stSidebar"] .stButton > button {{ font-weight:700; font-size:.88rem; letter-spacing:.01em; min-height:2.6rem; }}
[data-testid="stSidebar"] .stButton > button:not(:disabled) {{
  background:linear-gradient(100deg, {BLUE_DEEP}, {BLUE}); color:#fff; border-color:transparent; box-shadow:0 8px 18px rgba(24,56,71,.22);
}}
[data-testid="stSidebar"] .stButton > button:not(:disabled):hover {{ background:linear-gradient(100deg, {BLUE}, {BLUE_MID}); color:#fff; }}
[data-testid="stSidebar"] .stButton > button:not(:disabled) * {{ color:#fff !important; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ font-size:.74rem; line-height:1.5; color:{MUTED}; }}
.side-count b {{ font-size:1.6rem; font-weight:800; letter-spacing:-.02em; }}
.side-count span {{ font-size:.8rem; font-weight:500; }}

/* ================= equal-height cards within a row ================= */
[data-testid="stHorizontalBlock"]:has([class*="st-key-card_"]) {{ align-items:stretch; }}
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] [class*="st-key-card_"]) {{ display:flex; flex-direction:column; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]:has([class*="st-key-card_"]) {{ flex:1 1 auto; height:100%; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [class*="st-key-card_"],
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > div:has(> [class*="st-key-card_"]) {{ flex:1 1 auto; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > div > [class*="st-key-card_"] {{ height:100%; }}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


# ---- HTML building blocks --------------------------------------------------------------------
def pill(text: str, tone: str = "info", symbol: str = "") -> str:
    sym = f"<span aria-hidden='true'>{symbol}</span>" if symbol else ""
    return f'<span class="pill pill-{tone}">{sym}{esc(text)}</span>'


def card_header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="card-s">{esc(subtitle)}</div>' if subtitle else ""
    st.html(f'<div class="card-h"><div><div class="card-t">{esc(title)}</div>{sub}</div></div>')


# ---- hero artwork: one original line-art vector per page ------------------------------------------

_W = 'fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"'
_C = f'fill="none" stroke="{BLUE_SOFT}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"'
_BACKDROP = (
    f'<circle cx="455" cy="30" r="120" fill="none" stroke="{BLUE_SOFT}" stroke-width="26" opacity=".45"/>'
    f'<circle cx="215" cy="215" r="70" fill="none" stroke="{MINT}" stroke-width="18" opacity=".40"/>'
    f'<path d="M20 172 q30 -34 60 0 t60 0 t60 0" fill="none" stroke="{MINT}" stroke-width="4" stroke-linecap="round" opacity=".7"/>'
    + "".join(f'<circle cx="{70 + 18 * i}" cy="{34 + 18 * j}" r="2.6" fill="#ffffff" opacity=".7"/>'
              for i in range(5) for j in range(4))
)
_ART = {
    "overview": (
        '<rect x="270" y="110" width="18" height="50" rx="6" fill="#fff" opacity=".9"/>'
        '<rect x="298" y="85" width="18" height="75" rx="6" fill="#fff" opacity=".9"/>'
        f'<rect x="326" y="60" width="18" height="100" rx="6" fill="{BLUE_SOFT}"/>'
        '<rect x="354" y="95" width="18" height="65" rx="6" fill="#fff" opacity=".9"/>'
        f'<path d="M228 62 h36 l12 -28 l18 60 l14 -40 l10 18 h66" {_C}/>'
        '<circle cx="440" cy="122" r="30" fill="none" stroke="#fff" stroke-width="12" stroke-dasharray="120 190" stroke-linecap="round"/>'
    ),
    "flow": (
        f'<circle cx="330" cy="100" r="52" {_W}/><path d="M330 66 V100 l24 15" {_W}/>'
        '<circle cx="248" cy="100" r="9" fill="#fff"/><circle cx="222" cy="100" r="7" fill="#fff" opacity=".75"/>'
        '<circle cx="201" cy="100" r="5" fill="#fff" opacity=".5"/>'
        f'<path d="M408 70 l24 30 l-24 30 M438 70 l24 30 l-24 30 M468 70 l24 30 l-24 30" {_C}/>'
    ),
    "capacity": (
        f'<path d="M250 152 V68 M250 126 H410 V152 M410 126 V106 a22 22 0 0 0 -22 -22 H300 V126" {_W}/>'
        '<circle cx="275" cy="103" r="13" fill="#fff"/>'
        f'<path d="M432 128 a38 38 0 0 1 76 0" fill="none" stroke="{BLUE_SOFT}" stroke-width="10" stroke-linecap="round"/>'
        f'<path d="M470 128 l18 -24" {_W}/><circle cx="470" cy="128" r="5" fill="#fff"/>'
    ),
    "quality": (
        f'<path d="M330 36 l56 20 v46 c0 36 -26 56 -56 70 c-30 -14 -56 -34 -56 -70 v-46 z" {_W}/>'
        f'<path d="M304 102 l19 19 l35 -40" {_C}/>'
        f'<path d="M440 58 v26 M427 71 h26 M232 128 v18 M223 137 h18" {_C}/>'
        '<circle cx="452" cy="138" r="7" fill="#fff" opacity=".8"/>'
    ),
    "cost": (
        f'<ellipse cx="295" cy="108" rx="44" ry="14" {_W}/>'
        f'<path d="M251 108 v44 a44 14 0 0 0 88 0 v-44 M251 130 a44 14 0 0 0 88 0" {_W}/>'
        f'<path d="M372 152 l36 -42 l26 20 l44 -62 M452 66 h28 v28" {_C}/>'
        '<circle cx="295" cy="56" r="22" fill="#fff" opacity=".9"/>'
        f'<path d="M303 50 c-3 -7 -16 -5 -16 2 c0 9 17 5 17 14 c0 7 -13 8 -18 1 M295 40 v32" fill="none" stroke="{BLUE}" stroke-width="3.5" stroke-linecap="round"/>'
    ),
    "drill": (
        '<rect x="300" y="34" width="60" height="30" rx="9" fill="#fff" opacity=".92"/>'
        f'<path d="M330 64 V90 M250 90 H410 M250 90 V110 M330 90 V110 M410 90 V110 M330 138 V156" {_W}/>'
        f'<rect x="225" y="110" width="50" height="28" rx="8" {_W}/><rect x="305" y="110" width="50" height="28" rx="8" {_W}/>'
        f'<rect x="385" y="110" width="50" height="28" rx="8" {_W}/>'
        f'<rect x="300" y="156" width="60" height="26" rx="8" fill="{BLUE_SOFT}"/>'
    ),
    "insights": (
        f'<path d="M330 46 a42 42 0 0 1 24 76 v14 h-48 v-14 a42 42 0 0 1 24 -76 z M312 150 h36 M319 163 h22" {_W}/>'
        f'<path d="M330 28 V14 M264 88 H250 M410 88 H396 M284 44 l-10 -10 M376 44 l10 -10" {_C}/>'
        f'<path d="M450 108 q4 16 20 20 q-16 4 -20 20 q-4 -16 -20 -20 q16 -4 20 -20 z" fill="{MINT}"/>'
        '<path d="M228 140 q2 9 11 11 q-9 2 -11 11 q-2 -9 -11 -11 q9 -2 11 -11 z" fill="#fff" opacity=".85"/>'
    ),
    "methods": (
        f'<ellipse cx="290" cy="58" rx="44" ry="14" {_W}/>'
        f'<path d="M246 58 v84 a44 14 0 0 0 88 0 v-84 M246 86 a44 14 0 0 0 88 0 M246 114 a44 14 0 0 0 88 0" {_W}/>'
        f'<path d="M334 100 h50" {_C} stroke-dasharray="2 9"/>'
        f'<rect x="388" y="58" width="104" height="84" rx="12" {_W}/>'
        f'<path d="M388 86 h104 M388 114 h104 M422 58 v84 M457 58 v84" fill="none" stroke="#fff" stroke-width="2.5" opacity=".85"/>'
        f'<rect x="388" y="58" width="104" height="28" rx="12" fill="{BLUE_SOFT}" opacity=".55"/>'
    ),
}
# page title -> artwork (so pages.py does not need to change)
HERO_ART_BY_TITLE = {
    "Hospital operations overview": "overview", "Patient flow and wait times": "flow",
    "Capacity and resources": "capacity", "Quality and outcomes": "quality", "Cost and resource use": "cost",
    "Drill-down explorer": "drill", "Insights and recommended actions": "insights", "Data and methods": "methods",
}


def hero_art(title: str) -> str:
    art = _ART[HERO_ART_BY_TITLE.get(title, "overview")]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 200" width="520" height="200">{_BACKDROP}{art}</svg>'
    return svg_img(svg, "hero-art")


def hero(title: str, subtitle: str, chips: list[str], eyebrow: str = "Healthcare operations dashboard") -> None:
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.html(
        f'<div class="hero">{hero_art(title)}<div class="hero-row"><div><div class="eyebrow">{esc(eyebrow)}</div>'
        f"<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div><div class='chips'>{chip_html}</div></div></div>"
    )


def sparkline(values: list[float], width: int = 96, height: int = 34) -> str:
    """12-point style sparkline: de-emphasised line, accent dot on the latest point."""
    vals = [v for v in values if v is not None and v == v]
    if len(vals) < 3:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    step = (width - 8) / (len(vals) - 1)
    pts = [(4 + i * step, 4 + (height - 8) * (1 - (v - lo) / span)) for i, v in enumerate(vals)]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    lx, ly = pts[-1]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polyline points="{path}" fill="none" stroke="{BLUE_SOFT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.6" fill="{BLUE}" stroke="#fff" stroke-width="2"/></svg>'
    )
    return svg_img(svg, "kpi-spark", width, height)
