import streamlit as st
if not st.session_state.get("password_correct", False):
    st.stop()

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import requests

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
    page_title="ARIA · Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────
# GUARD
# ─────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.warning("No dataset loaded.")
    st.page_link("app.py", label="← Upload Data", icon="⬅️")
    st.stop()

df       = st.session_state["df"]
filename = st.session_state.get("filename", "dataset.xlsx")

# ─────────────────────────────────────────────────────────────────
# TRANSACTIONS DATA (from 2nd sheet, if present in the uploaded file)
# ─────────────────────────────────────────────────────────────────
tx_df = pd.DataFrame()
if "uploaded_file_bytes" in st.session_state:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(BytesIO(st.session_state["uploaded_file_bytes"]), data_only=True)
        if "Transactions" in wb.sheetnames:
            ws = wb["Transactions"]
            rows = list(ws.iter_rows(values_only=True))
            hdrs = rows[0]
            tx_df = pd.DataFrame([dict(zip(hdrs, r)) for r in rows[1:] if any(v is not None for v in r)])
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────
# CHART THEME (consistent helper — avoids the duplicate-margin bug)
# ─────────────────────────────────────────────────────────────────
PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Manrope, sans-serif", color="#94A3B8", size=11),
)
BLUE_PAL = ["#3B82F6", "#06B6D4", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444", "#F97316", "#84CC16"]

def style_fig(fig, height=300, margin=None, **kwargs):
    """Apply the shared theme without ever colliding on duplicate kwargs."""
    fig.update_layout(**PLOT_BASE, height=height, **kwargs)
    fig.update_layout(margin=margin or dict(l=8, r=8, t=32, b=8))
    return fig

# ─────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

*,*::before,*::after{box-sizing:border-box;}
:root{
  --bg: #020510; --bg2: #040A1A; --bg3: #071020;
  --surface: rgba(255,255,255,0.032); --surface2: rgba(255,255,255,0.055);
  --border: rgba(255,255,255,0.072); --border2: rgba(255,255,255,0.12);
  --blue: #3B82F6; --blue2: #60A5FA; --cyan: #06B6D4; --purple: #8B5CF6;
  --green: #10B981; --gold: #F59E0B; --red: #EF4444; --orange: #F97316;
  --txt1: #F1F5F9; --txt2: #94A3B8; --txt3: #475569;
}
html,body,.stApp{
  background:
    radial-gradient(ellipse 80% 60% at 20% -5%, rgba(59,130,246,0.09) 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(139,92,246,0.07) 0%, transparent 55%),
    #020510 !important;
  color: var(--txt2); font-family: 'Inter', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 5.2rem 2.2vw 3rem !important; max-width: 100% !important; }

/* topbar */
#topbar{
  position:fixed;top:0;left:0;right:0;z-index:200;
  display:flex;align-items:center;justify-content:space-between;
  padding:.72rem 2rem; background:rgba(2,5,16,0.82);
  border-bottom:1px solid var(--border); backdrop-filter:blur(28px);
}
.tb-brand{display:flex;align-items:center;gap:.6rem;}
.tb-mark{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#3B82F6,#8B5CF6 55%,#06B6D4);
  display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:900;color:#fff;
  box-shadow:0 0 18px rgba(59,130,246,.4);}
.tb-name{font-size:.92rem;font-weight:800;color:var(--txt1);letter-spacing:-.3px;}
.tb-sep{color:var(--border2);margin:0 .3rem;}
.tb-page{font-size:.82rem;color:var(--txt2);font-weight:500;}
.tb-pills{display:flex;gap:.5rem;align-items:center;}
.tb-pill{font-family:'JetBrains Mono',monospace;font-size:.58rem;padding:3px 10px;border-radius:6px;
  background:var(--surface);border:1px solid var(--border);color:var(--txt3);letter-spacing:.4px;}
.tb-live{display:flex;align-items:center;gap:5px;font-family:'JetBrains Mono',monospace;font-size:.58rem;
  padding:3px 10px;border-radius:6px;background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.2);color:var(--green);}
.live-dot{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green);animation:lpulse 2s infinite;}
@keyframes lpulse{0%,100%{opacity:1;}50%{opacity:.25;}}

/* sidebar */
section[data-testid="stSidebar"]{background:rgba(4,10,26,.96) !important;border-right:1px solid var(--border) !important;backdrop-filter:blur(20px);}
section[data-testid="stSidebar"] *{color:var(--txt2) !important;}
.sb-hdr{font-family:'JetBrains Mono',monospace;font-size:.56rem;letter-spacing:2.5px;text-transform:uppercase;
  color:var(--blue2) !important;padding:.55rem 0 .25rem;margin-bottom:.4rem;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:6px;}
.sb-hdr::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(59,130,246,.2),transparent);}
.sb-stat{display:flex;justify-content:space-between;align-items:center;font-size:.76rem;padding:.2rem 0;}
.sb-stat .lbl{color:var(--txt3);} .sb-stat .val{color:var(--txt1);font-weight:600;}
.sb-chip{display:inline-flex;align-items:center;gap:5px;font-family:'JetBrains Mono',monospace;font-size:.58rem;
  padding:2px 9px;border-radius:99px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.22);color:var(--green);}
.chip-dot{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 5px var(--green);animation:lpulse 2s infinite;}

/* section header w/ helper subtitle — this is the core "easy to understand" pattern */
.sec-wrap{ margin: 2.4rem 0 1.1rem; }
.sec-hdr{display:flex;align-items:center;gap:10px;font-family:'JetBrains Mono',monospace;font-size:.62rem;
  color:var(--blue2);letter-spacing:2.5px;text-transform:uppercase;}
.sec-hdr .ln{flex:1;height:1px;background:linear-gradient(90deg,rgba(59,130,246,.25),transparent);}
.sec-hdr .badge{font-size:.5rem;padding:2px 7px;border-radius:4px;background:rgba(59,130,246,.1);
  border:1px solid rgba(59,130,246,.2);color:var(--blue2);letter-spacing:1px;}
.sec-sub{font-size:.82rem;color:var(--txt3);margin-top:.35rem;font-weight:400;line-height:1.5;max-width:780px;}

/* hero banner */
#hero-banner{border-radius:20px;border:1px solid rgba(59,130,246,.18);
  background:linear-gradient(120deg,rgba(59,130,246,.08) 0%,rgba(139,92,246,.05) 50%,rgba(6,182,212,.05) 100%);
  backdrop-filter:blur(18px);padding:1.6rem 1.8rem 1.4rem;position:relative;overflow:hidden;margin-bottom:1.6rem;}
#hero-banner::before{content:'';position:absolute;top:-60px;right:-40px;width:320px;height:320px;border-radius:50%;
  background:radial-gradient(circle,rgba(59,130,246,.13),transparent 70%);pointer-events:none;}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;position:relative;z-index:1;}
.hero-eyebrow{font-family:'JetBrains Mono',monospace;font-size:.58rem;color:var(--green);letter-spacing:2.5px;
  text-transform:uppercase;display:flex;align-items:center;gap:7px;margin-bottom:.55rem;}
.hero-dot{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green);animation:lpulse 2s infinite;}
.hero-title{font-size:1.4rem;font-weight:800;color:var(--txt1);margin-bottom:.3rem;}
.hero-desc{font-size:.84rem;color:var(--txt3);max-width:540px;line-height:1.55;}
.health-badge{font-family:'JetBrains Mono',monospace;font-size:.68rem;padding:7px 16px;border-radius:99px;
  white-space:nowrap;font-weight:700;letter-spacing:.4px;}
.health-good{background:rgba(16,185,129,.1);color:var(--green);border:1px solid rgba(16,185,129,.3);}
.health-warn{background:rgba(245,158,11,.1);color:var(--gold);border:1px solid rgba(245,158,11,.3);}
.health-bad{background:rgba(239,68,68,.1);color:var(--red);border:1px solid rgba(239,68,68,.3);}
.hero-meta-row{display:flex;flex-wrap:wrap;gap:.6rem;border-top:1px solid var(--border);padding-top:1rem;
  margin-top:1.1rem;position:relative;z-index:1;}
.hmeta{display:flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--txt3);background:rgba(255,255,255,.025);border:1px solid var(--border);border-radius:8px;padding:4px 11px;}
.hmeta b{color:var(--txt1);font-weight:700;}

/* KPI cards */
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin-bottom:.8rem;}
.kpi{border-radius:15px;border:1px solid var(--border);background:var(--surface);backdrop-filter:blur(14px);
  padding:1.05rem 1.2rem;transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;position:relative;overflow:hidden;}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;border-radius:15px 15px 0 0;opacity:.6;}
.kpi.blue::before{background:linear-gradient(90deg,var(--blue),var(--cyan));}
.kpi.cyan::before{background:linear-gradient(90deg,var(--cyan),var(--blue));}
.kpi.green::before{background:linear-gradient(90deg,var(--green),var(--cyan));}
.kpi.gold::before{background:linear-gradient(90deg,var(--gold),var(--orange));}
.kpi.purple::before{background:linear-gradient(90deg,var(--purple),var(--blue));}
.kpi.red::before{background:linear-gradient(90deg,var(--red),var(--orange));}
.kpi:hover{transform:translateY(-3px);border-color:var(--border2);box-shadow:0 8px 28px rgba(59,130,246,.1);}
.kpi-top{display:flex;justify-content:space-between;align-items:flex-start;}
.kpi-icon{font-size:1.15rem;}
.kpi-help{font-size:.6rem;color:var(--txt3);cursor:help;border:1px solid var(--border);border-radius:50%;
  width:16px;height:16px;display:flex;align-items:center;justify-content:center;}
.kpi-lab{font-family:'JetBrains Mono',monospace;font-size:.53rem;color:var(--txt3);text-transform:uppercase;
  letter-spacing:1.2px;margin:.5rem 0 .3rem;}
.kpi-val{font-size:1.5rem;font-weight:800;line-height:1.1;margin-bottom:.25rem;}
.kpi-val.blue{color:var(--blue2);} .kpi-val.cyan{color:var(--cyan);} .kpi-val.green{color:var(--green);}
.kpi-val.gold{color:var(--gold);} .kpi-val.purple{color:var(--purple);} .kpi-val.red{color:var(--red);}
.kpi-foot{font-size:.69rem;color:var(--txt3);}
.kpi-delta{font-size:.69rem;font-weight:700;margin-top:.25rem;display:inline-flex;align-items:center;gap:3px;}
.d-up{color:var(--green);} .d-dn{color:var(--red);}

/* glass card */
.gc{border-radius:17px;border:1px solid var(--border);background:var(--surface);backdrop-filter:blur(14px);
  padding:1.2rem 1.3rem;height:100%;}
.gc-title{font-family:'JetBrains Mono',monospace;font-size:.58rem;color:var(--txt3);text-transform:uppercase;
  letter-spacing:1.5px;margin-bottom:.85rem;display:flex;align-items:center;gap:6px;}
.gc-title .dot{width:5px;height:5px;border-radius:50%;background:var(--blue);flex-shrink:0;}
.gc-note{font-size:.72rem;color:var(--txt3);margin-top:.6rem;line-height:1.5;border-top:1px solid rgba(255,255,255,.04);padding-top:.6rem;}

/* leaderboard */
.lb-row{display:flex;align-items:center;gap:9px;padding:.45rem 0;border-bottom:1px solid rgba(255,255,255,.035);}
.lb-row:last-child{border-bottom:none;}
.lb-rank{width:22px;font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--txt3);flex-shrink:0;text-align:center;}
.lb-rank.r1{color:var(--gold);font-weight:700;} .lb-rank.r2{color:var(--txt2);font-weight:600;} .lb-rank.r3{color:var(--orange);font-weight:600;}
.lb-av{width:29px;height:29px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;
  font-size:.63rem;font-weight:700;background:rgba(59,130,246,.15);color:var(--blue2);border:1px solid rgba(59,130,246,.22);}
.lb-av.gold{background:rgba(245,158,11,.12);color:var(--gold);border-color:rgba(245,158,11,.22);}
.lb-info{flex:1;min-width:0;} .lb-top{display:flex;justify-content:space-between;align-items:center;}
.lb-name{font-size:.81rem;color:var(--txt2);font-weight:500;} .lb-cat{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--txt3);}
.lb-val{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--txt1);font-weight:700;}
.lb-bar{height:2.5px;border-radius:99px;background:rgba(255,255,255,.05);margin-top:4px;overflow:hidden;}
.lb-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--cyan));}
.consist-badge{font-family:'JetBrains Mono',monospace;font-size:.48rem;padding:1px 7px;border-radius:5px;margin-left:.4rem;}
.consist-reliable{background:rgba(16,185,129,.1);color:var(--green);} .consist-watch{background:rgba(245,158,11,.1);color:var(--gold);}

/* channel rows */
.ch-row{display:flex;align-items:center;justify-content:space-between;padding:.42rem 0;border-bottom:1px solid rgba(255,255,255,.035);}
.ch-row:last-child{border-bottom:none;}
.ch-name{font-size:.8rem;color:var(--txt2);} .ch-sub{font-size:.62rem;color:var(--txt3);display:block;}
.ch-bar-wrap{flex:1;margin:0 .8rem;height:5px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;}
.ch-bar{height:100%;border-radius:99px;}
.ch-val{font-family:'JetBrains Mono',monospace;font-size:.73rem;color:var(--txt1);font-weight:600;white-space:nowrap;}
.ch-pct{font-size:.62rem;color:var(--txt3);margin-left:.4rem;}

/* alerts */
.alert-card{display:flex;align-items:center;gap:8px;padding:.4rem .75rem;border-radius:11px;
  background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);margin-bottom:.32rem;font-size:.77rem;color:var(--txt2);}
.alert-card .adot{width:6px;height:6px;border-radius:50%;background:var(--red);box-shadow:0 0 5px var(--red);flex-shrink:0;}
.ok-card{display:flex;align-items:center;gap:6px;font-size:.79rem;color:var(--green);padding:.3rem 0;}

/* health badges */
.hbadge{font-family:'JetBrains Mono',monospace;font-size:.55rem;padding:2px 8px;border-radius:6px;}
.hbadge.strong{background:rgba(16,185,129,.08);color:var(--green);border:1px solid rgba(16,185,129,.2);}
.hbadge.moderate{background:rgba(245,158,11,.08);color:var(--gold);border:1px solid rgba(245,158,11,.2);}
.hbadge.low{background:rgba(239,68,68,.08);color:var(--red);border:1px solid rgba(239,68,68,.2);}

/* progress */
.prog-track{height:9px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;margin:.6rem 0 .35rem;}
.prog-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--purple),var(--cyan));}
.prog-cap{display:flex;justify-content:space-between;font-size:.7rem;color:var(--txt3);}

/* AI insight card */
.ai-card{border-radius:18px;border:1px solid rgba(139,92,246,.22);
  background:linear-gradient(135deg,rgba(139,92,246,.07),rgba(59,130,246,.04));padding:1.4rem 1.5rem;position:relative;overflow:hidden;}
.ai-card::before{content:'';position:absolute;top:-50px;right:-30px;width:220px;height:220px;border-radius:50%;
  background:radial-gradient(circle,rgba(139,92,246,.12),transparent 70%);pointer-events:none;}
.ai-title{font-size:1rem;font-weight:700;color:var(--txt1);display:flex;align-items:center;gap:8px;margin-bottom:.8rem;position:relative;z-index:1;}
.ai-badge{font-family:'JetBrains Mono',monospace;font-size:.55rem;padding:2px 9px;border-radius:99px;
  background:rgba(139,92,246,.12);border:1px solid rgba(139,92,246,.3);color:var(--purple);margin-left:auto;}
.ai-body{font-size:.86rem;color:var(--txt2);line-height:1.85;white-space:pre-wrap;position:relative;z-index:1;}
.ai-point{display:flex;gap:9px;padding:.4rem 0;border-bottom:1px solid rgba(255,255,255,.04);align-items:flex-start;}
.ai-point:last-child{border-bottom:none;}
.ai-point-icon{font-size:.9rem;flex-shrink:0;margin-top:1px;}

/* party / followup */
.party-row{display:flex;align-items:center;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid rgba(255,255,255,.035);}
.party-row:last-child{border-bottom:none;}
.party-name{font-size:.8rem;color:var(--txt2);} .party-val{font-family:'JetBrains Mono',monospace;font-size:.75rem;color:var(--txt1);font-weight:600;}
.party-due{font-size:.63rem;color:var(--red);}
.fu-row{display:flex;align-items:center;gap:9px;padding:.4rem .68rem;border-radius:10px;background:rgba(245,158,11,.04);
  border:1px solid rgba(245,158,11,.12);margin-bottom:.3rem;font-size:.77rem;color:var(--txt2);}
.fu-dot{width:5px;height:5px;border-radius:50%;background:var(--gold);flex-shrink:0;}
.fu-inv{font-family:'JetBrains Mono',monospace;font-size:.65rem;color:var(--txt3);}

/* coll */
.coll-row{display:flex;justify-content:space-between;align-items:center;padding:.38rem 0;border-bottom:1px solid rgba(255,255,255,.035);}
.coll-row:last-child{border-bottom:none;}
.coll-lbl{font-size:.78rem;color:var(--txt3);} .coll-val{font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--txt1);font-weight:600;}

/* table & buttons */
div[data-testid="stDataFrame"]{border-radius:13px;overflow:hidden;border:1px solid var(--border);}
.stButton button,.stDownloadButton button{
  background:linear-gradient(135deg,rgba(59,130,246,.12),rgba(139,92,246,.09)) !important;
  border:1px solid rgba(59,130,246,.25) !important;color:var(--txt1) !important;border-radius:11px !important;
  font-family:'Inter',sans-serif !important;font-weight:600 !important;transition:all .22s ease !important;}
.stButton button:hover,.stDownloadButton button:hover{border-color:var(--cyan) !important;
  box-shadow:0 0 18px rgba(6,182,212,.12) !important;transform:translateY(-1px) !important;}
.stButton button[kind="primary"]{background:linear-gradient(135deg,var(--blue),var(--purple)) !important;border:none !important;}

div[data-testid="stRadio"]>div{display:flex;gap:.4rem;flex-wrap:wrap;}
div[data-testid="stRadio"] label{background:var(--surface);border:1px solid var(--border);border-radius:9px;
  padding:3px 13px;font-size:.71rem;cursor:pointer;transition:all .18s;}
div[data-testid="stRadio"] label:hover{border-color:var(--blue);}
div[data-testid="stSelectbox"] label,div[data-testid="stMultiSelect"] label,div[data-testid="stSlider"] label{
  color:var(--txt3) !important;font-family:'JetBrains Mono',monospace !important;font-size:.58rem !important;
  text-transform:uppercase !important;letter-spacing:1px !important;}

/* footer */
.aria-footer{text-align:center;margin-top:2.5rem;padding-top:1.4rem;border-top:1px solid var(--border);
  font-family:'JetBrains Mono',monospace;font-size:.6rem;color:var(--txt3);letter-spacing:1px;}

::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(59,130,246,.3);border-radius:99px;}
</style>
""", unsafe_allow_html=True)


def section_header(title, subtitle, badge=None):
    """Consistent section header with a one-line plain-English explanation underneath."""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="sec-wrap">
      <div class="sec-hdr">◈ {title}{badge_html}<div class="ln"></div></div>
      <div class="sec-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div id="topbar">
  <div class="tb-brand">
    <div class="tb-mark">A</div>
    <div class="tb-name">ARIA</div>
    <div class="tb-sep">·</div>
    <div class="tb-page">Sales Intelligence Dashboard</div>
  </div>
  <div class="tb-pills">
    <div class="tb-pill">{filename}</div>
    <div class="tb-pill">LLaMA 3.3-70B</div>
    <div class="tb-live"><div class="live-dot"></div>Live</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.9rem .5rem .4rem;border-bottom:1px solid var(--border);margin-bottom:.6rem;">
      <div style="display:flex;align-items:center;gap:.5rem;">
        <div style="width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#3B82F6,#8B5CF6 55%,#06B6D4);display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:900;color:#fff;">A</div>
        <div>
          <div style="font-size:.88rem;font-weight:800;color:#F1F5F9;">ARIA Dashboard</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:.5rem;color:#475569;">v5.0 · Neural Glass</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-hdr">System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-chip"><div class="chip-dot"></div>All Systems Online</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-top:.6rem;">
      <div class="sb-stat"><span class="lbl">File</span><span class="val" style="font-size:.65rem;">{filename}</span></div>
      <div class="sb-stat"><span class="lbl">Rows</span><span class="val">{len(df)}</span></div>
      <div class="sb-stat"><span class="lbl">Cols</span><span class="val">{len(df.columns)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-hdr" style="margin-top:.9rem;">Date Range</div>', unsafe_allow_html=True)
    n_date_cols = max(len(df.columns) - 1, 1)
    preset = st.selectbox("Quick Select", ["Full Range", "Last 7 Days", "Last 14 Days", "This Week"],
                           label_visibility="collapsed",
                           help="Choose how much of the report to analyze. 'Full Range' uses every day in the file.")
    if preset == "Last 7 Days":
        date_range = (max(1, n_date_cols - 6), n_date_cols)
    elif preset == "Last 14 Days":
        date_range = (max(1, n_date_cols - 13), n_date_cols)
    elif preset == "This Week":
        date_range = (max(1, n_date_cols - 4), n_date_cols)
    else:
        date_range = (1, n_date_cols)

    lo, hi = date_range
    st.markdown(f"""<div class="sb-stat"><span class="lbl">Period</span><span class="val">Day {lo} – {hi}</span></div>
    <div class="sb-stat"><span class="lbl">Days</span><span class="val">{hi-lo+1}</span></div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-hdr" style="margin-top:.9rem;">Filters</div>', unsafe_allow_html=True)
    all_people_df = get_salesperson_totals(df)
    all_cats = sorted(all_people_df["Category"].unique().tolist()) if not all_people_df.empty else []
    sel_cats = st.multiselect("Category", options=all_cats, default=all_cats, label_visibility="collapsed",
                               placeholder="Filter categories…",
                               help="Show only the sales channels you pick (e.g. just ADS or just Office Kerala).")
    avail_names = all_people_df[all_people_df["Category"].isin(sel_cats)]["Salesperson"].tolist() if sel_cats else []
    sel_people = st.multiselect("Salesperson", options=avail_names, default=avail_names,
                                 label_visibility="collapsed", placeholder="Filter people…",
                                 help="Narrow the dashboard down to specific salespeople.")

    st.markdown('<div class="sb-hdr" style="margin-top:.9rem;">Target</div>', unsafe_allow_html=True)
    monthly_target = st.number_input("Monthly Target (₹)", min_value=0, value=2_000_000, step=100_000,
                                      label_visibility="collapsed",
                                      help="Your sales goal for the month — used to calculate progress %.")

    st.markdown('<div class="sb-hdr" style="margin-top:.9rem;">Display</div>', unsafe_allow_html=True)
    show_raw      = st.checkbox("Show data tables", value=True)
    show_tx       = st.checkbox("Show transactions", value=True)
    leaderboard_n = st.slider("Leaderboard size", 5, 25, 10, label_visibility="collapsed")

    st.markdown("<div style='height:.4rem;'></div>", unsafe_allow_html=True)
    if st.button("← New Upload", use_container_width=True):
        st.switch_page("app.py")
    if st.button("AI Copilot →", use_container_width=True, type="primary"):
        st.switch_page("pages/2_AI_Chat.py")

# ─────────────────────────────────────────────────────────────────
# DATA COMPUTATION
# ─────────────────────────────────────────────────────────────────
date_cols_all      = df.columns[1:]
selected_date_cols = date_cols_all[lo - 1: hi]
filtered_df        = df[[df.columns[0]] + list(selected_date_cols)].copy()

person_totals = get_salesperson_totals(filtered_df)
if sel_people:
    person_totals = person_totals[person_totals["Salesperson"].isin(sel_people)]
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
top_performer = person_totals.iloc[0] if not person_totals.empty else None

today_val   = float(daily_totals.iloc[-1]) if len(daily_totals) >= 1 else 0.0
yest_val    = float(daily_totals.iloc[-2]) if len(daily_totals) >= 2 else 0.0
day_chg_pct = ((today_val - yest_val) / yest_val * 100) if yest_val else 0.0

week_this    = float(daily_totals.iloc[-7:].sum())    if len(daily_totals) >= 7  else float(daily_totals.sum())
week_prev    = float(daily_totals.iloc[-14:-7].sum()) if len(daily_totals) >= 14 else 0.0
week_chg_pct = ((week_this - week_prev) / week_prev * 100) if week_prev else 0.0

progress_pct = min(real_mtd / monthly_target * 100, 100) if monthly_target else 0
best_idx     = int(daily_totals.values.argmax()) if len(daily_totals) else 0
worst_idx    = int(daily_totals.values.argmin()) if len(daily_totals) else 0

tp_name = top_performer["Salesperson"] if top_performer is not None else "—"
tp_val  = float(top_performer["Total"]) if top_performer is not None else 0.0

d_cls, d_arrow = ("d-up", "▲") if day_chg_pct >= 0 else ("d-dn", "▼")
w_cls, w_arrow = ("d-up", "▲") if week_chg_pct >= 0 else ("d-dn", "▼")

# Transactions metrics
tx_total = tx_received = tx_due = 0.0
tx_channels = {}; tx_payments = {}; tx_parties = {}
if not tx_df.empty:
    tx_total    = float(tx_df["Total Amount"].sum())
    tx_received = float(tx_df["Received/Paid Amount"].sum())
    tx_due      = float(tx_df["Balance Due"].sum())
    if "Sales Channel" in tx_df.columns:
        tx_channels = tx_df.groupby("Sales Channel")["Total Amount"].sum().sort_values(ascending=False).to_dict()
    if "Payment Type" in tx_df.columns:
        tx_payments = tx_df.groupby("Payment Type")["Total Amount"].sum().sort_values(ascending=False).to_dict()
    if "Party Name" in tx_df.columns:
        tx_parties = tx_df.groupby("Party Name")["Total Amount"].sum().sort_values(ascending=False).to_dict()

collection_rate = (tx_received / tx_total * 100) if tx_total else 0.0

# returns (best-effort lookup — section "Sales Return / Cancellation" in the raw report)
returns_total = 0.0
try:
    ret_row = df[df.iloc[:, 0].astype(str).str.contains("Sales Return", case=False, na=False)]
    if not ret_row.empty:
        returns_total = float(pd.to_numeric(ret_row.iloc[0, lo:hi+1], errors="coerce").fillna(0).sum())
except Exception:
    pass
net_sales = max(total_sales - returns_total, 0)

# cash & bank (best-effort lookup)
def _row_value(label_substr):
    try:
        r = df[df.iloc[:, 0].astype(str).str.contains(label_substr, case=False, na=False)]
        if not r.empty:
            return float(pd.to_numeric(r.iloc[0, 1:], errors="coerce").fillna(0).sum())
    except Exception:
        pass
    return 0.0

bank_balance = _row_value("Bank Balance TOTAL")
cash_balance = _row_value("Cash Balance TOTAL")

# overall health signal — plain-English summary for the hero banner
if week_chg_pct >= 5:
    health_cls, health_txt = "health-good", "🟢 Trending up this week"
elif week_chg_pct <= -5:
    health_cls, health_txt = "health-bad", "🔴 Sales declining this week"
else:
    health_cls, health_txt = "health-warn", "🟡 Holding steady this week"

# ─────────────────────────────────────────────────────────────────
# ① HERO BANNER — plain-English status
# ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div id="hero-banner">
  <div class="hero-top">
    <div>
      <div class="hero-eyebrow"><div class="hero-dot"></div>Live overview · Day {lo}–{hi} · {hi-lo+1} days selected</div>
      <div class="hero-title">How's the business doing right now?</div>
      <div class="hero-desc">This page turns your daily sales report into plain answers: who's performing, where the money's coming from, and what needs attention — no spreadsheet reading required.</div>
    </div>
    <div class="health-badge {health_cls}">{health_txt}</div>
  </div>
  <div class="hero-meta-row">
    <div class="hmeta">📄 <b>{filename}</b></div>
    <div class="hmeta">📊 <b>{len(df)}</b> rows · <b>{len(df.columns)}</b> columns</div>
    <div class="hmeta">👥 <b>{n_active}</b> active salespeople</div>
    <div class="hmeta">🧾 <b>{len(tx_df) if not tx_df.empty else 0}</b> logged transactions</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ② AI INSIGHTS — short auto-generated summary
# ─────────────────────────────────────────────────────────────────
section_header("AI Insights", "A short, plain-English summary generated by ARIA's AI — read this first if you're short on time.", "AI")


def generate_ai_insight(summary_text: str) -> str:
    api_key = st.session_state.get("groq_api_key") or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": (
                        "You are ARIA, a sales analytics assistant for a homeopathic/pharma sales business. "
                        "Given a data summary, write a short, plain-English insight in at most 4 short bullet "
                        "points. No jargon, no markdown headers, just 4 lines starting with an emoji. "
                        "Focus on: overall performance, a standout person or channel, a risk/concern if any, "
                        "and one practical suggestion."
                    )},
                    {"role": "user", "content": summary_text[:6000]},
                ],
                "temperature": 0.4,
                "max_tokens": 350,
            },
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return None
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=600)
def cached_ai_insight(cache_key: str, summary_text: str):
    return generate_ai_insight(summary_text)


ai_cache_key = f"{filename}-{lo}-{hi}-{total_sales:.0f}"
with st.spinner("ARIA is reading your data…"):
    ai_text = cached_ai_insight(ai_cache_key, get_data_summary_for_ai(filtered_df))

st.markdown('<div class="ai-card">', unsafe_allow_html=True)
st.markdown('<div class="ai-title">🧠 ARIA says<span class="ai-badge">LLaMA 3.3-70B</span></div>', unsafe_allow_html=True)
if ai_text:
    st.markdown(f'<div class="ai-body">{ai_text}</div>', unsafe_allow_html=True)
else:
    # graceful fallback if no API key / network — still useful, computed locally
    fallback = (
        f"📈 Total sales for the selected period: ₹{total_sales:,.0f}, averaging ₹{avg_daily:,.0f}/day.\n"
        f"🏆 {tp_name} is the top performer with ₹{tp_val:,.0f} in sales.\n"
        f"⚠️ {len(zero_list)} salesperson(s) had at least one zero-sale day in this period.\n"
        f"💡 Tip: open the AI Copilot page for deeper, conversational analysis of this data."
    )
    st.markdown(f'<div class="ai-body">{fallback}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ③ KEY METRICS
# ─────────────────────────────────────────────────────────────────
section_header("Key Metrics", "The core numbers that matter most — sales, targets, and how today compares to yesterday.", "LIVE")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi blue">
      <div class="kpi-top"><div class="kpi-icon">💰</div><div class="kpi-help" title="Total revenue across all channels for the selected date range.">?</div></div>
      <div class="kpi-lab">Total Sales</div>
      <div class="kpi-val blue">₹{total_sales:,.0f}</div>
      <div class="kpi-foot">Period: Day {lo}–{hi}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi cyan">
      <div class="kpi-top"><div class="kpi-icon">📅</div><div class="kpi-help" title="Total sales so far this month, compared against your target.">?</div></div>
      <div class="kpi-lab">Month To Date</div>
      <div class="kpi-val cyan">₹{real_mtd:,.0f}</div>
      <div class="kpi-foot">{progress_pct:.1f}% of target</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi gold">
      <div class="kpi-top"><div class="kpi-icon">📊</div><div class="kpi-help" title="Cumulative sales since the start of the year.">?</div></div>
      <div class="kpi-lab">Year To Date</div>
      <div class="kpi-val gold">₹{real_ytd:,.0f}</div>
      <div class="kpi-foot">Cumulative YTD</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi purple">
      <div class="kpi-top"><div class="kpi-icon">⚡</div><div class="kpi-help" title="Average sales per day over the selected period.">?</div></div>
      <div class="kpi-lab">Daily Average</div>
      <div class="kpi-val purple">₹{avg_daily:,.0f}</div>
      <div class="kpi-foot">Over {hi-lo+1} days</div>
    </div>""", unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5:
    st.markdown(f"""<div class="kpi gold">
      <div class="kpi-top"><div class="kpi-icon">🏆</div><div class="kpi-help" title="The salesperson with the highest total in this period.">?</div></div>
      <div class="kpi-lab">Top Performer</div>
      <div class="kpi-val gold" style="font-size:1.15rem;">{tp_name}</div>
      <div class="kpi-foot">₹{tp_val:,.0f} total</div>
    </div>""", unsafe_allow_html=True)
with c6:
    bill_count_val = "—"
    try:
        bill_row = df[df.iloc[:, 0].astype(str).str.contains("Bill Count", na=False)]
        if not bill_row.empty:
            bill_count_val = f"{int(bill_row.iloc[0, 1:].sum()):,}"
    except Exception:
        pass
    st.markdown(f"""<div class="kpi cyan">
      <div class="kpi-top"><div class="kpi-icon">🧾</div><div class="kpi-help" title="Total number of invoices/bills generated.">?</div></div>
      <div class="kpi-lab">Total Bill Count</div>
      <div class="kpi-val cyan">{bill_count_val}</div>
      <div class="kpi-foot">Invoices generated</div>
    </div>""", unsafe_allow_html=True)
with c7:
    pend_color = "red" if tx_due > tx_received else "gold"
    st.markdown(f"""<div class="kpi {pend_color}">
      <div class="kpi-top"><div class="kpi-icon">⏳</div><div class="kpi-help" title="Money invoiced but not yet collected from customers.">?</div></div>
      <div class="kpi-lab">Outstanding Dues</div>
      <div class="kpi-val {pend_color}">₹{tx_due:,.0f}</div>
      <div class="kpi-foot">{100 - collection_rate:.1f}% uncollected</div>
    </div>""", unsafe_allow_html=True)
with c8:
    zero_color = "red" if len(zero_list) > 0 else "green"
    st.markdown(f"""<div class="kpi {zero_color}">
      <div class="kpi-top"><div class="kpi-icon">🚨</div><div class="kpi-help" title="Salespeople who had at least one day with zero sales.">?</div></div>
      <div class="kpi-lab">Zero-Sale Alerts</div>
      <div class="kpi-val {zero_color}">{len(zero_list)}</div>
      <div class="kpi-foot">Sellers with gaps</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ④ DAILY SALES TREND
# ─────────────────────────────────────────────────────────────────
section_header("Daily Sales Trend", "See how sales moved day by day, and spot your best and worst days at a glance.")

ctrl_col, chart_col = st.columns([1, 4])
with ctrl_col:
    trend_type = st.radio("Chart", ["Area", "Line", "Bar", "Step"], key="trend")
    show_ma = st.checkbox("7-Day Average", value=True, help="Smooths daily ups and downs to show the underlying trend.")
    show_target_line = st.checkbox("Daily Target", value=False, help="Shows the daily sales goal needed to hit your monthly target.")
    if len(daily_totals):
        st.markdown(f"""
        <div style="margin-top:1rem;font-size:.75rem;color:var(--txt3);line-height:1.7;">
          🟢 Best day: <b style="color:var(--txt1);">Day {best_idx+1}</b><br>₹{daily_totals.values[best_idx]:,.0f}<br><br>
          🔴 Worst day: <b style="color:var(--txt1);">Day {worst_idx+1}</b><br>₹{daily_totals.values[worst_idx]:,.0f}
        </div>
        """, unsafe_allow_html=True)

with chart_col:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot"></div>Revenue · Daily View</div>', unsafe_allow_html=True)
    if len(daily_totals):
        x_labels = [f"Day {i+1}" for i in range(len(daily_totals))]
        y_vals = daily_totals.values
        daily_target = monthly_target / 26 if monthly_target else 0

        fig = go.Figure()
        if trend_type == "Area":
            fig.add_trace(go.Scatter(x=x_labels, y=y_vals, mode="lines",
                line=dict(color="#3B82F6", width=2.5, shape="spline"),
                fill="tozeroy", fillcolor="rgba(59,130,246,0.10)", name="Daily Sales"))
        elif trend_type == "Line":
            fig.add_trace(go.Scatter(x=x_labels, y=y_vals, mode="lines+markers",
                line=dict(color="#06B6D4", width=2.5, shape="spline"),
                marker=dict(size=5, color="#3B82F6"), name="Daily Sales"))
        elif trend_type == "Bar":
            colors_bar = ["rgba(59,130,246,0.85)" if v >= avg_daily else "rgba(139,92,246,0.7)" for v in y_vals]
            fig.add_trace(go.Bar(x=x_labels, y=y_vals,
                marker=dict(color=colors_bar, line=dict(color="rgba(59,130,246,0.3)", width=0.5)), name="Daily Sales"))
        else:
            fig.add_trace(go.Scatter(x=x_labels, y=y_vals, mode="lines",
                line=dict(color="#8B5CF6", width=2.5, shape="hv"), name="Daily Sales"))

        if show_ma and len(y_vals) >= 7:
            ma = pd.Series(y_vals).rolling(7).mean().values
            fig.add_trace(go.Scatter(x=x_labels, y=ma, mode="lines",
                line=dict(color="#F59E0B", width=1.5, dash="dot"), name="7-Day Average"))

        if show_target_line and daily_target:
            fig.add_hline(y=daily_target, line=dict(color="#EF4444", width=1, dash="dash"),
                          annotation_text=f"Target: ₹{daily_target:,.0f}")

        fig.update_xaxes(showgrid=False, tickfont=dict(size=9))
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickprefix="₹", tickformat=",.0f", tickfont=dict(size=9))
        style_fig(fig, height=330, showlegend=True, legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑤ SALES CHANNEL BREAKDOWN — new
# ─────────────────────────────────────────────────────────────────
section_header("Sales Channel Breakdown", "Where is your revenue actually coming from — your own office team, online stores, ads, or medical stores?")

ch_left, ch_right = st.columns([1.3, 1])
CHANNEL_LABELS = {
    "Office Sales Kerala":     ("🏢", "Your in-house sales team, Kerala"),
    "Office Sales Interstate": ("🚚", "In-house team selling outside Kerala"),
    "Company Direct Sales":    ("🤝", "Direct corporate / B2B deals"),
    "ADS":                     ("📣", "Sales driven by advertising campaigns"),
    "Exhibition Sales":        ("🎪", "Trade fairs and exhibitions"),
    "E-commerce Sales":        ("🛒", "Amazon, Flipkart, Jio, Web"),
    "Medical Store / Shops":   ("💊", "Third-party medical stores & dealers"),
}

with ch_left:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot"></div>📡 Revenue by Channel</div>', unsafe_allow_html=True)
    if not cat_totals.empty:
        cat_total_sum = cat_totals["Total"].sum()
        for _, row in cat_totals.sort_values("Total", ascending=False).iterrows():
            cat_name = row["Category"]
            pct = (row["Total"] / cat_total_sum * 100) if cat_total_sum else 0
            icon, desc = CHANNEL_LABELS.get(cat_name, ("📦", ""))
            color = BLUE_PAL[hash(cat_name) % len(BLUE_PAL)]
            st.markdown(f"""
            <div class="ch-row">
              <span class="ch-name">{icon} {cat_name}<span class="ch-sub">{desc}</span></span>
              <div class="ch-bar-wrap"><div class="ch-bar" style="width:{pct:.1f}%;background:{color};"></div></div>
              <span class="ch-val">₹{row['Total']:,.0f}<span class="ch-pct">{pct:.1f}%</span></span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.82rem;'>No channel data for this selection.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with ch_right:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot" style="background:var(--purple);"></div>🥧 Channel Share</div>', unsafe_allow_html=True)
    if not cat_totals.empty:
        donut = px.pie(cat_totals, names="Category", values="Total", hole=0.58, color_discrete_sequence=BLUE_PAL)
        donut.update_traces(textfont_color="#F1F5F9", marker=dict(line=dict(color="#020510", width=2)))
        style_fig(donut, height=280, legend=dict(font=dict(size=8.5)))
        st.plotly_chart(donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑥ TEAM PERFORMANCE
# ─────────────────────────────────────────────────────────────────
section_header("Team Performance", "See who's leading the pack, and who needs a closer look due to inconsistent sales.")
p1, p2 = st.columns([1.5, 1])

with p1:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot"></div>🏆 Salesperson Leaderboard</div>', unsafe_allow_html=True)
    if not person_totals.empty:
        max_v = person_totals["Total"].max()
        medals = {0: "r1", 1: "r2", 2: "r3"}
        html = ""
        for i, row in person_totals.head(leaderboard_n).reset_index(drop=True).iterrows():
            pct = (row["Total"] / max_v * 100) if max_v else 0
            rank_cls = medals.get(i, "")
            av_cls = "gold" if i == 0 else ""
            initial = row["Salesperson"][0].upper() if row["Salesperson"] else "?"
            is_zero_risk = row["Salesperson"] in zero_list
            consist_html = (
                '<span class="consist-badge consist-watch">⚠ Watch</span>' if is_zero_risk
                else '<span class="consist-badge consist-reliable">✓ Reliable</span>'
            )
            html += f"""
            <div class="lb-row">
              <div class="lb-rank {rank_cls}">#{i+1}</div>
              <div class="lb-av {av_cls}">{initial}</div>
              <div class="lb-info">
                <div class="lb-top">
                  <div>
                    <span class="lb-name">{row['Salesperson']}</span>
                    <span class="lb-cat"> · {row['Category']}</span>
                    {consist_html}
                  </div>
                  <span class="lb-val">₹{row['Total']:,.0f}</span>
                </div>
                <div class="lb-bar"><div class="lb-fill" style="width:{pct:.1f}%;"></div></div>
              </div>
            </div>"""
        st.markdown(html + '<div class="gc-note">💡 "Watch" means this person had at least one zero-sale day in the selected period — worth a quick check-in.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.82rem;'>No data.</div></div>", unsafe_allow_html=True)

with p2:
    st.markdown('<div class="gc" style="margin-bottom:.7rem;"><div class="gc-title"><div class="dot" style="background:var(--red);"></div>⚠️ Zero-Sales Alerts</div>', unsafe_allow_html=True)
    rel_zero = [n for n in zero_list if not sel_people or n in sel_people]
    if rel_zero:
        for n in rel_zero[:8]:
            st.markdown(f'<div class="alert-card"><div class="adot"></div>{n} · zero-sale day detected</div>', unsafe_allow_html=True)
        if len(rel_zero) > 8:
            st.markdown(f"<div style='font-size:.7rem;color:var(--txt3);margin-top:.3rem;'>+{len(rel_zero)-8} more</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-card">✅ No zero-sales in selected period</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""<div class="gc">
      <div class="gc-title"><div class="dot" style="background:var(--gold);"></div>🎯 Month Target</div>
      <div class="prog-track"><div class="prog-fill" style="width:{progress_pct:.1f}%;"></div></div>
      <div class="prog-cap"><span>₹{real_mtd:,.0f} achieved</span><span>{progress_pct:.1f}%</span></div>
      <div style="margin-top:.6rem;font-size:.74rem;color:var(--txt3);">
        Remaining: <b style="color:var(--txt1);">₹{max(0, monthly_target-real_mtd):,.0f}</b>
      </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑦ PRODUCT CATEGORY ANALYSIS (Pareto)
# ─────────────────────────────────────────────────────────────────
section_header("Product Category Analysis", "Which product categories drive most of your revenue? The line shows cumulative share — where it crosses 80% tells you which categories matter most.")

pc1, pc2 = st.columns([1.6, 1])
prod_cats = {}
try:
    PRODUCT_LABELS = ["AGRI SALE", "AQUA", "DAIRY", "GENERAL MEDICINE", "MET LIVE STOCK",
                      "PET", "POULTRY", "Precription - General", "Precription - Ann", "Precription - A k"]
    for plabel in PRODUCT_LABELS:
        r = df[df.iloc[:, 0].astype(str).str.strip().str.upper() == plabel.upper()]
        if not r.empty:
            val = float(pd.to_numeric(r.iloc[0, lo:hi+1], errors="coerce").fillna(0).sum())
            if val:
                prod_cats[plabel.title()] = val
except Exception:
    pass

with pc1:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot"></div>📊 Category Pareto (80/20 view)</div>', unsafe_allow_html=True)
    if prod_cats:
        pareto_df = pd.DataFrame(sorted(prod_cats.items(), key=lambda x: -x[1]), columns=["Category", "Total"])
        pareto_df["Cumulative %"] = pareto_df["Total"].cumsum() / pareto_df["Total"].sum() * 100
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=pareto_df["Category"], y=pareto_df["Total"], name="Revenue",
            marker=dict(color="#3B82F6")))
        fig_p.add_trace(go.Scatter(x=pareto_df["Category"], y=pareto_df["Cumulative %"], name="Cumulative %",
            yaxis="y2", line=dict(color="#F59E0B", width=2), mode="lines+markers"))
        fig_p.update_layout(
            yaxis=dict(tickprefix="₹", tickformat=",.0f", showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
            yaxis2=dict(overlaying="y", side="right", range=[0, 105], ticksuffix="%"),
            legend=dict(orientation="h", y=1.12, font=dict(size=9)),
        )
        fig_p.add_hline(y=80, yref="y2", line=dict(color="#EF4444", width=1, dash="dot"))
        style_fig(fig_p, height=300)
        st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.82rem;'>No product category rows detected in this file.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with pc2:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot" style="background:var(--green);"></div>🧬 Category Health</div>', unsafe_allow_html=True)
    if prod_cats:
        cmax = max(prod_cats.values())
        for cat, val in sorted(prod_cats.items(), key=lambda x: -x[1]):
            ratio = val / cmax if cmax else 0
            if ratio >= 0.6:
                bcls, btxt = "strong", "Strong"
            elif ratio >= 0.25:
                bcls, btxt = "moderate", "Moderate"
            else:
                bcls, btxt = "low", "Low"
            st.markdown(f"""
            <div class="ch-row">
              <span class="ch-name">{cat}</span>
              <span class="hbadge {bcls}">{btxt}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.8rem;'>No category data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑧ RETURNS & NET SALES — new (waterfall)
# ─────────────────────────────────────────────────────────────────
section_header("Returns & Net Sales", "How much of your gross sales actually stayed as real revenue, after returns and cancellations?")

rt1, rt2 = st.columns([1.6, 1])
with rt1:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot" style="background:var(--red);"></div>💧 Gross → Returns → Net</div>', unsafe_allow_html=True)
    wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Gross Sales", "Returns / Cancellations", "Net Sales"],
        y=[total_sales, -returns_total, net_sales],
        connector=dict(line=dict(color="rgba(255,255,255,.15)")),
        decreasing=dict(marker=dict(color="#EF4444")),
        increasing=dict(marker=dict(color="#10B981")),
        totals=dict(marker=dict(color="#3B82F6")),
        text=[f"₹{total_sales:,.0f}", f"-₹{returns_total:,.0f}", f"₹{net_sales:,.0f}"],
        textposition="outside",
    ))
    fig_wf = style_fig(wf, height=300, showlegend=False)
    fig_wf.update_yaxes(tickprefix="₹", tickformat=",.0f", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    st.plotly_chart(fig_wf, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with rt2:
    return_pct = (returns_total / total_sales * 100) if total_sales else 0
    return_color = "red" if return_pct > 10 else ("gold" if return_pct > 5 else "green")
    st.markdown(f"""<div class="gc">
      <div class="gc-title"><div class="dot" style="background:var(--red);"></div>📉 Return Impact</div>
      <div class="kpi-val {return_color}" style="font-size:2rem;">{return_pct:.1f}%</div>
      <div class="kpi-foot" style="margin-bottom:.8rem;">of gross sales returned or cancelled</div>
      <div class="coll-row"><span class="coll-lbl">Gross Sales</span><span class="coll-val">₹{total_sales:,.0f}</span></div>
      <div class="coll-row"><span class="coll-lbl">Returns</span><span class="coll-val" style="color:var(--red);">₹{returns_total:,.0f}</span></div>
      <div class="coll-row"><span class="coll-lbl">Net Sales</span><span class="coll-val" style="color:var(--green);">₹{net_sales:,.0f}</span></div>
      <div class="gc-note">💡 A return rate above 10% is usually worth investigating — it may point to product quality or fulfillment issues.</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑨ MONEY & CASH POSITION — new
# ─────────────────────────────────────────────────────────────────
section_header("Money & Cash Position", "How much money does the business have on hand right now, across bank and cash?")

mn1, mn2, mn3 = st.columns(3)
total_funds = bank_balance + cash_balance
with mn1:
    st.markdown(f"""<div class="kpi blue">
      <div class="kpi-top"><div class="kpi-icon">🏦</div><div class="kpi-help" title="Total funds held in bank accounts (current + fixed deposit).">?</div></div>
      <div class="kpi-lab">Bank Balance</div>
      <div class="kpi-val blue">₹{bank_balance:,.0f}</div>
      <div class="kpi-foot">Federal Bank · Current + FD</div>
    </div>""", unsafe_allow_html=True)
with mn2:
    st.markdown(f"""<div class="kpi green">
      <div class="kpi-top"><div class="kpi-icon">💵</div><div class="kpi-help" title="Physical cash held across all locations.">?</div></div>
      <div class="kpi-lab">Cash Balance</div>
      <div class="kpi-val green">₹{cash_balance:,.0f}</div>
      <div class="kpi-foot">Across all cash locations</div>
    </div>""", unsafe_allow_html=True)
with mn3:
    st.markdown(f"""<div class="kpi purple">
      <div class="kpi-top"><div class="kpi-icon">💰</div><div class="kpi-help" title="Bank balance + cash balance combined — your total available funds.">?</div></div>
      <div class="kpi-lab">Total Available Funds</div>
      <div class="kpi-val purple">₹{total_funds:,.0f}</div>
      <div class="kpi-foot">Bank + Cash combined</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑩ TRANSACTIONS & COLLECTIONS
# ─────────────────────────────────────────────────────────────────
section_header("Transactions & Collections", "Who owes you money, who's paid, and which follow-ups are due soon.")
tc1, tc2, tc3 = st.columns(3)

with tc1:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot" style="background:var(--green);"></div>💳 Collection Status</div>', unsafe_allow_html=True)
    if tx_total > 0:
        st.markdown(f"""
        <div class="coll-row"><span class="coll-lbl">Total Invoiced</span><span class="coll-val">₹{tx_total:,.0f}</span></div>
        <div class="coll-row"><span class="coll-lbl">Collected</span><span class="coll-val" style="color:var(--green);">₹{tx_received:,.0f}</span></div>
        <div class="coll-row"><span class="coll-lbl">Outstanding</span><span class="coll-val" style="color:var(--red);">₹{tx_due:,.0f}</span></div>
        <div class="coll-row"><span class="coll-lbl">Collection Rate</span><span class="coll-val" style="color:{'var(--green)' if collection_rate>=50 else 'var(--gold)'};">{collection_rate:.1f}%</span></div>
        """, unsafe_allow_html=True)
        donut2 = go.Figure(go.Pie(values=[tx_received, tx_due], labels=["Collected", "Outstanding"], hole=0.62,
            marker=dict(colors=["#10B981", "#EF4444"], line=dict(color="rgba(0,0,0,0)", width=0)), textfont=dict(size=10)))
        style_fig(donut2, height=160, showlegend=False, margin=dict(l=0, r=0, t=5, b=5))
        st.plotly_chart(donut2, use_container_width=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.8rem;'>No transaction data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tc2:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot" style="background:var(--cyan);"></div>💰 Payment Methods</div>', unsafe_allow_html=True)
    if tx_payments:
        total_pay = sum(tx_payments.values())
        PAY_COLORS = {"Razorpay": "#8B5CF6", "Cash": "#10B981", "Federal Bank": "#3B82F6"}
        for pay, val in tx_payments.items():
            pct = val / total_pay * 100 if total_pay else 0
            color = PAY_COLORS.get(pay, "#06B6D4")
            st.markdown(f"""
            <div class="ch-row">
              <span class="ch-name">{pay}</span>
              <div class="ch-bar-wrap"><div class="ch-bar" style="width:{pct:.1f}%;background:{color};"></div></div>
              <span class="ch-val">₹{val:,.0f}<span class="ch-pct">{pct:.1f}%</span></span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.8rem;'>No payment data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tc3:
    st.markdown('<div class="gc"><div class="gc-title"><div class="dot" style="background:var(--gold);"></div>📋 Upcoming Follow-Ups</div>', unsafe_allow_html=True)
    if not tx_df.empty and "Follow up date" in tx_df.columns:
        fu_df = tx_df[tx_df["Balance Due"] > 0].sort_values("Balance Due", ascending=False)
        for _, frow in fu_df.head(6).iterrows():
            party = frow.get("Party Name", "—")
            due = frow.get("Balance Due", 0)
            fu_date = frow.get("Follow up date", "—")
            st.markdown(f"""
            <div class="fu-row"><div class="fu-dot"></div>
              <div style="flex:1;"><div style="font-size:.76rem;color:var(--txt2);">{party} · <b style="color:var(--red);">₹{due:,.0f}</b></div>
              <div class="fu-inv">Due: {fu_date}</div></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:var(--txt3);font-size:.8rem;'>No follow-up data.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ⑪ EXPLORE THE DATA (tables + export) — power users
# ─────────────────────────────────────────────────────────────────
section_header("Explore the Data", "For when you want to dig into the raw numbers yourself, or export a copy.")

if show_raw:
    tbl_view = st.radio("Table view", ["Salesperson Totals", "Category Totals", "Daily Summary", "Filtered Dataset", "Full Dataset"],
                         horizontal=True, key="tbl_v")
    if tbl_view == "Salesperson Totals":
        st.dataframe(person_totals.style.format({"Total": "₹{:,.0f}"}), use_container_width=True, height=360)
    elif tbl_view == "Category Totals":
        st.dataframe(cat_totals.style.format({"Total": "₹{:,.0f}"}), use_container_width=True, height=360)
    elif tbl_view == "Daily Summary":
        daily_df = pd.DataFrame({"Day": [f"Day {i+1}" for i in range(len(daily_totals))],
                                  "Sales": daily_totals.values,
                                  "7-Day Avg": pd.Series(daily_totals.values).rolling(7).mean().values})
        st.dataframe(daily_df.style.format({"Sales": "₹{:,.0f}", "7-Day Avg": "₹{:,.0f}"}), use_container_width=True, height=360)
    elif tbl_view == "Filtered Dataset":
        st.dataframe(filtered_df, use_container_width=True, height=360)
    else:
        st.dataframe(df, use_container_width=True, height=360)

if show_tx and not tx_df.empty:
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    tf1, tf2, tf3 = st.columns(3)
    with tf1:
        ch_filter = st.multiselect("Channel", options=sorted(tx_df["Sales Channel"].dropna().unique().tolist()) if "Sales Channel" in tx_df.columns else [],
                                    default=None, placeholder="All channels", label_visibility="collapsed")
    with tf2:
        sm_filter = st.multiselect("Salesman", options=sorted(tx_df["Salesman Name"].dropna().unique().tolist()) if "Salesman Name" in tx_df.columns else [],
                                    default=None, placeholder="All salesmen", label_visibility="collapsed")
    with tf3:
        show_pending_only = st.checkbox("Pending only (Balance Due > 0)", value=False)

    disp_tx = tx_df.copy()
    if ch_filter and "Sales Channel" in disp_tx.columns:
        disp_tx = disp_tx[disp_tx["Sales Channel"].isin(ch_filter)]
    if sm_filter and "Salesman Name" in disp_tx.columns:
        disp_tx = disp_tx[disp_tx["Salesman Name"].isin(sm_filter)]
    if show_pending_only and "Balance Due" in disp_tx.columns:
        disp_tx = disp_tx[disp_tx["Balance Due"] > 0]

    st.dataframe(disp_tx, use_container_width=True, height=400)
    st.markdown(f"<div style='font-size:.7rem;color:var(--txt3);margin-top:.3rem;'>{len(disp_tx):,} transactions · ₹{disp_tx['Total Amount'].sum():,.0f} total · ₹{disp_tx['Balance Due'].sum():,.0f} outstanding</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# EXPORT CENTER
# ─────────────────────────────────────────────────────────────────
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
e1, e2, e3 = st.columns(3)
with e1:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Filtered")
        person_totals.to_excel(writer, index=False, sheet_name="Leaderboard")
        cat_totals.to_excel(writer, index=False, sheet_name="Categories")
        if not tx_df.empty:
            tx_df.to_excel(writer, index=False, sheet_name="Transactions")
    st.download_button("⬇ Excel Report", data=buf.getvalue(),
        file_name=f"ARIA_report_{filename.split('.')[0]}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with e2:
    st.download_button("⬇ AI Summary (.txt)", data=get_data_summary_for_ai(df),
        file_name="aria_ai_context.txt", mime="text/plain", use_container_width=True)
with e3:
    csv_buf = BytesIO()
    filtered_df.to_csv(csv_buf, index=False)
    st.download_button("⬇ CSV (Filtered)", data=csv_buf.getvalue(),
        file_name=f"aria_{filename.split('.')[0]}.csv", mime="text/csv", use_container_width=True)

# ─────────────────────────────────────────────────────────────────
# NAVIGATION + FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)
if st.button("Continue to ARIA AI Copilot →", use_container_width=True, type="primary"):
    st.switch_page("pages/2_AI_Chat.py")

st.markdown("""
<div class="aria-footer">ARIA · Sales Intelligence Platform · v5.0 Neural Glass</div>
""", unsafe_allow_html=True)