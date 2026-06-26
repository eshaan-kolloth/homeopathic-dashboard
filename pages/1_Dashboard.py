import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os, sys, io, textwrap, datetime

from utils.data_processor import (
    get_salesperson_totals,
    get_zero_sales,
    get_daily_totals,
    get_category_totals,
    get_mtd_total,
    get_ytd_total,
    get_data_summary_for_ai,
)
from utils.groq_client import ask_groq

st.set_page_config(
    page_title="ARIA · Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Guard ──────────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.warning("No dataset loaded. Please upload a file first.")
    st.page_link("app.py", label="← Back to Upload", icon="⬅️")
    st.stop()

df       = st.session_state["df"]
filename = st.session_state.get("filename", "dataset.xlsx")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;}
:root{
  --bg-1:#02030A;--bg-2:#040712;--bg-3:#06091A;
  --blue:#4F8CFF;--purple:#7B61FF;--cyan:#00D4FF;
  --green:#00FFC6;--gold:#FFD166;--red:#FF6B6B;
  --text-primary:#F4F7FC;--text-secondary:#AEB9D4;--text-muted:#6B7694;
  --glass-border:rgba(255,255,255,0.06);--glass-bg:rgba(255,255,255,0.03);
}
html,body,.stApp{
  background:radial-gradient(ellipse 120% 80% at 50% -10%,var(--bg-3) 0%,var(--bg-2) 45%,var(--bg-1) 100%) !important;
  color:var(--text-secondary);font-family:'Manrope',sans-serif;
}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:5.5rem 3.5vw 3rem !important;max-width:100% !important;}

/* sidebar */
section[data-testid="stSidebar"]{background:rgba(4,7,18,0.97) !important;border-right:1px solid var(--glass-border);}
section[data-testid="stSidebar"] *{color:var(--text-secondary) !important;}
.sb-section{margin-bottom:1.2rem;}
.sb-hdr{font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:var(--cyan);letter-spacing:2px;text-transform:uppercase;padding:0.5rem 0 0.3rem;border-bottom:1px solid var(--glass-border);margin-bottom:0.6rem;}
.sb-stat{display:flex;justify-content:space-between;align-items:center;font-size:0.78rem;padding:0.22rem 0;}
.sb-stat .lbl{color:var(--text-muted);}
.sb-stat .val{color:var(--text-primary);font-weight:600;}
.sb-badge{display:inline-flex;align-items:center;gap:5px;font-family:'JetBrains Mono',monospace;font-size:0.62rem;padding:3px 9px;border-radius:99px;}
.sb-badge.on{background:rgba(0,255,198,0.08);border:1px solid rgba(0,255,198,0.25);color:var(--green);}
.sb-dot{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 5px var(--green);animation:pulse 2s ease infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.3;}}

/* top bar */
#dash-topbar{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0.85rem 2.4rem;background:rgba(2,3,10,0.75);border-bottom:1px solid var(--glass-border);backdrop-filter:blur(24px);}
.tb-brand{display:flex;align-items:center;gap:0.7rem;}
.tb-mark{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,var(--blue),var(--purple) 60%,var(--cyan));display:flex;align-items:center;justify-content:center;font-size:0.78rem;font-weight:700;color:#fff;box-shadow:0 0 16px rgba(79,140,255,0.4);}
.tb-name{font-size:0.9rem;font-weight:700;color:var(--text-primary);}
.tb-tag{font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:var(--text-muted);background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:5px;padding:2px 7px;}
.tb-right{display:flex;align-items:center;gap:1.4rem;}
.tb-pill{display:flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.6px;}
.tb-dot{width:5px;height:5px;border-radius:50%;animation:pulse 2.4s ease infinite;}
.tb-dot.g{background:var(--green);box-shadow:0 0 5px var(--green);}
.tb-dot.b{background:var(--blue);box-shadow:0 0 5px var(--blue);animation-delay:.5s;}

/* section headers */
.sec-hdr{display:flex;align-items:center;gap:10px;font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:var(--cyan);letter-spacing:2.5px;text-transform:uppercase;margin:2.2rem 0 1rem;}
.sec-hdr .ln{flex:1;height:1px;background:linear-gradient(90deg,var(--glass-border),transparent);}

/* intelligence banner */
#banner{border-radius:20px;border:1px solid var(--glass-border);background:linear-gradient(120deg,rgba(79,140,255,0.07),rgba(123,97,255,0.05) 50%,rgba(0,212,255,0.04));backdrop-filter:blur(20px);padding:1.5rem 1.8rem;position:relative;overflow:hidden;}
#banner::before{content:'';position:absolute;top:-50%;right:-8%;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(79,140,255,0.18),transparent 70%);filter:blur(10px);}
.bn-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.1rem;position:relative;z-index:1;}
.bn-title{font-size:1.1rem;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:8px;}
.bn-dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 2s infinite;}
.bn-sub{font-size:0.76rem;color:var(--text-muted);margin-top:0.15rem;}
.bn-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:0;position:relative;z-index:1;}
.bcell{padding:0.35rem 0.9rem;border-left:1px solid var(--glass-border);}
.bcell:first-child{border-left:none;padding-left:0;}
.bcell .lab{font-family:'JetBrains Mono',monospace;font-size:0.52rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.1px;margin-bottom:0.25rem;}
.bcell .num{font-size:1.35rem;font-weight:800;color:var(--text-primary);line-height:1.1;}
.bcell .num.cy{color:var(--cyan);}.bcell .num.gr{color:var(--green);}.bcell .num.go{color:var(--gold);}.bcell .num.pu{color:var(--purple);}.bcell .num.re{color:var(--red);}
.bcell .delta{font-size:0.68rem;margin-top:0.2rem;font-weight:600;}
.delta.up{color:var(--green);}.delta.dn{color:var(--red);}

/* kpi cards */
.kpi{border-radius:16px;border:1px solid var(--glass-border);background:var(--glass-bg);backdrop-filter:blur(14px);padding:1.1rem 1.3rem;transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease;}
.kpi:hover{transform:translateY(-4px);border-color:rgba(79,140,255,0.3);box-shadow:0 8px 32px rgba(79,140,255,0.08);}
.kpi-lab{font-family:'JetBrains Mono',monospace;font-size:0.56rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.3px;margin-bottom:0.4rem;}
.kpi-val{font-size:1.45rem;font-weight:800;}
.kpi-val.cy{color:var(--cyan);}.kpi-val.gr{color:var(--green);}.kpi-val.go{color:var(--gold);}.kpi-val.pu{color:var(--purple);}.kpi-val.re{color:var(--red);}
.kpi-foot{font-size:0.7rem;color:var(--text-muted);margin-top:0.35rem;}
.kpi-delta{font-size:0.72rem;font-weight:600;margin-top:0.3rem;}

/* glass card */
.gcard{border-radius:18px;border:1px solid var(--glass-border);background:var(--glass-bg);backdrop-filter:blur(14px);padding:1.3rem 1.4rem;}
.gcard-title{font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:0.8rem;}

/* leaderboard */
.lb-row{display:flex;align-items:center;gap:10px;padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.03);}
.lb-row:last-child{border-bottom:none;}
.lb-rank{width:22px;font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:var(--text-muted);flex-shrink:0;}
.lb-rank.r1{color:var(--gold);}.lb-rank.r2{color:var(--cyan);}.lb-rank.r3{color:var(--purple);}
.lb-info{flex:1;}
.lb-top{display:flex;justify-content:space-between;align-items:center;}
.lb-name{font-size:0.83rem;color:var(--text-secondary);}
.lb-cat{font-family:'JetBrains Mono',monospace;font-size:0.55rem;color:var(--text-muted);}
.lb-val{font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:var(--text-primary);font-weight:700;}
.lb-bar{height:3px;border-radius:99px;background:rgba(255,255,255,0.05);margin-top:4px;overflow:hidden;}
.lb-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--cyan));}

/* alerts */
.alert-pill{display:flex;align-items:center;gap:8px;padding:0.4rem 0.75rem;border-radius:10px;background:rgba(255,107,107,0.06);border:1px solid rgba(255,107,107,0.18);margin-bottom:0.35rem;font-size:0.78rem;color:var(--text-secondary);}
.alert-dot{width:6px;height:6px;border-radius:50%;background:var(--red);box-shadow:0 0 6px var(--red);flex-shrink:0;}
.ok-pill{font-size:0.8rem;color:var(--green);display:flex;align-items:center;gap:7px;}

/* category health */
.health-row{display:flex;align-items:center;justify-content:space-between;padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.03);}
.health-row:last-child{border-bottom:none;}
.health-name{font-size:0.82rem;color:var(--text-secondary);}
.health-val{font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:var(--text-primary);font-weight:600;}
.hbadge{font-family:'JetBrains Mono',monospace;font-size:0.58rem;padding:2px 8px;border-radius:99px;}
.hbadge.strong{background:rgba(0,255,198,0.1);color:var(--green);border:1px solid rgba(0,255,198,0.25);}
.hbadge.moderate{background:rgba(255,209,102,0.1);color:var(--gold);border:1px solid rgba(255,209,102,0.25);}
.hbadge.low{background:rgba(255,107,107,0.1);color:var(--red);border:1px solid rgba(255,107,107,0.25);}

/* progress bar */
.prog-track{height:10px;border-radius:99px;background:rgba(255,255,255,0.05);overflow:hidden;margin:0.6rem 0 0.35rem;}
.prog-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--purple),var(--cyan));}
.prog-cap{display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-muted);}

/* day comparison table */
.day-row{display:flex;justify-content:space-between;align-items:center;padding:0.32rem 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:0.8rem;}
.day-row:last-child{border-bottom:none;}

/* chart toggle */
div[data-testid="stRadio"] > div{display:flex;gap:0.5rem;flex-wrap:wrap;}
div[data-testid="stRadio"] label{background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:8px;padding:4px 12px;font-size:0.72rem;cursor:pointer;transition:all .2s;}
div[data-testid="stRadio"] label:hover{border-color:var(--blue);}

/* buttons */
.stButton button,.stDownloadButton button{background:linear-gradient(135deg,rgba(79,140,255,0.12),rgba(123,97,255,0.1)) !important;border:1px solid rgba(79,140,255,0.28) !important;color:var(--text-primary) !important;border-radius:10px !important;font-family:'Manrope',sans-serif !important;font-weight:600 !important;transition:all .25s ease !important;}
.stButton button:hover,.stDownloadButton button:hover{border-color:var(--cyan) !important;box-shadow:0 0 20px rgba(0,212,255,0.12) !important;transform:translateY(-1px) !important;}
.stButton button[kind="primary"]{background:linear-gradient(135deg,var(--blue),var(--purple)) !important;border:none !important;}

/* report button special */
.rpt-btn .stButton button{background:linear-gradient(135deg,rgba(255,209,102,0.15),rgba(255,107,107,0.1)) !important;border:1px solid rgba(255,209,102,0.35) !important;font-size:1rem !important;padding:0.8rem !important;}

/* dataframe */
div[data-testid="stDataFrame"]{border-radius:14px;overflow:hidden;border:1px solid var(--glass-border);}

/* selectbox / multiselect / slider */
div[data-testid="stSelectbox"] label,div[data-testid="stMultiSelect"] label,div[data-testid="stSlider"] label{
  color:var(--text-muted) !important;font-family:'JetBrains Mono',monospace !important;font-size:0.62rem !important;text-transform:uppercase !important;letter-spacing:1px !important;}

/* AI summary card */
.ai-card{border-radius:18px;border:1px solid rgba(123,97,255,0.25);background:linear-gradient(135deg,rgba(123,97,255,0.06),rgba(79,140,255,0.04));backdrop-filter:blur(16px);padding:1.5rem 1.6rem;}
.ai-title{font-size:1rem;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:9px;margin-bottom:0.8rem;}
.ai-body{font-size:0.88rem;color:var(--text-secondary);line-height:1.75;white-space:pre-wrap;}
</style>
""", unsafe_allow_html=True)

# ── Top bar ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div id="dash-topbar">
  <div class="tb-brand">
    <div class="tb-mark">A</div>
    <div class="tb-name">ARIA</div>
    <div class="tb-tag">Sales Intelligence · Dashboard</div>
    <div class="tb-tag">{filename}</div>
  </div>
  <div class="tb-right">
    <div class="tb-pill"><div class="tb-dot g"></div>Live Data</div>
    <div class="tb-pill"><div class="tb-dot b"></div>Neural Engine</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:

    st.markdown('<div class="sb-hdr">System</div>', unsafe_allow_html=True)
    st.markdown('<span class="sb-badge on"><span class="sb-dot"></span>All Systems Online</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-top:0.7rem;">
      <div class="sb-stat"><span class="lbl">File</span><span class="val" style="font-size:0.7rem;">{filename}</span></div>
      <div class="sb-stat"><span class="lbl">Rows</span><span class="val">{len(df)}</span></div>
      <div class="sb-stat"><span class="lbl">Columns</span><span class="val">{len(df.columns)}</span></div>
      <div class="sb-stat"><span class="lbl">AI Model</span><span class="val">LLaMA 3.3-70B</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-hdr" style="margin-top:1.2rem;">Date Period</div>', unsafe_allow_html=True)
    n_date_cols = max(len(df.columns) - 1, 1)
    date_range = st.slider("Day range", min_value=1, max_value=n_date_cols, value=(1, n_date_cols), label_visibility="collapsed")

    # Quick period presets
    preset = st.selectbox("Quick Select", ["Custom", "Last 7 Days", "Last 14 Days", "Last 30 Days", "Full Range"], label_visibility="collapsed")
    if preset == "Last 7 Days":
        date_range = (max(1, n_date_cols - 6), n_date_cols)
    elif preset == "Last 14 Days":
        date_range = (max(1, n_date_cols - 13), n_date_cols)
    elif preset == "Last 30 Days":
        date_range = (max(1, n_date_cols - 29), n_date_cols)
    elif preset == "Full Range":
        date_range = (1, n_date_cols)

    lo, hi = date_range
    st.markdown(f"""
    <div class="sb-stat"><span class="lbl">Period</span><span class="val">Day {lo} → Day {hi}</span></div>
    <div class="sb-stat"><span class="lbl">Days Selected</span><span class="val">{hi - lo + 1}</span></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-hdr" style="margin-top:1.2rem;">Filters</div>', unsafe_allow_html=True)

    all_people_df = get_salesperson_totals(df)
    all_names = all_people_df["Salesperson"].tolist() if not all_people_df.empty else []

    # Category filter
    all_cats = sorted(all_people_df["Category"].unique().tolist()) if not all_people_df.empty else []
    sel_cats = st.multiselect("Category", options=all_cats, default=all_cats, label_visibility="collapsed",
                               placeholder="Filter by category…")

    # Salesperson filter — respects category selection
    if sel_cats:
        available_names = all_people_df[all_people_df["Category"].isin(sel_cats)]["Salesperson"].tolist()
    else:
        available_names = all_names
    selected_people = st.multiselect("Salesperson", options=available_names, default=available_names,
                                      label_visibility="collapsed", placeholder="Filter by person…")

    st.markdown('<div class="sb-hdr" style="margin-top:1.2rem;">Display</div>', unsafe_allow_html=True)
    show_raw = st.checkbox("Show raw data table", value=True)
    show_week = st.checkbox("Show weekly breakdown", value=True)
    leaderboard_n = st.slider("Leaderboard top N", 5, 20, 10, label_visibility="collapsed")

    st.markdown('<div class="sb-hdr" style="margin-top:1.2rem;">Target</div>', unsafe_allow_html=True)
    monthly_target = st.number_input("Monthly Target (₹)", min_value=0, value=2000000, step=100000,
                                      label_visibility="collapsed")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("← New Upload", use_container_width=True):
        st.switch_page("app.py")

# ── Apply filters ──────────────────────────────────────────────────────────────
date_cols_all     = df.columns[1:]
selected_date_cols = date_cols_all[lo - 1 : hi]
filtered_df        = df[[df.columns[0]] + list(selected_date_cols)].copy()

person_totals = get_salesperson_totals(filtered_df)
if selected_people:
    person_totals = person_totals[person_totals["Salesperson"].isin(selected_people)]
if sel_cats:
    person_totals = person_totals[person_totals["Category"].isin(sel_cats)]

zero_list    = get_zero_sales(filtered_df)
daily_totals = get_daily_totals(filtered_df)
cat_totals   = get_category_totals(filtered_df)
real_mtd     = get_mtd_total(df)
real_ytd     = get_ytd_total(df)

total_sales   = float(person_totals["Total"].sum()) if not person_totals.empty else 0.0
avg_daily     = float(daily_totals.mean())          if len(daily_totals) else 0.0
n_active      = int((person_totals["Total"] > 0).sum()) if not person_totals.empty else 0
top_performer = person_totals.iloc[0]               if not person_totals.empty else None

today_val     = float(daily_totals.iloc[-1])  if len(daily_totals) >= 1 else 0.0
yest_val      = float(daily_totals.iloc[-2])  if len(daily_totals) >= 2 else 0.0
day_chg_pct   = ((today_val - yest_val) / yest_val * 100) if yest_val else 0.0

week_this     = float(daily_totals.iloc[-7:].sum())  if len(daily_totals) >= 7  else float(daily_totals.sum())
week_prev     = float(daily_totals.iloc[-14:-7].sum()) if len(daily_totals) >= 14 else 0.0
week_chg_pct  = ((week_this - week_prev) / week_prev * 100) if week_prev else 0.0

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Manrope, sans-serif", color="#AEB9D4"),
    margin=dict(l=10, r=10, t=35, b=10),
)

# ── Intelligence Banner ────────────────────────────────────────────────────────
d_cls   = "up" if day_chg_pct  >= 0 else "dn"
d_arrow = "▲"  if day_chg_pct  >= 0 else "▼"
w_cls   = "up" if week_chg_pct >= 0 else "dn"
w_arrow = "▲"  if week_chg_pct >= 0 else "▼"
tp_name = top_performer["Salesperson"] if top_performer is not None else "—"

st.markdown(f"""
<div id="banner">
  <div class="bn-top">
    <div>
      <div class="bn-title"><div class="bn-dot"></div>Intelligence Summary</div>
      <div class="bn-sub">Auto-generated overview · Day {lo} – Day {hi} · {hi-lo+1} days selected</div>
    </div>
  </div>
  <div class="bn-grid">
    <div class="bcell"><div class="lab">Total Sales</div><div class="num cy">₹{total_sales:,.0f}</div></div>
    <div class="bcell"><div class="lab">Avg / Day</div><div class="num gr">₹{avg_daily:,.0f}</div></div>
    <div class="bcell"><div class="lab">Top Performer</div><div class="num go" style="font-size:1.05rem;">{tp_name}</div></div>
    <div class="bcell"><div class="lab">Active Sellers</div><div class="num pu">{n_active}</div></div>
    <div class="bcell"><div class="lab">Today vs Yesterday</div><div class="num" style="font-size:1.05rem;">₹{today_val:,.0f}</div><div class="delta {d_cls}">{d_arrow} {abs(day_chg_pct):.1f}%</div></div>
    <div class="bcell"><div class="lab">This Week</div><div class="num" style="font-size:1.05rem;">₹{week_this:,.0f}</div><div class="delta {w_cls}">{w_arrow} {abs(week_chg_pct):.1f}%</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row (8 cards) ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Key Metrics<div class="ln"></div></div>', unsafe_allow_html=True)

progress_pct = min(real_mtd / monthly_target * 100, 100) if monthly_target else 0
best_idx     = int(daily_totals.values.argmax()) if len(daily_totals) else 0
worst_idx    = int(daily_totals.values.argmin()) if len(daily_totals) else 0
n_zero_days  = int((daily_totals == 0).sum())

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Total Sales</div><div class="kpi-val cy">₹{total_sales:,.0f}</div><div class="kpi-foot">Period: Day {lo}–{hi}</div></div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Month To Date</div><div class="kpi-val gr">₹{real_mtd:,.0f}</div><div class="kpi-foot">{progress_pct:.1f}% of target</div></div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Year To Date</div><div class="kpi-val go">₹{real_ytd:,.0f}</div><div class="kpi-foot">Cumulative YTD</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Daily Average</div><div class="kpi-val pu">₹{avg_daily:,.0f}</div><div class="kpi-foot">Over {hi-lo+1} days</div></div>""", unsafe_allow_html=True)

k5, k6, k7, k8 = st.columns(4)
with k5:
    tp_val = f"₹{top_performer['Total']:,.0f}" if top_performer is not None else "—"
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Top Performer</div><div class="kpi-val go" style="font-size:1.1rem;">{tp_name}</div><div class="kpi-foot">{tp_val}</div></div>""", unsafe_allow_html=True)
with k6:
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Best Day</div><div class="kpi-val gr">Day {best_idx+1}</div><div class="kpi-foot">₹{daily_totals.values[best_idx]:,.0f}</div></div>""", unsafe_allow_html=True)
with k7:
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Active Sellers</div><div class="kpi-val cy">{n_active}</div><div class="kpi-foot">of {len(person_totals)} tracked</div></div>""", unsafe_allow_html=True)
with k8:
    zero_color = "re" if len(zero_list) > 0 else "gr"
    st.markdown(f"""<div class="kpi"><div class="kpi-lab">Zero-Sale Alerts</div><div class="kpi-val {zero_color}">{len(zero_list)}</div><div class="kpi-foot">sellers with gaps</div></div>""", unsafe_allow_html=True)

# ── Daily Trend Chart ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Daily Sales Trend<div class="ln"></div></div>', unsafe_allow_html=True)

col_chart_ctrl, col_chart_main = st.columns([1, 4])
with col_chart_ctrl:
    trend_type = st.radio("Chart type", ["Line", "Bar", "Area", "Step"], key="trend_type")
    show_ma    = st.checkbox("Show 7-day MA", value=True)

with col_chart_main:
    st.markdown('<div class="gcard"><div class="gcard-title">📈 Daily Revenue · ' + trend_type + ' View</div>', unsafe_allow_html=True)
    if len(daily_totals):
        x_labels = [f"Day {i+1}" for i in range(len(daily_totals))]
        y_vals   = daily_totals.values

        fig = go.Figure()
        if trend_type == "Line":
            fig.add_trace(go.Scatter(x=x_labels, y=y_vals, mode="lines+markers",
                line=dict(color="#00D4FF", width=2.5, shape="spline"),
                marker=dict(size=5, color="#4F8CFF"), name="Daily Sales"))
        elif trend_type == "Bar":
            fig.add_trace(go.Bar(x=x_labels, y=y_vals,
                marker=dict(color="#4F8CFF", opacity=0.8,
                line=dict(color="#00D4FF", width=0.5)), name="Daily Sales"))
        elif trend_type == "Area":
            fig.add_trace(go.Scatter(x=x_labels, y=y_vals, mode="lines",
                line=dict(color="#00D4FF", width=2, shape="spline"),
                fill="tozeroy", fillcolor="rgba(79,140,255,0.12)", name="Daily Sales"))
        elif trend_type == "Step":
            fig.add_trace(go.Scatter(x=x_labels, y=y_vals, mode="lines",
                line=dict(color="#7B61FF", width=2, shape="hv"), name="Daily Sales"))

        # 7-day moving average
        if show_ma and len(y_vals) >= 7:
            ma = pd.Series(y_vals).rolling(7).mean().values
            fig.add_trace(go.Scatter(x=x_labels, y=ma, mode="lines",
                line=dict(color="#FFD166", width=1.5, dash="dot"), name="7-Day MA"))

        fig.update_layout(**PLOT, height=340, showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
            tickprefix="₹", tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div style='color:var(--text-muted);'>No data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Leaderboard + Zero Alert ───────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Team Performance<div class="ln"></div></div>', unsafe_allow_html=True)
p1, p2 = st.columns([1.4, 1])

with p1:
    st.markdown('<div class="gcard"><div class="gcard-title">🏆 Salesperson Leaderboard</div>', unsafe_allow_html=True)
    if not person_totals.empty:
        max_v   = person_totals["Total"].max()
        medals  = {0: "r1", 1: "r2", 2: "r3"}
        rows_html = ""
        for i, row in person_totals.head(leaderboard_n).iterrows():
            pct      = (row["Total"] / max_v * 100) if max_v else 0
            rank_cls = medals.get(i, "")
            rows_html += f"""
            <div class="lb-row">
              <div class="lb-rank {rank_cls}">#{i+1}</div>
              <div class="lb-info">
                <div class="lb-top">
                  <span>
                    <span class="lb-name">{row['Salesperson']}</span>
                    <span class="lb-cat"> · {row['Category']}</span>
                  </span>
                  <span class="lb-val">₹{row['Total']:,.0f}</span>
                </div>
                <div class="lb-bar"><div class="lb-fill" style="width:{pct:.1f}%;"></div></div>
              </div>
            </div>"""
        st.markdown(rows_html + "</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--text-muted);font-size:0.85rem;'>No data for this selection.</div></div>", unsafe_allow_html=True)

with p2:
    st.markdown('<div class="gcard"><div class="gcard-title">⚠️ Zero Sales Alerts</div>', unsafe_allow_html=True)
    rel_zero = [n for n in zero_list if not selected_people or n in selected_people]
    if rel_zero:
        pills = "".join([f'<div class="alert-pill"><div class="alert-dot"></div>{n} · had at least one zero day</div>' for n in rel_zero[:10]])
        st.markdown(pills, unsafe_allow_html=True)
        if len(rel_zero) > 10:
            st.markdown(f"<div style='font-size:0.75rem;color:var(--text-muted);margin-top:0.4rem;'>+ {len(rel_zero)-10} more</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-pill">✅ No zero-sales days in selected period</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Category Analysis ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Category Analysis<div class="ln"></div></div>', unsafe_allow_html=True)
ca1, ca2 = st.columns(2)

with ca1:
    st.markdown('<div class="gcard"><div class="gcard-title">🧬 Category Health</div>', unsafe_allow_html=True)
    if not cat_totals.empty:
        cat_max = cat_totals["Total"].max()
        rows_html = ""
        for _, row in cat_totals.iterrows():
            ratio = row["Total"] / cat_max if cat_max else 0
            if ratio >= 0.6:   bcls, btxt = "strong",   "Strong"
            elif ratio >= 0.25: bcls, btxt = "moderate", "Moderate"
            else:               bcls, btxt = "low",      "Low"
            share = ratio * 100
            rows_html += f"""
            <div class="health-row">
              <span class="health-name">{row['Category']}</span>
              <span class="health-val">₹{row['Total']:,.0f}</span>
              <span style="font-size:0.72rem;color:var(--text-muted);">{share:.1f}%</span>
              <span class="hbadge {bcls}">{btxt}</span>
            </div>"""
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--text-muted);font-size:0.85rem;'>No category data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with ca2:
    st.markdown('<div class="gcard"><div class="gcard-title">📊 Category Breakdown</div>', unsafe_allow_html=True)
    cat_chart_type = st.radio("View", ["Donut", "Bar", "Treemap"], key="cat_chart", horizontal=True)
    if not cat_totals.empty:
        COLORS = ["#4F8CFF","#7B61FF","#00D4FF","#00FFC6","#FFD166","#FF6B6B","#A78BFA","#38BDF8"]
        if cat_chart_type == "Donut":
            cf = px.pie(cat_totals, names="Category", values="Total", hole=0.55,
                        color_discrete_sequence=COLORS)
            cf.update_traces(textfont_color="#F4F7FC", marker=dict(line=dict(color="#02030A", width=2)))
            cf.update_layout(**PLOT, height=280, legend=dict(font=dict(size=9)))
        elif cat_chart_type == "Bar":
            cf = px.bar(cat_totals, x="Total", y="Category", orientation="h",
                        color="Category", color_discrete_sequence=COLORS)
            cf.update_layout(**PLOT, height=280, showlegend=False)
            cf.update_xaxes(tickprefix="₹", tickformat=",.0f")
        else:
            cf = px.treemap(cat_totals, path=["Category"], values="Total",
                            color="Total", color_continuous_scale=["#06091A","#4F8CFF","#00FFC6"])
            cf.update_layout(**PLOT, height=280)
        st.plotly_chart(cf, use_container_width=True)
    else:
        st.markdown("<div style='color:var(--text-muted);'>No data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Sales Distribution ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Sales Distribution<div class="ln"></div></div>', unsafe_allow_html=True)
d1c, d2c = st.columns(2)

with d1c:
    st.markdown('<div class="gcard"><div class="gcard-title">🥧 Salesperson Share</div>', unsafe_allow_html=True)
    pie_type = st.radio("View", ["Pie", "Bar", "Funnel"], key="pie_type", horizontal=True)
    if not person_totals.empty:
        top_n = person_totals.head(8)
        COLORS = ["#4F8CFF","#7B61FF","#00D4FF","#00FFC6","#FFD166","#FF6B6B","#A78BFA","#38BDF8"]
        if pie_type == "Pie":
            pf = px.pie(top_n, names="Salesperson", values="Total", hole=0.5,
                        color_discrete_sequence=COLORS)
            pf.update_traces(textfont_color="#F4F7FC", marker=dict(line=dict(color="#02030A",width=2)))
            pf.update_layout(**PLOT, height=300, legend=dict(font=dict(size=9)))
        elif pie_type == "Bar":
            pf = px.bar(top_n, x="Salesperson", y="Total", color="Category",
                        color_discrete_sequence=COLORS)
            pf.update_layout(**PLOT, height=300, showlegend=True)
            pf.update_yaxes(tickprefix="₹", tickformat=",.0f")
        else:
            pf = go.Figure(go.Funnel(
                y=top_n["Salesperson"].tolist(),
                x=top_n["Total"].tolist(),
                textposition="inside",
                marker=dict(color=COLORS[:len(top_n)]),
                texttemplate="%{label}<br>₹%{value:,.0f}"
            ))
            pf.update_layout(**PLOT, height=300)
        st.plotly_chart(pf, use_container_width=True)
    else:
        st.markdown("<div style='color:var(--text-muted);'>No data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with d2c:
    st.markdown('<div class="gcard"><div class="gcard-title">📉 Sales Heatmap (by person × day)</div>', unsafe_allow_html=True)
    if not person_totals.empty and len(selected_date_cols) > 0:
        top_people = person_totals.head(10)["Salesperson"].tolist()
        hm_df = filtered_df[filtered_df.iloc[:, 0].isin(top_people)].copy()
        hm_df = hm_df.set_index(hm_df.columns[0])
        hm_df = hm_df.apply(pd.to_numeric, errors="coerce").fillna(0)
        if not hm_df.empty:
            hm_fig = px.imshow(
                hm_df,
                color_continuous_scale=["#02030A","#071124","#4F8CFF","#00FFC6"],
                aspect="auto",
                labels=dict(x="Day", y="Salesperson", color="₹ Sales")
            )
            hm_fig.update_layout(**PLOT, height=300)
            hm_fig.update_coloraxes(colorbar=dict(tickprefix="₹",tickformat=",.0f",len=0.8))
            st.plotly_chart(hm_fig, use_container_width=True)
        else:
            st.markdown("<div style='color:var(--text-muted);'>No heatmap data.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--text-muted);'>No data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Weekly Breakdown ───────────────────────────────────────────────────────────
if show_week and len(daily_totals) > 0:
    st.markdown('<div class="sec-hdr">◈ Weekly Breakdown<div class="ln"></div></div>', unsafe_allow_html=True)
    week_data = []
    for w in range((len(daily_totals) + 6) // 7):
        chunk = daily_totals.values[w*7 : (w+1)*7]
        week_data.append({
            "Week": f"Week {w+1}",
            "Total": chunk.sum(),
            "Avg":   chunk.mean(),
            "Best":  chunk.max(),
            "Days":  len(chunk),
        })
    wdf = pd.DataFrame(week_data)

    wf = go.Figure()
    wf.add_trace(go.Bar(x=wdf["Week"], y=wdf["Total"],
        name="Total", marker_color="#4F8CFF", opacity=0.85))
    wf.add_trace(go.Scatter(x=wdf["Week"], y=wdf["Avg"],
        mode="lines+markers", name="Avg/Day",
        line=dict(color="#FFD166", width=2), yaxis="y2"))
    wf.update_layout(**PLOT, height=300, showlegend=True,
        yaxis=dict(tickprefix="₹", tickformat=",.0f", title="Weekly Total"),
        yaxis2=dict(tickprefix="₹", tickformat=",.0f", overlaying="y", side="right", title="Avg/Day"),
        legend=dict(orientation="h", y=1.08))
    st.plotly_chart(wf, use_container_width=True)

# ── Targets & Summary ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Targets &amp; Summary<div class="ln"></div></div>', unsafe_allow_html=True)
t1, t2, t3 = st.columns(3)

with t1:
    st.markdown('<div class="gcard"><div class="gcard-title">🎯 Month Target</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="prog-track"><div class="prog-fill" style="width:{progress_pct:.1f}%;"></div></div>
    <div class="prog-cap"><span>₹{real_mtd:,.0f} achieved</span><span>{progress_pct:.1f}% of ₹{monthly_target:,.0f}</span></div>
    <div style="margin-top:0.7rem;font-size:0.78rem;color:var(--text-muted);">
      Remaining: <b style="color:var(--text-primary);">₹{max(0, monthly_target - real_mtd):,.0f}</b>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with t2:
    st.markdown('<div class="gcard"><div class="gcard-title">📅 Period Summary</div>', unsafe_allow_html=True)
    if len(daily_totals):
        rows = [
            ("Best Day",     f"Day {best_idx+1}",  f"₹{daily_totals.values[best_idx]:,.0f}",  "var(--green)"),
            ("Worst Day",    f"Day {worst_idx+1}", f"₹{daily_totals.values[worst_idx]:,.0f}", "var(--red)"),
            ("Zero Days",    f"{n_zero_days}",      "no sales",                                "var(--red)" if n_zero_days else "var(--green)"),
            ("Days Tracked", f"{hi-lo+1}",          "total",                                   "var(--cyan)"),
        ]
        html = ""
        for lbl, v1, v2, col in rows:
            html += f'<div class="day-row"><span style="color:var(--text-muted);">{lbl}</span><span style="color:{col};font-weight:700;">{v1} · {v2}</span></div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with t3:
    st.markdown('<div class="gcard"><div class="gcard-title">📊 YTD Progress</div>', unsafe_allow_html=True)
    ytd_target = monthly_target * 12
    ytd_pct    = min(real_ytd / ytd_target * 100, 100) if ytd_target else 0
    st.markdown(f"""
    <div class="prog-track"><div class="prog-fill" style="width:{ytd_pct:.1f}%;background:linear-gradient(90deg,var(--purple),var(--gold));"></div></div>
    <div class="prog-cap"><span>₹{real_ytd:,.0f} YTD</span><span>{ytd_pct:.1f}% of annual</span></div>
    <div style="margin-top:0.7rem;font-size:0.78rem;color:var(--text-muted);">
      Annual Target: <b style="color:var(--text-primary);">₹{ytd_target:,.0f}</b>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Raw Data Table ─────────────────────────────────────────────────────────────
if show_raw:
    st.markdown('<div class="sec-hdr">◈ Full Dataset<div class="ln"></div></div>', unsafe_allow_html=True)

    tbl_view = st.radio("Table view", ["Filtered", "Full Dataset", "Salesperson Totals", "Category Totals"],
                         horizontal=True, key="tbl_view")
    if tbl_view == "Filtered":
        st.dataframe(filtered_df, use_container_width=True, height=360)
    elif tbl_view == "Full Dataset":
        st.dataframe(df, use_container_width=True, height=360)
    elif tbl_view == "Salesperson Totals":
        st.dataframe(person_totals.style.format({"Total": "₹{:,.0f}"}), use_container_width=True, height=360)
    else:
        st.dataframe(cat_totals.style.format({"Total": "₹{:,.0f}"}), use_container_width=True, height=360)

# ── Export ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Export Data<div class="ln"></div></div>', unsafe_allow_html=True)
e1, e2, e3 = st.columns(3)

with e1:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        filtered_df.to_excel(writer,  index=False, sheet_name="Filtered")
        person_totals.to_excel(writer, index=False, sheet_name="Leaderboard")
        cat_totals.to_excel(writer,    index=False, sheet_name="Categories")
    st.download_button("⬇ Download Excel Report", data=buf.getvalue(),
        file_name=f"aria_report_{filename.split('.')[0]}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)

with e2:
    st.download_button("⬇ Download AI Summary (.txt)", data=get_data_summary_for_ai(df),
        file_name="aria_ai_context.txt", mime="text/plain", use_container_width=True)

with e3:
    csv_buf = BytesIO()
    filtered_df.to_csv(csv_buf, index=False)
    st.download_button("⬇ Download CSV", data=csv_buf.getvalue(),
        file_name=f"aria_filtered_{filename.split('.')[0]}.csv",
        mime="text/csv", use_container_width=True)

# ── Generate PDF Report ────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">◈ Generate Report<div class="ln"></div></div>', unsafe_allow_html=True)

st.markdown("""
<div style="border-radius:16px;border:1px solid rgba(255,209,102,0.2);background:linear-gradient(135deg,rgba(255,209,102,0.06),rgba(123,97,255,0.04));padding:1.2rem 1.5rem;margin-bottom:1rem;">
  <div style="font-size:0.95rem;font-weight:700;color:var(--text-primary);margin-bottom:0.4rem;">📄 ARIA Intelligence Report</div>
  <div style="font-size:0.82rem;color:var(--text-muted);">Generates a full PDF with all charts, tables, KPIs, and an AI-written narrative summary powered by LLaMA 3.3-70B via Groq.</div>
</div>
""", unsafe_allow_html=True)

gen_col, _ = st.columns([1, 2])
with gen_col:
    gen_report = st.button("🚀 Generate Full PDF Report", use_container_width=True, type="primary")

if gen_report:
    with st.spinner("ARIA is generating your report — calling Groq AI for summary…"):

        # ── 1. AI summary via Groq ─────────────────────────────────────────────
        data_summary = get_data_summary_for_ai(df)
        ai_prompt = f"""You are ARIA, an expert sales analyst. 
Generate a concise but comprehensive executive report summary (around 300-400 words) for the following homeopathic company sales data.

Include:
1. Overall performance highlights
2. Top performers and standout categories
3. Trends and patterns observed
4. Areas of concern (zero-sales, low performers)
5. Actionable recommendations

Write in a professional, clear tone. Use Indian currency formatting (₹).

{data_summary}"""

        ai_summary = ask_groq(
            question=ai_prompt,
            data_summary=data_summary,
            chat_history=[]
        )

        # ── 2. Build PDF ───────────────────────────────────────────────────────
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                             Table, TableStyle, Image, HRFlowable,
                                             PageBreak)
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Font — try bundled DejaVu, fallback to Helvetica with Rs.
            font_path = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "DejaVuSans.ttf")
            font_bold_path = font_path.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
            USE_DEJAVU = False
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("DejaVu", font_path))
                    if os.path.exists(font_bold_path):
                        pdfmetrics.registerFont(TTFont("DejaVuBold", font_bold_path))
                    USE_DEJAVU = True
                except Exception:
                    pass

            BASE_FONT      = "DejaVu"     if USE_DEJAVU else "Helvetica"
            BASE_FONT_BOLD = "DejaVuBold" if USE_DEJAVU else "Helvetica-Bold"
            INR = "₹" if USE_DEJAVU else "Rs."

            def fmt(v):
                return f"{INR}{v:,.0f}"

            # ── Colours ──────────────────────────────────────────────────────
            C_BG    = colors.HexColor("#02030A")
            C_BLUE  = colors.HexColor("#4F8CFF")
            C_CYAN  = colors.HexColor("#00D4FF")
            C_GREEN = colors.HexColor("#00FFC6")
            C_GOLD  = colors.HexColor("#FFD166")
            C_MUTED = colors.HexColor("#6B7694")
            C_WHITE = colors.white
            C_DARK  = colors.HexColor("#06091A")

            # ── Styles ────────────────────────────────────────────────────────
            styles = getSampleStyleSheet()
            def S(name, **kw):
                return ParagraphStyle(name, fontName=BASE_FONT, **kw)
            def SB(name, **kw):
                return ParagraphStyle(name, fontName=BASE_FONT_BOLD, **kw)

            s_title  = SB("title",  fontSize=28, textColor=C_WHITE, spaceAfter=4, leading=32)
            s_sub    = S("sub",     fontSize=12, textColor=C_MUTED, spaceAfter=2)
            s_h1     = SB("h1",     fontSize=14, textColor=C_CYAN,  spaceBefore=14, spaceAfter=6)
            s_h2     = SB("h2",     fontSize=11, textColor=C_GOLD,  spaceBefore=8,  spaceAfter=4)
            s_body   = S("body",    fontSize=9,  textColor=colors.HexColor("#AEB9D4"), leading=14, spaceAfter=4)
            s_kpi_n  = SB("kpin",   fontSize=20, textColor=C_CYAN)
            s_kpi_l  = S("kpil",    fontSize=7,  textColor=C_MUTED)
            s_ai     = S("ai",      fontSize=9.5,textColor=colors.HexColor("#C8D4E8"), leading=16)

            buf_pdf = BytesIO()
            doc = SimpleDocTemplate(buf_pdf, pagesize=A4,
                leftMargin=1.8*cm, rightMargin=1.8*cm,
                topMargin=1.8*cm,  bottomMargin=1.8*cm)

            story = []

            # ── Cover ─────────────────────────────────────────────────────────
            story.append(Spacer(1, 1.5*cm))
            story.append(Paragraph("ARIA", s_title))
            story.append(Paragraph("Sales Intelligence Report", SB("t2", fontSize=16, textColor=C_BLUE, spaceAfter=4)))
            story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}", s_sub))
            story.append(Paragraph(f"Source file: {filename}  ·  Period: Day {lo}–Day {hi}  ·  {hi-lo+1} days", s_sub))
            story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=16))
            story.append(Spacer(1, 0.5*cm))

            # ── KPI summary table ─────────────────────────────────────────────
            story.append(Paragraph("Key Performance Indicators", s_h1))
            kpi_data = [
                ["Metric", "Value", "Metric", "Value"],
                ["Total Sales",    fmt(total_sales), "MTD",           fmt(real_mtd)],
                ["YTD",            fmt(real_ytd),    "Daily Average",  fmt(avg_daily)],
                ["Top Performer",  tp_name,           "Active Sellers", str(n_active)],
                ["Best Day",       f"Day {best_idx+1} · {fmt(daily_totals.values[best_idx])}",
                 "Zero Alerts",    str(len(zero_list))],
                ["Month Target",   fmt(monthly_target), "Achievement",  f"{progress_pct:.1f}%"],
            ]
            kpi_tbl = Table(kpi_data, colWidths=[4*cm, 4.5*cm, 4*cm, 4.5*cm])
            kpi_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0),   C_DARK),
                ("TEXTCOLOR",  (0,0), (-1,0),   C_CYAN),
                ("FONTNAME",   (0,0), (-1,0),   BASE_FONT_BOLD),
                ("FONTSIZE",   (0,0), (-1,-1),  8),
                ("FONTNAME",   (0,1), (-1,-1),  BASE_FONT),
                ("TEXTCOLOR",  (0,1), (-1,-1),  C_WHITE),
                ("TEXTCOLOR",  (1,1), (1,-1),   C_GREEN),
                ("TEXTCOLOR",  (3,1), (3,-1),   C_GOLD),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#06091A"), colors.HexColor("#040712")]),
                ("GRID",       (0,0), (-1,-1),  0.3, colors.HexColor("#1A2040")),
                ("TOPPADDING", (0,0), (-1,-1),  5),
                ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                ("LEFTPADDING",(0,0), (-1,-1),  6),
            ]))
            story.append(kpi_tbl)
            story.append(Spacer(1, 0.6*cm))

            # ── Leaderboard table ─────────────────────────────────────────────
            story.append(Paragraph("Salesperson Leaderboard", s_h1))
            if not person_totals.empty:
                lb_header = [["Rank", "Salesperson", "Category", "Total Sales", "Share %"]]
                total_s   = person_totals["Total"].sum()
                lb_rows   = []
                for i, row in person_totals.head(15).iterrows():
                    share = row["Total"] / total_s * 100 if total_s else 0
                    lb_rows.append([f"#{i+1}", row["Salesperson"], row["Category"],
                                    fmt(row["Total"]), f"{share:.1f}%"])
                lb_tbl = Table(lb_header + lb_rows,
                               colWidths=[1.5*cm, 4.5*cm, 4.5*cm, 4*cm, 2.5*cm])
                lb_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0),   C_DARK),
                    ("TEXTCOLOR",  (0,0), (-1,0),   C_GOLD),
                    ("FONTNAME",   (0,0), (-1,0),   BASE_FONT_BOLD),
                    ("FONTSIZE",   (0,0), (-1,-1),  8),
                    ("FONTNAME",   (0,1), (-1,-1),  BASE_FONT),
                    ("TEXTCOLOR",  (0,1), (-1,-1),  C_WHITE),
                    ("TEXTCOLOR",  (3,1), (3,-1),   C_GREEN),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#06091A"), colors.HexColor("#040712")]),
                    ("GRID",       (0,0), (-1,-1),  0.3, colors.HexColor("#1A2040")),
                    ("TOPPADDING", (0,0), (-1,-1),  4),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                    ("LEFTPADDING",(0,0), (-1,-1),  5),
                ]))
                story.append(lb_tbl)

            story.append(PageBreak())

            # ── Category breakdown ─────────────────────────────────────────────
            story.append(Paragraph("Category Performance", s_h1))
            if not cat_totals.empty:
                ct_header = [["Category", "Total Sales", "Share %", "Health"]]
                cat_total_sum = cat_totals["Total"].sum()
                ct_rows = []
                for _, row in cat_totals.iterrows():
                    share = row["Total"] / cat_total_sum * 100 if cat_total_sum else 0
                    ratio = row["Total"] / cat_totals["Total"].max() if cat_totals["Total"].max() else 0
                    health = "Strong" if ratio >= 0.6 else ("Moderate" if ratio >= 0.25 else "Low")
                    ct_rows.append([row["Category"], fmt(row["Total"]), f"{share:.1f}%", health])
                ct_tbl = Table(ct_header + ct_rows, colWidths=[5.5*cm, 4.5*cm, 3*cm, 4*cm])
                ct_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), C_DARK),
                    ("TEXTCOLOR",  (0,0), (-1,0), C_CYAN),
                    ("FONTNAME",   (0,0), (-1,0), BASE_FONT_BOLD),
                    ("FONTSIZE",   (0,0), (-1,-1), 8),
                    ("FONTNAME",   (0,1), (-1,-1), BASE_FONT),
                    ("TEXTCOLOR",  (0,1), (-1,-1), C_WHITE),
                    ("TEXTCOLOR",  (1,1), (1,-1),  C_GREEN),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#06091A"), colors.HexColor("#040712")]),
                    ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#1A2040")),
                    ("TOPPADDING", (0,0), (-1,-1), 4),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                    ("LEFTPADDING",(0,0), (-1,-1),  5),
                ]))
                story.append(ct_tbl)

            story.append(Spacer(1, 0.5*cm))

            # ── Static charts (matplotlib) ─────────────────────────────────────
            story.append(Paragraph("Daily Sales Trend", s_h1))

            def mpl_fig_to_image(fig):
                img_buf = BytesIO()
                fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=150,
                            facecolor="#02030A")
                img_buf.seek(0)
                plt.close(fig)
                return img_buf

            # Trend chart
            fig_t, ax_t = plt.subplots(figsize=(14, 4), facecolor="#02030A")
            ax_t.set_facecolor("#06091A")
            x_t = range(len(daily_totals))
            ax_t.fill_between(x_t, daily_totals.values, alpha=0.18, color="#4F8CFF")
            ax_t.plot(x_t, daily_totals.values, color="#00D4FF", linewidth=2.5)
            ax_t.scatter(x_t, daily_totals.values, color="#4F8CFF", s=25, zorder=5)
            if len(daily_totals) >= 7:
                ma7 = pd.Series(daily_totals.values).rolling(7).mean()
                ax_t.plot(x_t, ma7, color="#FFD166", linewidth=1.5, linestyle="--", label="7-Day MA")
                ax_t.legend(facecolor="#06091A", edgecolor="#1A2040", labelcolor="#AEB9D4", fontsize=8)
            ax_t.set_xlabel("Day", color="#6B7694", fontsize=9)
            ax_t.set_ylabel("Sales (₹)", color="#6B7694", fontsize=9)
            ax_t.tick_params(colors="#6B7694", labelsize=8)
            ax_t.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}K" if x >= 1000 else str(int(x))))
            ax_t.spines[:].set_color("#1A2040")
            ax_t.grid(axis="y", color="#1A2040", linewidth=0.5)
            img_t = mpl_fig_to_image(fig_t)
            story.append(Image(img_t, width=17*cm, height=5*cm))
            story.append(Spacer(1, 0.4*cm))

            # Category bar chart
            story.append(Paragraph("Category Sales Breakdown", s_h1))
            if not cat_totals.empty:
                fig_c, ax_c = plt.subplots(figsize=(12, 4), facecolor="#02030A")
                ax_c.set_facecolor("#06091A")
                pal = ["#4F8CFF","#7B61FF","#00D4FF","#00FFC6","#FFD166","#FF6B6B"]
                bars = ax_c.barh(cat_totals["Category"], cat_totals["Total"],
                                  color=pal[:len(cat_totals)], alpha=0.88)
                for bar, val in zip(bars, cat_totals["Total"]):
                    ax_c.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height()/2,
                              f"₹{val/1e3:.1f}K", va="center", color="#AEB9D4", fontsize=8)
                ax_c.set_xlabel("Total Sales (₹)", color="#6B7694", fontsize=9)
                ax_c.tick_params(colors="#6B7694", labelsize=8)
                ax_c.spines[:].set_color("#1A2040")
                ax_c.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}K"))
                ax_c.grid(axis="x", color="#1A2040", linewidth=0.5)
                img_c = mpl_fig_to_image(fig_c)
                story.append(Image(img_c, width=15*cm, height=5*cm))

            story.append(PageBreak())

            # ── Zero sales list ────────────────────────────────────────────────
            story.append(Paragraph("Zero-Sales Alerts", s_h1))
            if zero_list:
                za_header = [["Salesperson"]]
                za_rows   = [[n] for n in zero_list]
                za_tbl    = Table(za_header + za_rows, colWidths=[17*cm])
                za_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0),   C_DARK),
                    ("TEXTCOLOR",  (0,0), (-1,0),   colors.HexColor("#FF6B6B")),
                    ("FONTNAME",   (0,0), (-1,0),   BASE_FONT_BOLD),
                    ("FONTSIZE",   (0,0), (-1,-1),  8),
                    ("FONTNAME",   (0,1), (-1,-1),  BASE_FONT),
                    ("TEXTCOLOR",  (0,1), (-1,-1),  C_WHITE),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#0D0610"), colors.HexColor("#06091A")]),
                    ("GRID",       (0,0), (-1,-1),  0.3, colors.HexColor("#2A1020")),
                    ("TOPPADDING", (0,0), (-1,-1),  3),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 3),
                    ("LEFTPADDING",(0,0), (-1,-1),  5),
                ]))
                story.append(za_tbl)
            else:
                story.append(Paragraph("✓ No zero-sales alerts in the selected period.", s_body))

            story.append(Spacer(1, 0.6*cm))
            story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE))
            story.append(Spacer(1, 0.4*cm))

            # ── AI Summary ────────────────────────────────────────────────────
            story.append(Paragraph("AI-Generated Executive Summary", s_h1))
            story.append(Paragraph("Powered by LLaMA 3.3-70B via Groq API", s_sub))
            story.append(Spacer(1, 0.3*cm))
            for para in ai_summary.split("\n"):
                para = para.strip()
                if para:
                    story.append(Paragraph(para, s_ai))
                    story.append(Spacer(1, 0.15*cm))

            story.append(Spacer(1, 0.6*cm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=C_MUTED))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(f"ARIA Sales Intelligence Platform  ·  Report generated {datetime.datetime.now().strftime('%d %B %Y')}  ·  Powered by LLaMA 3.3-70B",
                S("footer", fontSize=7, textColor=C_MUTED, alignment=1)))

            # ── Build PDF ──────────────────────────────────────────────────────
            def draw_bg(canvas, doc):
                canvas.saveState()
                canvas.setFillColor(C_BG)
                canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
                canvas.restoreState()

            doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)
            pdf_bytes = buf_pdf.getvalue()

            st.success("✅ Report generated successfully!")
            st.download_button(
                "⬇ Download ARIA Intelligence Report (PDF)",
                data=pdf_bytes,
                file_name=f"ARIA_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            # Show AI summary inline too
            st.markdown('<div class="sec-hdr">◈ AI Executive Summary<div class="ln"></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-card"><div class="ai-title">🤖 ARIA Analysis</div><div class="ai-body">{ai_summary}</div></div>', unsafe_allow_html=True)

        except ImportError:
            st.error("reportlab not installed. Run: pip install reportlab")
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            st.exception(e)

# ── Navigation ──────────────────────────────────────────────────────────────────
st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
if st.button("Continue to AI Assistant →", use_container_width=True, type="primary"):
    st.switch_page("pages/2_AI_Chat.py")