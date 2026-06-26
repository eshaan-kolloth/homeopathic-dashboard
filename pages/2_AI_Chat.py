import streamlit as st
import datetime
import os
import re
import time
import traceback
from io import BytesIO

from utils.groq_client import ask_groq
from utils.data_processor import (
    get_salesperson_totals,
    get_zero_sales,
    get_daily_totals,
    get_category_totals,
    get_mtd_total,
    get_ytd_total,
    get_data_summary_for_ai,
)

st.set_page_config(
    page_title="ARIA · AI Copilot",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════
# GLOBAL CSS — Neural Glass Dark Theme + Animations
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

*,*::before,*::after { box-sizing: border-box; }

:root {
  --bg-1: #02030A; --bg-2: #040712; --bg-3: #06091A;
  --blue: #4F8CFF; --purple: #7B61FF; --cyan: #00D4FF;
  --green: #00FFC6; --gold: #FFD166; --red: #FF6B6B;
  --text-primary: #F4F7FC; --text-secondary: #AEB9D4; --text-muted: #6B7694;
  --glass-border: rgba(255,255,255,0.07); --glass-bg: rgba(255,255,255,0.03);
}

html, body, .stApp {
  background: radial-gradient(ellipse 130% 80% at 50% -10%,
    rgba(15,20,60,0.95) 0%, var(--bg-2) 50%, var(--bg-1) 100%) !important;
  color: var(--text-secondary);
  font-family: 'Manrope', sans-serif;
}

#MainMenu, footer, header, .stDeployButton { visibility: hidden; }

.block-container {
  padding: 1.2rem 2vw 5rem !important;
  max-width: 900px !important;
  margin: 0 auto !important;
}

/* ── ANIMATIONS ── */
@keyframes dotPulse { 0%,100%{opacity:1;} 50%{opacity:0.25;} }
@keyframes fadeSlideUp { from{opacity:0;transform:translateY(14px);} to{opacity:1;transform:translateY(0);} }
@keyframes glowPulse { 0%,100%{box-shadow:0 0 8px rgba(79,140,255,0.3);} 50%{box-shadow:0 0 22px rgba(79,140,255,0.6);} }
@keyframes shimmer { 0%{background-position:-200% 0;} 100%{background-position:200% 0;} }
@keyframes orbitSpin { from{transform:rotate(0deg);} to{transform:rotate(360deg);} }
@keyframes typingBounce { 0%,60%,100%{transform:translateY(0);} 30%{transform:translateY(-6px);} }
@keyframes modeActivate { 0%{transform:scale(0.96);opacity:0.6;} 100%{transform:scale(1);opacity:1;} }

/* ── TOPBAR ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.65rem 1.1rem; margin-bottom: 1.1rem;
  background: rgba(6,9,26,0.75);
  border: 1px solid rgba(79,140,255,0.15);
  border-radius: 16px; backdrop-filter: blur(24px);
  animation: fadeSlideUp 0.5s ease both;
}
.tb-left { display: flex; align-items: center; gap: 0.8rem; }
.tb-logo {
  width: 34px; height: 34px; border-radius: 10px;
  background: linear-gradient(135deg, var(--blue), var(--purple) 55%, var(--cyan));
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; font-weight: 900; color: #fff; flex-shrink: 0;
  animation: glowPulse 3s ease infinite;
}
.tb-title { font-size: 1rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.3px; }
.tb-badge {
  font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; font-weight: 600;
  padding: 3px 10px; border-radius: 99px; border: 1px solid;
  transition: all 0.3s ease;
}
.tb-right { display: flex; align-items: center; gap: 10px; }
.tb-stat {
  font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; color: var(--text-muted);
  background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
  padding: 3px 8px; border-radius: 8px;
}
.tb-live { display: flex; align-items: center; gap: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; color: var(--green); }
.tb-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); animation: dotPulse 2s ease infinite; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: rgba(3,5,15,0.98) !important;
  border-right: 1px solid rgba(79,140,255,0.1) !important;
}
section[data-testid="stSidebar"] * { color: var(--text-secondary) !important; }

.sb-label {
  font-family: 'JetBrains Mono', monospace; font-size: 0.54rem;
  color: var(--cyan); letter-spacing: 2.5px; text-transform: uppercase;
  padding: 0.5rem 0 0.25rem; border-bottom: 1px solid rgba(0,212,255,0.12);
  margin-bottom: 0.5rem; margin-top: 0.8rem;
}

/* MODE BUTTONS — Segmented control feel */
div[data-testid="stVerticalBlock"] .mode-btn button {
  border-radius: 10px !important; font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.72rem !important; font-weight: 600 !important;
  padding: 0.55rem 0.8rem !important; width: 100% !important;
  text-align: left !important; transition: all 0.2s ease !important;
  margin-bottom: 5px !important;
}
.mode-btn-off button {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  color: var(--text-muted) !important;
}
.mode-btn-off button:hover {
  background: rgba(79,140,255,0.08) !important;
  border-color: rgba(79,140,255,0.3) !important;
  color: var(--blue) !important;
  transform: translateX(3px);
}
.mode-btn-on button {
  border: 1px solid !important; font-weight: 700 !important;
  animation: modeActivate 0.25s ease both;
}

.mode-desc {
  font-size: 0.67rem; line-height: 1.55; margin: -2px 0 10px;
  padding: 6px 10px; border-radius: 8px;
  background: rgba(255,255,255,0.02); border-left: 2px solid;
}

/* KPI cards */
.sb-kpi {
  background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border);
  border-radius: 10px; padding: 0.55rem 0.75rem; margin-bottom: 0.4rem;
  position: relative; overflow: hidden; transition: all 0.2s;
}
.sb-kpi:hover { background: rgba(255,255,255,0.04); transform: translateX(2px); }
.sb-kpi::before { content:''; position:absolute; left:0; top:0; bottom:0; width:3px; border-radius:10px 0 0 10px; }
.kc1::before{background:var(--cyan);} .kc2::before{background:var(--gold);}
.kc3::before{background:var(--green);} .kc4::before{background:var(--red);} .kc5::before{background:var(--purple);}
.sb-kpi-label { font-family:'JetBrains Mono',monospace; font-size:0.52rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.8px; }
.sb-kpi-value { font-size:0.88rem; font-weight:700; color:var(--text-primary); margin-top:2px; }

/* Chip buttons */
.chip-btn button {
  border-radius: 8px !important; font-size: 0.7rem !important;
  padding: 0.38rem 0.65rem !important; width: 100% !important;
  text-align: left !important; transition: all 0.18s !important;
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  color: var(--text-secondary) !important; margin-bottom: 4px !important;
}
.chip-btn button:hover {
  background: rgba(0,212,255,0.06) !important;
  border-color: rgba(0,212,255,0.35) !important;
  color: var(--cyan) !important; transform: translateX(3px);
}

/* ── WELCOME CARD ── */
.welcome-card {
  border-radius: 20px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
  background: linear-gradient(135deg,
    rgba(79,140,255,0.08) 0%, rgba(123,97,255,0.05) 50%, rgba(0,212,255,0.04) 100%);
  border: 1px solid rgba(79,140,255,0.2);
  animation: fadeSlideUp 0.6s ease both;
  position: relative; overflow: hidden;
}
.welcome-card::before {
  content: ''; position: absolute; top: -40px; right: -40px;
  width: 180px; height: 180px; border-radius: 50%;
  background: radial-gradient(circle, rgba(79,140,255,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.wc-row { display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem; }
.wc-pulse {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--green); box-shadow: 0 0 10px var(--green);
  animation: dotPulse 2s infinite; flex-shrink: 0;
}
.wc-title { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); }
.wc-sub { font-size: 0.86rem; color: var(--text-muted); line-height: 1.7; margin-bottom: 1rem; }
.wc-chips { display: flex; flex-wrap: wrap; gap: 7px; }
.wc-chip {
  font-size: 0.72rem; padding: 5px 12px; border-radius: 99px;
  background: rgba(79,140,255,0.1); border: 1px solid rgba(79,140,255,0.2);
  color: var(--blue); font-weight: 500;
}

/* ── ACTIVE MODE BANNER ── */
.mode-banner {
  display: flex; align-items: center; gap: 10px; padding: 0.6rem 1rem;
  border-radius: 12px; margin-bottom: 0.8rem; border: 1px solid;
  animation: fadeSlideUp 0.4s ease both;
}
.mb-icon { font-size: 1.2rem; }
.mb-info {}
.mb-name { font-size: 0.78rem; font-weight: 800; }
.mb-desc { font-size: 0.68rem; margin-top: 1px; opacity: 0.75; }

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.025) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 16px !important;
  padding: 0.3rem 0.6rem !important;
  margin-bottom: 0.7rem !important;
  animation: fadeSlideUp 0.35s ease both;
}
[data-testid="stChatMessageAvatarAssistant"] {
  background: linear-gradient(135deg, rgba(79,140,255,0.25), rgba(123,97,255,0.2)) !important;
}
[data-testid="stChatMessageAvatarUser"] {
  background: rgba(255,209,102,0.15) !important;
}

/* ARIA HTML tables inside chat */
.aria-table { width:100%; border-collapse:collapse; margin:0.5rem 0; font-size:0.82rem; }
.aria-table th {
  background: rgba(79,140,255,0.12); color: var(--cyan);
  font-family: 'JetBrains Mono', monospace; font-size: 0.58rem;
  text-transform: uppercase; letter-spacing: 0.8px;
  padding: 0.45rem 0.8rem; text-align: left;
  border: 1px solid rgba(255,255,255,0.07);
}
.aria-table td { padding:0.36rem 0.8rem; border:1px solid rgba(255,255,255,0.04); color:var(--text-secondary); }
.aria-table tr:nth-child(even) td { background: rgba(255,255,255,0.015); }
.aria-table tr.top-row td { color: var(--green); font-weight: 600; }
.aria-table tr.alert-row td { color: var(--red); }
.aria-table tr.warn-row td { color: var(--gold); }

.report-body {
  font-size: 0.84rem; line-height: 1.85; color: var(--text-secondary);
}
.report-body strong { color: var(--text-primary); }
.report-body br { display: block; margin: 0.2rem 0; }

/* ── TYPING INDICATOR ── */
.typing-wrap { display:flex; align-items:center; gap:6px; padding:0.4rem 0; }
.typing-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--blue);
  animation: typingBounce 1.2s ease infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; background: var(--purple); }
.typing-dot:nth-child(3) { animation-delay: 0.3s; background: var(--cyan); }
.typing-label { font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:var(--text-muted); }

/* ── REPORT EXPANDER ── */
details {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 12px !important;
  margin-bottom: 0.5rem !important;
  overflow: hidden !important;
}
details summary {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.68rem !important; color: var(--cyan) !important;
  padding: 0.5rem 0.8rem !important; cursor: pointer !important;
  transition: background 0.2s !important;
}
details summary:hover { background: rgba(0,212,255,0.05) !important; }
details[open] summary { border-bottom: 1px solid var(--glass-border) !important; }

/* Report outer card */
.report-card {
  border-radius: 18px; border: 1px solid rgba(255,209,102,0.15);
  background: linear-gradient(135deg, rgba(6,9,26,0.9), rgba(10,14,35,0.8));
  padding: 1.4rem 1.6rem; margin-top: 0.8rem;
}
.report-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1rem; padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--glass-border);
}
.rh-title { font-size: 0.95rem; font-weight: 800; color: var(--text-primary); }
.rh-meta { font-family:'JetBrains Mono',monospace; font-size:0.58rem; color:var(--text-muted); }

/* Progress steps */
.prog-steps { display:flex; flex-direction:column; gap:0.4rem; margin:0.7rem 0; }
.prog-step { display:flex; align-items:center; gap:8px; font-family:'JetBrains Mono',monospace; font-size:0.64rem; }
.ps-icon { width:18px; height:18px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.55rem; flex-shrink:0; }
.ps-done { background:rgba(0,255,198,0.15); color:var(--green); }
.ps-active { background:rgba(79,140,255,0.2); color:var(--blue); animation:glowPulse 1s infinite; }
.ps-pending { background:rgba(255,255,255,0.05); color:var(--text-muted); }
.ps-label-done { color:var(--green); } .ps-label-active { color:var(--blue); } .ps-label-pending { color:var(--text-muted); }

/* ── CHAT INPUT ── */
.stChatInput > div {
  background: rgba(6,9,26,0.8) !important;
  border: 1px solid rgba(79,140,255,0.2) !important;
  border-radius: 16px !important;
  backdrop-filter: blur(20px) !important;
}
.stChatInput > div:focus-within {
  border-color: rgba(79,140,255,0.5) !important;
  box-shadow: 0 0 28px rgba(79,140,255,0.12) !important;
}

/* ── GLOBAL BUTTON OVERRIDES ── */
.stButton button {
  font-family: 'Manrope', sans-serif !important;
  transition: all 0.2s ease !important;
}
.stDownloadButton button {
  background: linear-gradient(135deg, var(--green), var(--cyan)) !important;
  border: none !important; color: #02030A !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 18px rgba(0,255,198,0.2) !important;
  border-radius: 12px !important; font-size: 0.82rem !important;
}
.stDownloadButton button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(0,255,198,0.35) !important;
}

/* Primary action button */
.primary-btn button {
  background: linear-gradient(135deg, var(--blue), var(--purple)) !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 4px 18px rgba(79,140,255,0.28) !important;
  border-radius: 12px !important; font-weight: 700 !important;
  font-size: 0.82rem !important;
}
.primary-btn button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(79,140,255,0.45) !important;
}

/* Nav buttons */
.nav-btn button {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid var(--glass-border) !important;
  color: var(--text-muted) !important;
  border-radius: 10px !important; font-size: 0.76rem !important;
  margin-bottom: 4px !important;
}
.nav-btn button:hover {
  background: rgba(79,140,255,0.08) !important;
  border-color: rgba(79,140,255,0.3) !important;
  color: var(--blue) !important;
}

/* Divider */
.aria-divider {
  height: 1px; background: linear-gradient(90deg, transparent, rgba(79,140,255,0.2), transparent);
  margin: 0.8rem 0;
}

/* Confidence meter */
.conf-bar-wrap { display:flex; align-items:center; gap:8px; margin-top:6px; }
.conf-bar-track { flex:1; height:4px; background:rgba(255,255,255,0.06); border-radius:99px; overflow:hidden; }
.conf-bar-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--blue),var(--cyan)); }
.conf-label { font-family:'JetBrains Mono',monospace; font-size:0.56rem; color:var(--text-muted); white-space:nowrap; }

/* Insight badge */
.insight-badge {
  display:inline-flex; align-items:center; gap:4px;
  font-family:'JetBrains Mono',monospace; font-size:0.56rem; font-weight:600;
  padding:2px 8px; border-radius:99px; margin-right:4px; margin-bottom:4px;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# GUARD — no dataset loaded
# ═══════════════════════════════════════════════════════════════════
if "df" not in st.session_state:
    st.markdown("""
    <div style="text-align:center;padding:3rem;animation:fadeSlideUp 0.5s ease both;">
      <div style="font-size:3rem;margin-bottom:1rem;">◆</div>
      <div style="font-size:1.2rem;font-weight:800;color:#F4F7FC;margin-bottom:0.5rem;">ARIA needs data to work</div>
      <div style="font-size:0.86rem;color:#6B7694;margin-bottom:1.5rem;">Upload your Excel sales file to unlock the full AI intelligence dashboard.</div>
    </div>
    """, unsafe_allow_html=True)
    col_c = st.columns([1, 2, 1])[1]
    with col_c:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("← Upload Dataset", use_container_width=True):
            st.switch_page("app.py")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

df       = st.session_state["df"]
filename = st.session_state.get("filename", "dataset.xlsx")

# ═══════════════════════════════════════════════════════════════════
# CACHED COMPUTATIONS
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def compute_stats(_df_id):
    totals     = get_salesperson_totals(df)
    daily      = get_daily_totals(df)
    cat_totals = get_category_totals(df)
    zero_list  = get_zero_sales(df)
    summary    = get_data_summary_for_ai(df)
    return totals, daily, cat_totals, zero_list, summary

df_id = f"{df.shape}_{list(df.columns)}"
totals, daily, cat_totals, zero_list, data_summary = compute_stats(df_id)

total_rev      = float(totals["Total"].sum())       if not totals.empty     else 0.0
mtd            = get_mtd_total(df)
ytd            = get_ytd_total(df)
top_seller     = totals.iloc[0]["Salesperson"]      if not totals.empty     else "—"
top_val        = float(totals.iloc[0]["Total"])     if not totals.empty     else 0.0
avg_daily      = float(daily.mean())                if len(daily) > 0       else 0.0
active_sellers = int((totals["Total"] > 0).sum())   if not totals.empty     else 0

mtd_display = f"₹{mtd:,.0f}" if mtd > 0 else "N/A"
mtd_for_ai  = f"₹{mtd:,.0f}" if mtd > 0 else "Not available — dataset is historical"

never_sold, bad_day = [], []
for s in zero_list:
    if not totals.empty:
        row = totals[totals["Salesperson"] == s]
        if not row.empty and float(row.iloc[0]["Total"]) == 0:
            never_sold.append(s)
        else:
            bad_day.append(s)

rev_per_seller   = (total_rev / active_sellers) if active_sellers > 0 else 0
top_multiplier   = (top_val / rev_per_seller)   if rev_per_seller > 0 else 0
zero_rate        = (len(never_sold) / active_sellers * 100) if active_sellers > 0 else 0

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
DEFAULTS = {
    "chat_history":   [],
    "bi_mode":        "Analyst",
    "bi_report_txt":  None,
    "_pending_ai":    False,
    "_pending_q":     None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

current_mode = st.session_state["bi_mode"]
msg_count    = sum(1 for m in st.session_state["chat_history"] if m["role"] == "user")

# ═══════════════════════════════════════════════════════════════════
# MODE METADATA
# ═══════════════════════════════════════════════════════════════════
MODE_META = {
    "Analyst": {
        "icon": "📊", "color": "#4F8CFF", "bg": "rgba(79,140,255,0.08)",
        "border": "rgba(79,140,255,0.25)",
        "desc": "Deep breakdowns · trend analysis · root causes · every number",
        "badge_txt": "DEEP ANALYSIS",
    },
    "Executive": {
        "icon": "🧑‍💼", "color": "#FFD166", "bg": "rgba(255,209,102,0.08)",
        "border": "rgba(255,209,102,0.25)",
        "desc": "5-bullet briefs · one priority · under 80 words · boardroom-ready",
        "badge_txt": "EXEC BRIEF",
    },
    "Investor": {
        "icon": "📈", "color": "#00FFC6", "bg": "rgba(0,255,198,0.08)",
        "border": "rgba(0,255,198,0.25)",
        "desc": "Growth % · ROI trajectory · concentration risk · scaling potential",
        "badge_txt": "GROWTH FOCUS",
    },
    "Operational": {
        "icon": "⚙️", "color": "#FF6B6B", "bg": "rgba(255,107,107,0.08)",
        "border": "rgba(255,107,107,0.25)",
        "desc": "Named actions · zero-alerts first · specific people · today's priority",
        "badge_txt": "FIELD OPS",
    },
}
m = MODE_META[current_mode]

# ═══════════════════════════════════════════════════════════════════
# AI MODE INSTRUCTIONS (injected into system prompt)
# ═══════════════════════════════════════════════════════════════════
MODE_INSTRUCTIONS = {
    "Analyst": """
ANALYST MODE — DEEP DATA ANALYST
You are a senior data analyst. Precise, thorough, pattern-focused.
RULES:
① Complete breakdowns — never truncate data
② Every number has context (vs avg, vs prior period)
③ HTML tables for any data > 2 rows or 2 columns (class="aria-table")
④ Always include TREND OBSERVATION and ROOT CAUSE NOTES
⑤ Match length to complexity: fact→2-4 lines, comparison→table+insights, analysis→full sections
⑥ Highlight outliers explicitly — name the person, category, day
⑦ Never round unless asked
⑧ Use: MoM, YoY, variance, delta, trailing average
""",
    "Executive": """
EXECUTIVE MODE — CEO BRIEFING ADVISOR
You brief a time-constrained CEO. Every word must earn its place.
RULES:
① HARD LIMIT: under 80 words total — no exceptions
② Lead with the single most important number — always first line
③ Maximum 5 bullet points — never more
④ ONE recommendation only — highest priority action
⑤ No tables (CEO sees those elsewhere)
⑥ No hedging language — be definitive
⑦ Format: bullets + "▶ ACTION: [directive]"
⑧ Active voice only. Never passive.
""",
    "Investor": """
INVESTOR MODE — GROWTH REVENUE ANALYST
You advise an investor or board member. Think in % and multiples.
RULES:
① Always open with revenue growth % and trajectory (accelerating/decelerating)
② Flag top 1-2 categories with highest scaling potential and WHY
③ Include ratios: top seller vs average, category concentration, active seller %
④ Every insight connects to: revenue upside OR business risk
⑤ Flag concentration risks (>40% dependency)
⑥ Use HTML tables for ratio comparisons (class="aria-table")
⑦ Frame recommendations in: resource allocation, growth levers, risk mitigation
""",
    "Operational": """
OPERATIONAL MODE — FIELD OPERATIONS MANAGER
No-nonsense. Morning standup in 10 minutes. You know every person by name.
RULES:
① NAME SPECIFIC PEOPLE in every answer — never "a salesperson" — always "BINOY", "RAHUL" etc
② Every response has NAMED ACTION ITEMS: → [ACTION VERB] [PERSON] — [specific reason]
③ ZERO-SALES ALERTS always first — highest priority
④ Numbered action list — no paragraphs
⑤ Zero strategic commentary — only field operations
⑥ Use: URGENT, IMMEDIATE, TODAY, FOLLOW UP NOW
⑦ End with TODAY'S PRIORITY LIST (max 5 items, ranked by urgency)
""",
}

# ═══════════════════════════════════════════════════════════════════
# MASTER SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════
BI_SYSTEM_PROMPT = f"""
ARIA — AI SALES INTELLIGENCE COPILOT
Homeopathic Pharmaceutical Company · Internal BI Platform

IDENTITY: You are ARIA, a purpose-built analytical engine for sales intelligence.
Not a general assistant. Designed for evidence-based business decisions.

ACTIVE MODE: {current_mode.upper()}
{MODE_INSTRUCTIONS.get(current_mode, "")}

QUERY CLASSIFICATION (classify silently, apply rules, never write the type):
TYPE A — Greeting/small talk → 1-2 friendly sentences, no data
TYPE B — Single fact → 1-3 lines, exact fact + one line context
TYPE C — Comparison/list → HTML table first, then 1-2 insights below
TYPE D — Full analysis → structured sections, mode output format

FORMATTING:
- Currency: ₹ Indian format (₹3,47,594 not ₹347,594)
- HTML tables: <table class="aria-table">...</table>
- Row classes: top-row (green), alert-row (red), warn-row (gold)
- Section headers: <strong>── SECTION ──</strong>

NEVER:
✗ Fabricate numbers
✗ End with "Let me know if...", "Hope this helps!", "Feel free to ask!"
✗ Say "As an AI...", "Great question!", repeat the question
✗ Exceed 80 words in Executive Mode
✗ Make up data — say clearly if data is unavailable
✗ Use passive voice when active is possible

ALWAYS:
✓ Start immediately with the answer
✓ Name people, categories, exact values
✓ Contextualize every number
✓ Apply active MODE rules strictly

INTELLIGENCE RULES:
- Underperforming: >20% below team average
- Top performer: >30% above team average
- Never Sold = ₹0 entire period → CRITICAL
- Had Bad Day = ₹0 on one day but non-zero overall → MONITOR

LIVE DATA:
Dataset: {filename}
{data_summary}

KEY METRICS:
Total Revenue     : ₹{total_rev:,.0f}
MTD Revenue       : {mtd_for_ai}
YTD Revenue       : ₹{ytd:,.0f}
Daily Average     : ₹{avg_daily:,.0f}
Top Seller        : {top_seller} (₹{top_val:,.0f})
Active Sellers    : {active_sellers}
Rev / Seller      : ₹{rev_per_seller:,.0f}
Top Multiplier    : {top_multiplier:.2f}× average
Zero-Sale Rate    : {zero_rate:.1f}%

ALERTS:
Never Sold (₹0 total) : {', '.join(never_sold) if never_sold else 'None'}
Had Bad Day (₹0 day)  : {', '.join(bad_day) if bad_day else 'None'}
"""

# ═══════════════════════════════════════════════════════════════════
# TOPBAR
# ═══════════════════════════════════════════════════════════════════
alert_count = len(never_sold) + len(bad_day)
st.markdown(f"""
<div class="topbar">
  <div class="tb-left">
    <div class="tb-logo">A</div>
    <span class="tb-title">ARIA</span>
    <span class="tb-badge" style="background:{m['bg']};border-color:{m['border']};color:{m['color']};">
      {m['icon']} {m['badge_txt']}
    </span>
  </div>
  <div class="tb-right">
    <span class="tb-stat">💬 {msg_count} messages</span>
    <span class="tb-stat">{'🚨 ' + str(alert_count) + ' alerts' if alert_count else '✅ No alerts'}</span>
    <span class="tb-live"><span class="tb-dot"></span>Groq · LLaMA 3.3</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Mode Switcher ──
    st.markdown('<div class="sb-label">Analysis Mode</div>', unsafe_allow_html=True)
    for mname, meta in MODE_META.items():
        is_active = (current_mode == mname)
        btn_class = "mode-btn mode-btn-on" if is_active else "mode-btn mode-btn-off"
        btn_label = f"{meta['icon']}  {mname}{'  ←' if is_active else ''}"
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button(btn_label, key=f"mode_{mname}", use_container_width=True):
            if not is_active:
                st.session_state["bi_mode"] = mname
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Show active mode description
    st.markdown(f"""
    <div class="mode-desc" style="color:{m['color']};border-left-color:{m['color']};">
      {m['desc']}
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Questions ──
    st.markdown('<div class="sb-label">Quick Questions</div>', unsafe_allow_html=True)
    quick_qs = [
        "📊 Total revenue breakdown?",
        "🏆 Who is the top performer?",
        "🚨 Which sellers had zero sales?",
        "📋 Compare top 5 sellers",
        "🗂️ Show category breakdown",
        "📈 What are the growth trends?",
        "⚠️ Business alerts summary",
        "💡 Key growth opportunities?",
    ]
    st.markdown('<div class="chip-btn">', unsafe_allow_html=True)
    for i, q in enumerate(quick_qs):
        if st.button(q, key=f"qchip_{i}", use_container_width=True):
            clean_q = re.sub(r'^[^\w]+\s*', '', q)
            st.session_state["chat_history"].append({
                "role": "user", "content": clean_q,
                "ts": datetime.datetime.now().strftime("%I:%M %p"),
            })
            st.session_state["_pending_ai"] = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Live KPIs ──
    st.markdown('<div class="sb-label">Live KPIs</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sb-kpi kc1">
      <div class="sb-kpi-label">Total Revenue</div>
      <div class="sb-kpi-value">₹{total_rev:,.0f}</div>
    </div>
    <div class="sb-kpi kc2">
      <div class="sb-kpi-label">MTD Revenue</div>
      <div class="sb-kpi-value">{mtd_display}</div>
    </div>
    <div class="sb-kpi kc3">
      <div class="sb-kpi-label">Top Seller</div>
      <div class="sb-kpi-value" style="font-size:0.78rem;">{top_seller} · ₹{top_val:,.0f}</div>
    </div>
    <div class="sb-kpi kc4">
      <div class="sb-kpi-label">Zero-Sale Alerts</div>
      <div class="sb-kpi-value" style="color:{'#FF6B6B' if zero_list else '#00FFC6'};">
        {len(never_sold)} never sold · {len(bad_day)} bad day
      </div>
    </div>
    <div class="sb-kpi kc5">
      <div class="sb-kpi-label">Active Sellers</div>
      <div class="sb-kpi-value" style="color:#7B61FF;">{active_sellers}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation ──
    st.markdown('<div class="sb-label">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("📊  Dashboard", use_container_width=True, key="nav_dash"):
        st.switch_page("pages/1_Dashboard.py")
    if st.button("📤  New Upload", use_container_width=True, key="nav_upload"):
        st.switch_page("app.py")
    if st.button("🗑️  Clear Chat", use_container_width=True, key="nav_clear"):
        st.session_state["chat_history"] = []
        st.session_state["bi_report_txt"] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # File info
    st.markdown(f"""
    <div style="margin-top:0.8rem;padding:0.5rem 0.7rem;background:rgba(255,255,255,0.02);
    border:1px solid var(--glass-border);border-radius:8px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.52rem;color:#6B7694;text-transform:uppercase;letter-spacing:0.8px;">Active File</div>
      <div style="font-size:0.72rem;color:#AEB9D4;margin-top:2px;word-break:break-all;">{filename}</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ACTIVE MODE BANNER (visible in main area — so user always sees mode)
# ═══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="mode-banner" style="background:{m['bg']};border-color:{m['border']};">
  <div class="mb-icon">{m['icon']}</div>
  <div class="mb-info">
    <div class="mb-name" style="color:{m['color']};">{mname} Mode Active</div>
    <div class="mb-desc" style="color:{m['color']};">{m['desc']}</div>
  </div>
</div>
""".replace("mname", current_mode), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# WELCOME CARD (first load only)
# ═══════════════════════════════════════════════════════════════════
if not st.session_state["chat_history"]:
    st.markdown(f"""
    <div class="welcome-card">
      <div class="wc-row">
        <div class="wc-pulse"></div>
        <div class="wc-title">ARIA — Sales Intelligence Copilot</div>
      </div>
      <div class="wc-sub">
        Analysing <strong style="color:#F4F7FC;">{filename}</strong> in real time.
        Switch modes in the sidebar for different analysis styles.
        Quick questions are always visible — no scrolling needed.
      </div>
      <div class="wc-chips">
        <span class="wc-chip">📊 {active_sellers} Active Sellers</span>
        <span class="wc-chip">💰 ₹{total_rev:,.0f} Total Revenue</span>
        <span class="wc-chip">🏆 {top_seller} leads</span>
        {'<span class="wc-chip" style="background:rgba(255,107,107,0.12);border-color:rgba(255,107,107,0.25);color:#FF6B6B;">🚨 ' + str(alert_count) + ' Alerts</span>' if alert_count else '<span class="wc-chip" style="background:rgba(0,255,198,0.1);border-color:rgba(0,255,198,0.2);color:#00FFC6;">✅ All Clear</span>'}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# AI RESPONSE HELPER
# ═══════════════════════════════════════════════════════════════════
def get_ai_response(user_text: str) -> str:
    groq_hist = []
    for msg_h in st.session_state["chat_history"][-10:]:
        content = msg_h["content"]
        if msg_h.get("is_report") and len(content) > 300:
            content = content[:300] + "… [truncated for context]"
        groq_hist.append({"role": msg_h["role"], "content": content})
    try:
        return ask_groq(user_text, BI_SYSTEM_PROMPT, chat_history=groq_hist)
    except Exception as e:
        return (
            f'<div style="color:#FF6B6B;font-family:JetBrains Mono,monospace;font-size:0.78rem;">'
            f'⚠️ ARIA error: {str(e)[:200]}<br>'
            f'<span style="color:#6B7694;font-size:0.68rem;">Check your Groq API key and try again.</span></div>'
        )

def render_aria(content: str):
    st.markdown(f'<div class="report-body">{content}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# CHAT HISTORY RENDER
# ═══════════════════════════════════════════════════════════════════
for msg_h in st.session_state["chat_history"]:
    if msg_h.get("is_report"):
        continue
    with st.chat_message(msg_h["role"], avatar="◆" if msg_h["role"] == "assistant" else "👤"):
        if msg_h["role"] == "assistant":
            render_aria(msg_h["content"])
        else:
            st.write(msg_h["content"])
        if msg_h.get("ts"):
            st.caption(msg_h["ts"])

# ═══════════════════════════════════════════════════════════════════
# PENDING AI (from sidebar quick question) — fires before chat_input
# ═══════════════════════════════════════════════════════════════════
if st.session_state["_pending_ai"]:
    st.session_state["_pending_ai"] = False
    last_q = st.session_state["chat_history"][-1]["content"]

    # Show the user message immediately
    with st.chat_message("user", avatar="👤"):
        st.write(last_q)
        st.caption(st.session_state["chat_history"][-1].get("ts", ""))

    # ARIA typing + response
    with st.chat_message("assistant", avatar="◆"):
        st.markdown(f"""
        <div class="typing-wrap">
          <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
          <span class="typing-label">ARIA thinking in {current_mode} mode…</span>
        </div>
        """, unsafe_allow_html=True)
        response = get_ai_response(last_q)
        st.empty()
        render_aria(response)
        now_ts = datetime.datetime.now().strftime("%I:%M %p")
        st.caption(now_ts)

    st.session_state["chat_history"].append({
        "role": "assistant", "content": response,
        "ts": now_ts,
    })

# ═══════════════════════════════════════════════════════════════════
# CHAT INPUT
# ═══════════════════════════════════════════════════════════════════
user_input = st.chat_input(f"Ask ARIA in {current_mode} mode… ({m['badge_txt']})")

if user_input:
    now_ts = datetime.datetime.now().strftime("%I:%M %p")
    st.session_state["chat_history"].append({
        "role": "user", "content": user_input, "ts": now_ts,
    })
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)
        st.caption(now_ts)

    with st.chat_message("assistant", avatar="◆"):
        with st.spinner(f"ARIA thinking in {current_mode} mode…"):
            response = get_ai_response(user_input)
        render_aria(response)
        st.caption(now_ts)

    st.session_state["chat_history"].append({
        "role": "assistant", "content": response, "ts": now_ts,
    })
    st.rerun()

# ═══════════════════════════════════════════════════════════════════
# REPORT & PDF — in expander (isolated, can't disturb chat)
# ═══════════════════════════════════════════════════════════════════
st.markdown('<div class="aria-divider"></div>', unsafe_allow_html=True)

with st.expander(f"◈ Intelligence Report & PDF Export  [{current_mode} Mode]", expanded=False):

    st.markdown(f"""
    <div style="font-size:0.78rem;color:#6B7694;margin-bottom:0.8rem;line-height:1.6;">
      Generate a full structured BI report in <strong style="color:{m['color']};">{current_mode} Mode</strong>.
      Then export it as a professionally styled PDF with charts, tables, and AI insights.
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        gen_report = st.button("🚀 Generate BI Report", use_container_width=True, key="gen_rpt")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        dl_pdf = st.button("📄 Build & Download PDF", use_container_width=True, key="dl_pdf_btn")
    with c3:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_rpt"):
            st.session_state["bi_report_txt"] = None
            st.rerun()

    REPORT_STEPS = [
        ("🔍", "Analysing salesperson data…"),
        ("📊", "Computing category performance…"),
        ("📈", "Running trend analysis…"),
        ("🧠", "Generating AI insights…"),
        ("💡", "Building recommendations…"),
        ("✅", "Finalising report…"),
    ]
    PDF_STEPS = [
        ("🎨", "Building cover page…"),
        ("📋", "Compiling KPI tables…"),
        ("📊", "Rendering charts…"),
        ("🧠", "Embedding AI report…"),
        ("📄", "Exporting PDF…"),
    ]

    def render_steps(steps: list, done_count: int):
        rows = ""
        for i, (icon, label) in enumerate(steps):
            if i < done_count:
                cls = "ps-done"; lc = "ps-label-done"; ic = "ps-done"
                disp_icon = "✓"
            elif i == done_count:
                cls = "ps-active"; lc = "ps-label-active"; ic = "ps-active"
                disp_icon = icon
            else:
                cls = "ps-pending"; lc = "ps-label-pending"; ic = "ps-pending"
                disp_icon = icon
            rows += f'<div class="prog-step"><div class="ps-icon {ic}">{disp_icon}</div><span class="{lc}">{label}</span></div>'
        return f'<div class="prog-steps">{rows}</div>'

    # ── GENERATE REPORT ──
    if gen_report:
        MODE_REPORT_RULES = {
            "Analyst":     "Full detail. All 10 sections. HTML tables for every dataset. Name every person and category.",
            "Executive":   "Sections 1 (3 bullets), 2 (table), 9 (3 recs), 10 (5 actions). Nothing else. Under 200 words total.",
            "Investor":    "Focus on growth%, ROI, scaling. All ratios in tables. Revenue trajectory mandatory.",
            "Operational": "Section 6 (zero-alerts with names) first. Section 10 (named actions) second. Section 3 (daily snapshot) third. No strategy.",
        }
        report_prompt = f"""
{MODE_REPORT_RULES.get(current_mode, '')}

Generate a Business Intelligence Report for this homeopathic pharmaceutical company.
Date: {datetime.date.today().strftime('%d %B %Y')}
All currency in ₹ Indian format.
Use <table class="aria-table"> for all tabular data.
Row classes: top-row (best), alert-row (zero/critical), warn-row (low/warning).
Section headers: <strong>── N. SECTION NAME ──</strong>

Sections (apply mode filter above):
1. EXECUTIVE SUMMARY
2. KPI SCORECARD
3. SALESPERSON PERFORMANCE
4. CATEGORY ANALYSIS
5. DAILY TREND ANALYSIS
6. ZERO-SALES & ALERTS
7. AI INSIGHT ENGINE
8. GROWTH OPPORTUNITIES
9. STRATEGIC RECOMMENDATIONS
10. NEXT BEST ACTIONS
"""
        prog_ph = st.empty()
        for si in range(len(REPORT_STEPS)):
            prog_ph.markdown(render_steps(REPORT_STEPS, si), unsafe_allow_html=True)
            time.sleep(0.3)

        try:
            report_text = ask_groq(report_prompt, BI_SYSTEM_PROMPT, chat_history=[])
        except Exception as e:
            report_text = f'<span style="color:#FF6B6B;">⚠️ Report failed: {str(e)[:200]}</span>'

        prog_ph.markdown(render_steps(REPORT_STEPS, len(REPORT_STEPS)), unsafe_allow_html=True)
        time.sleep(0.4)
        prog_ph.empty()

        st.session_state["bi_report_txt"] = report_text
        st.rerun()

    # ── DISPLAY REPORT ──
    if st.session_state.get("bi_report_txt"):
        report_raw = st.session_state["bi_report_txt"]

        st.markdown(f"""
        <div class="report-card">
          <div class="report-header">
            <div class="rh-title">◆ ARIA Intelligence Report</div>
            <div class="rh-meta">{m['icon']} {current_mode} Mode · {datetime.date.today().strftime('%d %B %Y')}</div>
          </div>
        """, unsafe_allow_html=True)

        # Split into sections by numbered headers
        section_re = re.compile(r'(<strong>──\s*\d+\..*?──</strong>)', re.DOTALL)
        parts = section_re.split(report_raw)

        if len(parts) > 1:
            intro = parts[0].strip()
            if intro:
                st.markdown(f'<div class="report-body">{intro}</div>', unsafe_allow_html=True)
            i = 1
            while i < len(parts):
                header = parts[i].strip()
                content = parts[i + 1].strip() if (i + 1) < len(parts) else ""
                # Extract clean title for expander
                clean_title = re.sub(r'<[^>]+>', '', header).strip().lstrip('─').strip()
                with st.expander(f"▸ {clean_title}", expanded=False):
                    st.markdown(f'<div class="report-body">{content}</div>', unsafe_allow_html=True)
                i += 2
        else:
            # Fallback: plain render
            st.markdown(f'<div class="report-body">{report_raw}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── PDF BUILDER ──
    def build_pdf(report_txt: str, mode: str, fname: str):
        """
        Build a full PDF report with cover, KPI table, leaderboard,
        category table, charts, zero-alert table, and AI text.
        Returns (pdf_bytes, warning_string_or_None).
        """
        import io
        warnings_list = []

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mticker
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                Image as RLImage, HRFlowable, PageBreak,
            )
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError as ie:
            return None, f"Missing library: {ie}. Run: pip install reportlab matplotlib"

        # Font setup
        base_dir  = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "..", "assets", "fonts", "DejaVuSans.ttf")
        font_bold = os.path.join(base_dir, "..", "assets", "fonts", "DejaVuSans-Bold.ttf")
        USE_DJ = False
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVu", font_path))
                if os.path.exists(font_bold):
                    pdfmetrics.registerFont(TTFont("DejaVuBold", font_bold))
                USE_DJ = True
            except Exception as fe:
                warnings_list.append(f"Font fallback (Helvetica): {fe}")
        F  = "DejaVu" if USE_DJ else "Helvetica"
        FB = "DejaVuBold" if USE_DJ else "Helvetica-Bold"
        INR = "Rs." # safe for all fonts

        # Colors
        C_BG    = colors.HexColor("#02030A")
        C_DARK  = colors.HexColor("#06091A")
        C_PANEL = colors.HexColor("#0A0E23")
        C_BLUE  = colors.HexColor("#4F8CFF")
        C_CYAN  = colors.HexColor("#00D4FF")
        C_GREEN = colors.HexColor("#00FFC6")
        C_GOLD  = colors.HexColor("#FFD166")
        C_RED   = colors.HexColor("#FF6B6B")
        C_PURP  = colors.HexColor("#7B61FF")
        C_MUTED = colors.HexColor("#6B7694")
        C_TEXT  = colors.HexColor("#AEB9D4")
        C_WHITE = colors.HexColor("#F4F7FC")
        GRID    = colors.HexColor("#1A2040")

        def mkS(name, **kw):
            return ParagraphStyle(name, fontName=F, **kw)
        def mkSB(name, **kw):
            return ParagraphStyle(name, fontName=FB, **kw)

        s_h1   = mkSB("h1", fontSize=11, textColor=C_CYAN,  spaceBefore=14, spaceAfter=6)
        s_h2   = mkSB("h2", fontSize=9,  textColor=C_GOLD,  spaceBefore=10, spaceAfter=4)
        s_body = mkS("body", fontSize=8.5, textColor=C_TEXT, leading=13, spaceAfter=3)
        s_sub  = mkS("sub",  fontSize=8,  textColor=C_MUTED, spaceAfter=3)
        s_kv   = mkS("kv",  fontSize=8,  textColor=C_WHITE, spaceAfter=2)

        buf = io.BytesIO()
        try:
            doc = SimpleDocTemplate(
                buf, pagesize=A4,
                leftMargin=1.8*cm, rightMargin=1.8*cm,
                topMargin=1.6*cm, bottomMargin=2.4*cm,
            )
        except Exception as e:
            return None, f"PDF init failed: {e}"

        story = []
        W = A4[0] - 3.6*cm   # usable width

        # ── COVER ──
        try:
            # Gradient header bar
            cover_data = [[Paragraph(
                f'<font color="#F4F7FC" size="20"><b>ARIA Intelligence Report</b></font>',
                mkSB("ct", fontSize=20, textColor=C_WHITE, leading=24)
            )]]
            ct = Table(cover_data, colWidths=[W], rowHeights=[3.5*cm])
            ct.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (0,0), C_BLUE),
                ("LEFTPADDING", (0,0), (0,0), 18),
                ("VALIGN", (0,0), (0,0), "MIDDLE"),
                ("ROUNDEDCORNERS", [8]),
            ]))
            story.append(ct)
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph(f"Mode: {mode}", mkSB("cm", fontSize=12, textColor=C_BLUE, spaceAfter=4)))
            story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}", s_sub))
            story.append(Paragraph(f"File: {fname}", s_sub))
            story.append(Spacer(1, 0.3*cm))
            story.append(HRFlowable(width=W, thickness=1.5, color=C_BLUE, spaceAfter=10))
        except Exception as e:
            warnings_list.append(f"Cover skipped: {e}")

        # ── KPI TABLE ──
        try:
            story.append(Paragraph("Key Performance Indicators", s_h1))
            kd = [
                ["Metric", "Value", "Metric", "Value"],
                ["Total Revenue", f"{INR}{total_rev:,.0f}", "Daily Average", f"{INR}{avg_daily:,.0f}"],
                ["YTD Revenue",   f"{INR}{ytd:,.0f}",       "Top Seller",    top_seller],
                ["Active Sellers",str(active_sellers),      "Rev/Seller",    f"{INR}{rev_per_seller:,.0f}"],
                ["Never Sold",    str(len(never_sold)),      "Bad Day",       str(len(bad_day))],
                ["Top Value",     f"{INR}{top_val:,.0f}",   "Multiplier",    f"{top_multiplier:.2f}x avg"],
            ]
            col_w = [W*0.22, W*0.28, W*0.22, W*0.28]
            kt = Table(kd, colWidths=col_w)
            kt.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  C_DARK),
                ("TEXTCOLOR",   (0,0), (-1,0),  C_CYAN),
                ("FONTNAME",    (0,0), (-1,0),  FB),
                ("FONTNAME",    (0,1), (-1,-1), F),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("TEXTCOLOR",   (0,1), (-1,-1), C_WHITE),
                ("TEXTCOLOR",   (1,1), (1,-1),  C_GREEN),
                ("TEXTCOLOR",   (3,1), (3,-1),  C_GOLD),
                ("BACKGROUND",  (0,2), (-1,2),  C_PANEL),
                ("BACKGROUND",  (0,4), (-1,4),  C_PANEL),
                ("GRID",        (0,0), (-1,-1), 0.3, GRID),
                ("TOPPADDING",  (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                ("LEFTPADDING", (0,0), (-1,-1), 7),
            ]))
            story.append(kt)
            story.append(Spacer(1, 0.5*cm))
        except Exception as e:
            warnings_list.append(f"KPI table skipped: {e}")

        # ── LEADERBOARD ──
        try:
            story.append(Paragraph("Salesperson Leaderboard", s_h1))
            if not totals.empty:
                t_sum = totals["Total"].sum()
                lh  = [["Rank", "Salesperson", "Total Sales", "Share %", "vs Avg"]]
                lrows = []
                for idx_i, rw in enumerate(totals.head(20).itertuples()):
                    share = (rw.Total / t_sum * 100) if t_sum else 0
                    vs    = ((rw.Total / rev_per_seller - 1) * 100) if rev_per_seller else 0
                    vs_s  = f"+{vs:.0f}%" if vs >= 0 else f"{vs:.0f}%"
                    lrows.append([f"#{idx_i+1}", rw.Salesperson, f"{INR}{rw.Total:,.0f}", f"{share:.1f}%", vs_s])
                col_w2 = [W*0.09, W*0.36, W*0.24, W*0.16, W*0.15]
                lt = Table(lh + lrows, colWidths=col_w2)
                style_cmds = [
                    ("BACKGROUND",   (0,0), (-1,0),   C_DARK),
                    ("TEXTCOLOR",    (0,0), (-1,0),   C_GOLD),
                    ("FONTNAME",     (0,0), (-1,0),   FB),
                    ("FONTNAME",     (0,1), (-1,-1),  F),
                    ("FONTSIZE",     (0,0), (-1,-1),  8),
                    ("TEXTCOLOR",    (0,1), (-1,-1),  C_WHITE),
                    ("TEXTCOLOR",    (2,1), (2,-1),   C_GREEN),
                    ("GRID",         (0,0), (-1,-1),  0.3, GRID),
                    ("TOPPADDING",   (0,0), (-1,-1),  4),
                    ("BOTTOMPADDING",(0,0), (-1,-1),  4),
                    ("LEFTPADDING",  (0,0), (-1,-1),  6),
                    # Highlight row 1 (top performer)
                    ("BACKGROUND",   (0,1), (-1,1),   colors.HexColor("#071A0A")),
                ]
                lt.setStyle(TableStyle(style_cmds))
                story.append(lt)
            story.append(PageBreak())
        except Exception as e:
            warnings_list.append(f"Leaderboard skipped: {e}")

        # ── CATEGORY TABLE ──
        try:
            story.append(Paragraph("Category Performance", s_h1))
            if not cat_totals.empty:
                c_sum = float(cat_totals["Total"].sum())
                c_max = float(cat_totals["Total"].max())
                ch  = [["Category", "Total Sales", "Share %", "Health"]]
                crows = []
                for rw in cat_totals.itertuples():
                    sh = (rw.Total / c_sum * 100) if c_sum else 0
                    r  = (rw.Total / c_max)       if c_max  else 0
                    ht = "Strong" if r >= 0.6 else ("Moderate" if r >= 0.25 else "Low")
                    crows.append([str(rw.Category), f"{INR}{rw.Total:,.0f}", f"{sh:.1f}%", ht])
                col_w3 = [W*0.32, W*0.28, W*0.18, W*0.22]
                ctt = Table(ch + crows, colWidths=col_w3)
                ctt.setStyle(TableStyle([
                    ("BACKGROUND",   (0,0), (-1,0),  C_DARK),
                    ("TEXTCOLOR",    (0,0), (-1,0),  C_CYAN),
                    ("FONTNAME",     (0,0), (-1,0),  FB),
                    ("FONTNAME",     (0,1), (-1,-1), F),
                    ("FONTSIZE",     (0,0), (-1,-1), 8),
                    ("TEXTCOLOR",    (0,1), (-1,-1), C_WHITE),
                    ("TEXTCOLOR",    (1,1), (1,-1),  C_GREEN),
                    ("GRID",         (0,0), (-1,-1), 0.3, GRID),
                    ("TOPPADDING",   (0,0), (-1,-1), 4),
                    ("BOTTOMPADDING",(0,0), (-1,-1), 4),
                    ("LEFTPADDING",  (0,0), (-1,-1), 6),
                ]))
                story.append(ctt)
            story.append(Spacer(1, 0.5*cm))
        except Exception as e:
            warnings_list.append(f"Category table skipped: {e}")

        # ── HELPER: fig → bytes ──
        def fig_to_img(fig):
            ib = io.BytesIO()
            fig.savefig(ib, format="png", bbox_inches="tight", dpi=150, facecolor="#02030A")
            ib.seek(0)
            plt.close(fig)
            return ib

        CHART_BG  = "#02030A"
        PANEL_BG  = "#06091A"
        TICK_COL  = "#6B7694"
        GRID_COL  = "#1A2040"

        # ── DAILY TREND CHART ──
        try:
            story.append(Paragraph("Daily Sales Trend", s_h1))
            if len(daily) > 0:
                fig, ax = plt.subplots(figsize=(13, 3.8), facecolor=CHART_BG)
                ax.set_facecolor(PANEL_BG)
                xs = list(range(len(daily)))
                ys = list(daily.values)
                ax.fill_between(xs, ys, alpha=0.12, color="#4F8CFF")
                ax.plot(xs, ys, color="#00D4FF", linewidth=2.2, zorder=4)
                ax.scatter(xs, ys, color="#4F8CFF", s=22, zorder=5)
                if len(daily) >= 7:
                    ma7 = daily.rolling(7).mean()
                    ax.plot(xs, ma7, color="#FFD166", linewidth=1.5, linestyle="--", label="7-Day MA", zorder=3)
                    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL, labelcolor="#AEB9D4", fontsize=8)
                ax.tick_params(colors=TICK_COL, labelsize=7)
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                    lambda v, _: f"{v/1e3:.0f}K" if v >= 1000 else str(int(v))
                ))
                for sp in ax.spines.values():
                    sp.set_color(GRID_COL)
                ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.7)
                ax.set_xlabel("Day", color=TICK_COL, fontsize=7)
                ax.set_ylabel("Revenue", color=TICK_COL, fontsize=7)
                story.append(RLImage(fig_to_img(fig), width=W, height=4.5*cm))
            story.append(Spacer(1, 0.4*cm))
        except Exception as e:
            warnings_list.append(f"Daily trend chart skipped: {e}")

        # ── CATEGORY BAR CHART ──
        try:
            story.append(Paragraph("Category Revenue Breakdown", s_h1))
            if not cat_totals.empty:
                cats = cat_totals["Category"].astype(str).tolist()
                vals = [float(v) for v in cat_totals["Total"].tolist()]
                PAL  = ["#4F8CFF","#7B61FF","#00D4FF","#00FFC6","#FFD166","#FF6B6B","#A78BFA","#34D399"]
                fig2, ax2 = plt.subplots(figsize=(12, max(3, len(cats)*0.55)), facecolor=CHART_BG)
                ax2.set_facecolor(PANEL_BG)
                bar_colors = [PAL[i % len(PAL)] for i in range(len(cats))]
                bars = ax2.barh(cats, vals, color=bar_colors, alpha=0.85, edgecolor="none", height=0.6)
                for bar, val in zip(bars, vals):
                    ax2.text(
                        bar.get_width() * 1.012, bar.get_y() + bar.get_height()/2,
                        f"{INR}{val/1e3:.1f}K", va="center", color="#AEB9D4", fontsize=7.5
                    )
                ax2.tick_params(colors=TICK_COL, labelsize=7)
                for sp in ax2.spines.values():
                    sp.set_color(GRID_COL)
                ax2.xaxis.set_major_formatter(mticker.FuncFormatter(
                    lambda v, _: f"{v/1e3:.0f}K"
                ))
                ax2.grid(axis="x", color=GRID_COL, linewidth=0.5, alpha=0.7)
                story.append(RLImage(fig_to_img(fig2), width=W, height=max(4*cm, len(cats)*0.7*cm)))
            story.append(PageBreak())
        except Exception as e:
            warnings_list.append(f"Category chart skipped: {e}")

        # ── ZERO-SALES ALERTS TABLE ──
        try:
            story.append(Paragraph("Zero-Sales Alerts", s_h1))
            a_data = (
                [["Salesperson", "Alert Type", "Status", "Action Required"]]
                + [[n, "Never Sold", "CRITICAL", "Immediate management review"] for n in never_sold]
                + [[n, "Had Bad Day", "MONITOR",  "Follow up this week"]         for n in bad_day]
            )
            if len(a_data) > 1:
                col_w4 = [W*0.28, W*0.20, W*0.16, W*0.36]
                zt = Table(a_data, colWidths=col_w4)
                zt.setStyle(TableStyle([
                    ("BACKGROUND",   (0,0), (-1,0),  C_DARK),
                    ("TEXTCOLOR",    (0,0), (-1,0),  C_RED),
                    ("FONTNAME",     (0,0), (-1,0),  FB),
                    ("FONTNAME",     (0,1), (-1,-1), F),
                    ("FONTSIZE",     (0,0), (-1,-1), 8),
                    ("TEXTCOLOR",    (0,1), (-1,-1), C_WHITE),
                    ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#2A1020")),
                    ("TOPPADDING",   (0,0), (-1,-1), 4),
                    ("BOTTOMPADDING",(0,0), (-1,-1), 4),
                    ("LEFTPADDING",  (0,0), (-1,-1), 6),
                ]))
                story.append(zt)
            else:
                story.append(Paragraph("No zero-sales alerts. All sellers have recorded sales.", s_body))
            story.append(Spacer(1, 0.6*cm))
            story.append(HRFlowable(width=W, thickness=1, color=C_BLUE, spaceAfter=10))
        except Exception as e:
            warnings_list.append(f"Zero-alerts table skipped: {e}")

        # ── AI REPORT TEXT ──
        try:
            story.append(Paragraph("AI Intelligence Analysis", s_h1))
            story.append(Paragraph(f"Generated in {mode} Mode by ARIA", s_sub))
            story.append(Spacer(1, 0.25*cm))
            # Strip HTML tags for PDF text
            clean = re.sub(r'<[^>]+>', ' ', report_txt or "").strip()
            clean = re.sub(r'\s+', ' ', clean)
            for para in clean.split('\n'):
                p = para.strip()
                if p:
                    story.append(Paragraph(p, s_body))
                    story.append(Spacer(1, 0.07*cm))
        except Exception as e:
            warnings_list.append(f"AI text section skipped: {e}")

        # ── PAGE FOOTER ──
        def draw_page(canvas_obj, doc_obj):
            try:
                canvas_obj.saveState()
                # Dark background
                canvas_obj.setFillColor(C_BG)
                canvas_obj.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
                # Footer bar
                canvas_obj.setFillColor(C_PANEL)
                canvas_obj.rect(0, 0, A4[0], 1.8*cm, fill=1, stroke=0)
                # Footer line
                canvas_obj.setStrokeColor(C_BLUE)
                canvas_obj.setLineWidth(0.8)
                canvas_obj.line(1.8*cm, 1.8*cm, A4[0]-1.8*cm, 1.8*cm)
                # Footer text
                canvas_obj.setFont(F if USE_DJ else "Helvetica", 6.5)
                canvas_obj.setFillColor(C_MUTED)
                canvas_obj.drawCentredString(
                    A4[0]/2, 0.7*cm,
                    f"ARIA Sales Intelligence  ·  {mode} Mode  ·  {datetime.datetime.now().strftime('%d %B %Y')}  ·  LLaMA 3.3-70B via Groq"
                )
                canvas_obj.setFillColor(C_CYAN)
                canvas_obj.drawRightString(A4[0]-1.8*cm, 0.7*cm, f"Page {doc_obj.page}")
                canvas_obj.restoreState()
            except Exception:
                pass

        if not story:
            return None, "All PDF sections failed. Check warnings:\n" + "\n".join(warnings_list)

        try:
            doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
        except Exception:
            tb = traceback.format_exc()
            return None, f"PDF build failed at doc.build():\n\n{tb}"

        pdf_out = buf.getvalue()
        warn_str = ("PDF built with skipped sections:\n" + "\n".join(warnings_list)) if warnings_list else None
        return pdf_out, warn_str

    # ── TRIGGER PDF ──
    if dl_pdf:
        report_src = st.session_state.get("bi_report_txt") or ""
        if not report_src:
            with st.spinner("Generating quick summary for PDF…"):
                try:
                    report_src = ask_groq(
                        "Give a concise executive summary of this company's sales data in 5 key bullet points.",
                        BI_SYSTEM_PROMPT, chat_history=[],
                    )
                except Exception as e:
                    report_src = f"Summary unavailable: {e}"

        pdf_prog = st.empty()
        for si in range(len(PDF_STEPS)):
            pdf_prog.markdown(render_steps(PDF_STEPS, si), unsafe_allow_html=True)
            time.sleep(0.25)

        pdf_bytes, err = build_pdf(report_src, current_mode, filename)
        pdf_prog.markdown(render_steps(PDF_STEPS, len(PDF_STEPS)), unsafe_allow_html=True)
        time.sleep(0.3)
        pdf_prog.empty()

        if pdf_bytes is None:
            st.error("PDF generation failed. Full traceback:")
            st.code(err or "Unknown error", language="text")
        else:
            if err:
                st.warning(err)
            st.success("✅ PDF ready — click below to download")
            st.download_button(
                label="⬇️  Download ARIA Intelligence Report (PDF)",
                data=pdf_bytes,
                file_name=f"ARIA_Report_{current_mode}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ── BOTTOM NAV ──
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
if st.button("← Back to Dashboard", use_container_width=True, key="bottom_nav"):
    st.switch_page("pages/1_Dashboard.py")
st.markdown('</div>', unsafe_allow_html=True)