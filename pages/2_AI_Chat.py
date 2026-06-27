import streamlit as st
if not st.session_state.get("password_correct", False):
    st.stop()

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

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

:root{
  --bg-1:#050816; --bg-2:#071124; --bg-3:#091A30;
  --blue:#4F8CFF; --blue-d:rgba(79,140,255,0.12);
  --purple:#7B61FF; --purple-d:rgba(123,97,255,0.12);
  --cyan:#00D4FF; --cyan-d:rgba(0,212,255,0.10);
  --green:#00FFC6; --green-d:rgba(0,255,198,0.10);
  --gold:#FFD166; --gold-d:rgba(255,209,102,0.10);
  --red:#FF6B6B; --red-d:rgba(255,107,107,0.10);
  --text-primary:#FFFFFF; --text-secondary:#C8D4E8; --text-muted:#8A97B5;
  --glass-border:rgba(255,255,255,0.08); --glass-bg:rgba(255,255,255,0.05);
}

html,body,.stApp{
  background:radial-gradient(ellipse 120% 80% at 50% -10%,var(--bg-3) 0%,var(--bg-2) 45%,var(--bg-1) 100%) !important;
  font-family:'Manrope',sans-serif;
  color:var(--text-secondary);
}

.stApp::before{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background:
    radial-gradient(ellipse 60% 40% at 15% 20%,rgba(79,140,255,0.06) 0%,transparent 65%),
    radial-gradient(ellipse 50% 35% at 85% 75%,rgba(123,97,255,0.05) 0%,transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%,rgba(0,212,255,0.03) 0%,transparent 55%);
}

#MainMenu,footer,header,.stDeployButton{visibility:hidden;}

.block-container{
  padding:0.8rem 2vw 5rem !important;
  max-width:920px !important;
  margin:0 auto !important;
  position:relative; z-index:1;
}

/* ── ANIMATIONS ── */
@keyframes pulse      {0%,100%{opacity:1;}50%{opacity:.25;}}
@keyframes glow       {0%,100%{box-shadow:0 0 10px rgba(79,140,255,.35);}50%{box-shadow:0 0 24px rgba(79,140,255,.7);}}
@keyframes glowCyan   {0%,100%{box-shadow:0 0 10px rgba(0,212,255,.3);}50%{box-shadow:0 0 22px rgba(0,212,255,.65);}}
@keyframes glowGold   {0%,100%{box-shadow:0 0 10px rgba(255,209,102,.3);}50%{box-shadow:0 0 22px rgba(255,209,102,.6);}}
@keyframes bounce3    {0%,60%,100%{transform:translateY(0);}30%{transform:translateY(-6px);}}
@keyframes slideUp    {from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
@keyframes morphGrad  {0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}
@keyframes shimmer    {0%{opacity:0.4;}50%{opacity:1;}100%{opacity:0.4;}}
@keyframes ringFill   {from{stroke-dashoffset:131.9;}to{stroke-dashoffset:var(--ring-offset);}}

/* ══ TOPBAR ══ */
.topbar{
  display:flex; align-items:center; justify-content:space-between;
  padding:.55rem 1.2rem; margin-bottom:.9rem;
  background:rgba(10,13,28,0.92);
  border:1px solid rgba(79,140,255,0.14);
  border-radius:18px; backdrop-filter:blur(24px);
  animation:slideUp .5s ease both; position:relative; overflow:hidden;
}
.topbar::before{
  content:''; position:absolute; inset:0;
  background:linear-gradient(90deg,rgba(79,140,255,.04) 0%,transparent 40%,rgba(0,212,255,.03) 100%);
  pointer-events:none;
}
.tb-left{display:flex;align-items:center;gap:.75rem;}
.tb-logo{
  width:34px;height:34px;border-radius:10px;flex-shrink:0;
  background:linear-gradient(135deg,#4F8CFF 0%,#7B61FF 55%,#00D4FF 100%);
  display:flex;align-items:center;justify-content:center;
  font-size:.85rem;font-weight:900;color:#fff;letter-spacing:-.5px;
  animation:glow 3s ease infinite;
}
.tb-name{font-size:1rem;font-weight:900;color:var(--text-primary);letter-spacing:-.5px;}
.tb-tag{
  font-family:'JetBrains Mono',monospace;font-size:.54rem;font-weight:600;
  padding:2px 10px;border-radius:99px;
  background:linear-gradient(90deg,rgba(0,212,255,.12),rgba(79,140,255,.12));
  border:1px solid rgba(0,212,255,.22);color:var(--cyan);letter-spacing:.5px;
}
.tb-right{display:flex;align-items:center;gap:7px;}
.tb-pill{
  font-family:'JetBrains Mono',monospace;font-size:.53rem;color:var(--text-muted);
  background:rgba(255,255,255,.025);border:1px solid var(--glass-border);
  padding:3px 9px;border-radius:7px;
}
.tb-live{
  display:flex;align-items:center;gap:5px;
  font-family:'JetBrains Mono',monospace;font-size:.53rem;color:var(--green);
  background:var(--green-d);border:1px solid rgba(0,255,198,.18);
  padding:3px 9px;border-radius:7px;
}
.tb-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 1.8s infinite;}

/* ══ SIDEBAR BASE ══ */
section[data-testid="stSidebar"]{
  background:rgba(7,17,36,0.95) !important;
  border-right:1px solid var(--glass-border) !important;
  backdrop-filter:blur(20px);
}
section[data-testid="stSidebar"] *{color:var(--text-secondary) !important;}

.sb-brand{
  display:flex;align-items:center;gap:10px;
  padding:1rem .9rem .6rem;
  border-bottom:1px solid rgba(255,255,255,.04);
  margin-bottom:.3rem;
}
.sb-brand-logo{
  width:36px;height:36px;border-radius:10px;
  background:linear-gradient(135deg,#4F8CFF,#7B61FF 55%,#00D4FF);
  display:flex;align-items:center;justify-content:center;
  font-size:.9rem;font-weight:900;color:#fff;
  box-shadow:0 0 16px rgba(79,140,255,.4);
}
.sb-brand-name{font-size:.9rem;font-weight:800;color:var(--text-primary);}
.sb-brand-sub{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--text-muted);}

.sec{
  font-family:'JetBrains Mono',monospace;font-size:.48rem;
  letter-spacing:2.5px;text-transform:uppercase;
  padding:.55rem .9rem .2rem;color:var(--text-muted) !important;
  display:flex;align-items:center;gap:6px;
}
.sec::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,.06),transparent);}

/* ══ HEALTH RING ══ */
.health-ring-wrap{
  margin:.3rem .6rem .5rem;
  background:rgba(255,255,255,.018);
  border:1px solid rgba(255,255,255,.07);
  border-radius:13px; padding:.65rem .75rem;
  display:flex; align-items:center; gap:.75rem;
}
.health-label{font-family:'JetBrains Mono',monospace;font-size:.46rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;}
.health-score{font-size:1.1rem;font-weight:800;line-height:1;}
.health-mood{font-size:.6rem;font-weight:600;margin-top:3px;display:flex;align-items:center;gap:4px;}
.mood-dot{width:6px;height:6px;border-radius:50%;display:inline-block;flex-shrink:0;}

/* ══ MINI LEADERBOARD ══ */
.mini-lb{margin:0 .5rem .4rem;}
.mlb-row{display:flex;align-items:center;gap:7px;padding:.32rem .5rem;border-radius:9px;margin-bottom:4px;background:rgba(255,255,255,.018);border:1px solid rgba(255,255,255,.05);transition:all .15s;}
.mlb-gold{background:rgba(255,209,102,.06) !important;border-color:rgba(255,209,102,.18) !important;}
.mlb-row:hover{background:rgba(255,255,255,.03);border-color:rgba(255,255,255,.09);}
.mlb-rank{font-family:'JetBrains Mono',monospace;font-size:.48rem;color:var(--text-muted);width:14px;flex-shrink:0;text-align:center;}
.mlb-rank.gold{color:var(--gold);font-weight:700;}
.mlb-av{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.52rem;font-weight:700;flex-shrink:0;background:rgba(79,140,255,.18);color:#A8C5FF;border:1px solid rgba(79,140,255,.2);}
.mlb-av.gold{background:rgba(255,209,102,.15);color:#FFD980;border-color:rgba(255,209,102,.25);}
.mlb-name{font-size:.63rem;font-weight:600;color:var(--text-secondary);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.mlb-val{font-size:.58rem;font-weight:700;color:var(--green);font-family:'JetBrains Mono',monospace;}

/* ══ QUICK ASK CATEGORISED ══ */
.qcat-label{
  font-size:.46rem;font-family:'JetBrains Mono',monospace;
  text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);
  margin:.3rem 0 .2rem .6rem;
}
.qtile-wrap .stButton button{
  width:100% !important; min-height:58px !important;
  display:flex !important; flex-direction:column !important;
  align-items:center !important; justify-content:center !important;
  gap:3px !important; border-radius:10px !important;
  font-family:'Manrope',sans-serif !important;
  font-size:.62rem !important; font-weight:600 !important;
  line-height:1.2 !important; text-align:center !important;
  padding:.4rem .3rem !important; margin-bottom:5px !important;
  white-space:normal !important; transition:all .18s ease !important;
}
.qtile-wrap .stButton button p{font-size:.62rem !important;line-height:1.2 !important;}
.qtile-wrap.qtile-0 button{background:var(--blue-d) !important;border:1px solid rgba(79,140,255,.22) !important;color:#A8C5FF !important;}
.qtile-wrap.qtile-1 button{background:var(--gold-d) !important;border:1px solid rgba(255,209,102,.25) !important;color:#FFD980 !important;}
.qtile-wrap.qtile-2 button{background:var(--red-d) !important;border:1px solid rgba(255,107,107,.25) !important;color:#FF9090 !important;}
.qtile-wrap.qtile-3 button{background:var(--purple-d) !important;border:1px solid rgba(123,97,255,.22) !important;color:#BFB0FF !important;}
.qtile-wrap.qtile-4 button{background:var(--cyan-d) !important;border:1px solid rgba(0,212,255,.22) !important;color:#5CE0FF !important;}
.qtile-wrap.qtile-5 button{background:var(--green-d) !important;border:1px solid rgba(0,255,198,.18) !important;color:#5FFFDA !important;}
.qtile-wrap.qtile-0 button:hover{border-color:rgba(79,140,255,.55) !important;transform:translateY(-2px) !important;box-shadow:0 4px 14px rgba(79,140,255,.15) !important;}
.qtile-wrap.qtile-1 button:hover{border-color:rgba(255,209,102,.6) !important;transform:translateY(-2px) !important;box-shadow:0 4px 14px rgba(255,209,102,.12) !important;}
.qtile-wrap.qtile-2 button:hover{border-color:rgba(255,107,107,.55) !important;transform:translateY(-2px) !important;box-shadow:0 4px 14px rgba(255,107,107,.12) !important;}
.qtile-wrap.qtile-3 button:hover{border-color:rgba(123,97,255,.5) !important;transform:translateY(-2px) !important;box-shadow:0 4px 14px rgba(123,97,255,.12) !important;}
.qtile-wrap.qtile-4 button:hover{border-color:rgba(0,212,255,.55) !important;transform:translateY(-2px) !important;box-shadow:0 4px 14px rgba(0,212,255,.12) !important;}
.qtile-wrap.qtile-5 button:hover{border-color:rgba(0,255,198,.5) !important;transform:translateY(-2px) !important;box-shadow:0 4px 14px rgba(0,255,198,.1) !important;}

/* ══ SESSION STATS ══ */
.sess-stats{margin:.2rem .5rem .4rem;display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;}
.sess-card{background:rgba(255,255,255,.018);border:1px solid rgba(255,255,255,.06);border-radius:9px;padding:.38rem .3rem;text-align:center;}
.sess-num{font-size:.85rem;font-weight:700;color:var(--text-primary);}
.sess-lbl{font-family:'JetBrains Mono',monospace;font-size:.42rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-top:1px;}

/* ══ KPI cards ══ */
.sb-kpi{
  margin:0 .5rem .28rem;
  background:rgba(255,255,255,.018);
  border:1px solid rgba(255,255,255,.07);
  border-radius:11px; padding:.45rem .65rem;
  display:flex; align-items:center; justify-content:space-between;
  transition:all .2s;
}
.sb-kpi:hover{background:rgba(255,255,255,.03);border-color:rgba(255,255,255,.1);}
.sb-kpi-label{font-family:'JetBrains Mono',monospace;font-size:.44rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;}
.sb-kpi-value{font-size:.78rem;font-weight:700;color:var(--text-primary);line-height:1.2;}
.kpi-badge{font-size:.46rem;padding:2px 7px;border-radius:99px;font-family:'JetBrains Mono',monospace;white-space:nowrap;flex-shrink:0;}
.kpi-up  {background:rgba(0,255,198,.1);color:var(--green);border:1px solid rgba(0,255,198,.18);}
.kpi-warn{background:rgba(255,209,102,.1);color:var(--gold);border:1px solid rgba(255,209,102,.18);}
.kpi-down{background:rgba(255,107,107,.1);color:var(--red);border:1px solid rgba(255,107,107,.18);}

/* sidebar nav */
.sb-nav .stButton button{
  background:rgba(255,255,255,.018) !important;border:1px solid var(--glass-border) !important;
  color:var(--text-muted) !important;border-radius:10px !important;font-size:.72rem !important;
  margin-bottom:5px !important;transition:all .15s !important;font-weight:500 !important;
  text-align:left !important; padding:.5rem .7rem !important;
}
.sb-nav .stButton button:hover{
  background:rgba(79,140,255,.06) !important;border-color:rgba(79,140,255,.22) !important;
  color:var(--blue) !important;transform:translateX(2px) !important;
}

/* ══ DOCK SEAM ══ */
.dock-seam{display:flex;align-items:center;gap:10px;margin:1.3rem 0 1rem;}
.dock-seam::before,.dock-seam::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(79,140,255,.18),transparent);}
.dock-seam-label{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--text-muted);letter-spacing:2.5px;text-transform:uppercase;white-space:nowrap;}

/* ══ REPORT DOCK ══ */
.gen-banner{
  border-radius:20px; padding:1.4rem 1.6rem; margin:.4rem 0 .7rem;
  position:relative; overflow:hidden;
  background:linear-gradient(135deg, rgba(255,209,102,.08) 0%, rgba(255,107,107,.05) 30%, rgba(79,140,255,.07) 65%, rgba(0,212,255,.05) 100%);
  border:1px solid rgba(255,209,102,.2);
  animation:slideUp .5s ease both;
}
.gen-banner::before{
  content:''; position:absolute; top:-60px; right:-40px;
  width:220px;height:220px;border-radius:50%;
  background:radial-gradient(circle, rgba(255,209,102,.1) 0%, transparent 65%);
  pointer-events:none;
}
.gen-eyebrow{
  font-family:'JetBrains Mono',monospace;font-size:.52rem;color:var(--gold);
  letter-spacing:2px;text-transform:uppercase;margin-bottom:.4rem;
  display:flex;align-items:center;gap:6px;position:relative;z-index:1;
}
.gen-eyebrow::before{content:'◆';font-size:.42rem;animation:pulse 2s infinite;}
.gen-title{font-size:1.05rem;font-weight:900;color:var(--text-primary);margin-bottom:.3rem;letter-spacing:-.4px;position:relative;z-index:1;}
.gen-sub{font-size:.78rem;color:var(--text-muted);line-height:1.65;margin-bottom:1rem;position:relative;z-index:1;}
.gen-features{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:1.1rem;position:relative;z-index:1;}
.gen-feat{font-size:.65rem;padding:3px 10px;border-radius:99px;font-weight:500;}
.gf-blue  {background:var(--blue-d); border:1px solid rgba(79,140,255,.22); color:var(--blue);}
.gf-cyan  {background:var(--cyan-d); border:1px solid rgba(0,212,255,.2);   color:var(--cyan);}
.gf-green {background:var(--green-d);border:1px solid rgba(0,255,198,.18); color:var(--green);}
.gf-gold  {background:var(--gold-d); border:1px solid rgba(255,209,102,.2);color:var(--gold);}
.gf-purple{background:var(--purple-d);border:1px solid rgba(123,97,255,.2); color:var(--purple);}

.btn-generate button{
  background:linear-gradient(135deg, #4F8CFF 0%, #7B61FF 50%, #00D4FF 100%) !important;
  background-size:200% auto !important; animation:morphGrad 4s ease infinite !important;
  border:none !important; color:#fff !important;
  box-shadow:0 4px 22px rgba(79,140,255,.35), 0 0 0 1px rgba(255,255,255,.08) inset !important;
  border-radius:12px !important; font-weight:800 !important; font-size:.84rem !important;
  transition:all .2s !important;
}
.btn-generate button:hover{transform:translateY(-2px) !important;box-shadow:0 8px 32px rgba(79,140,255,.5) !important;}

.btn-pdf button{
  background:linear-gradient(135deg, #FFD166 0%, #FF9F43 100%) !important;
  border:none !important; color:#0A0D1C !important;
  box-shadow:0 4px 18px rgba(255,209,102,.28) !important;
  border-radius:12px !important; font-weight:800 !important; font-size:.84rem !important;
  transition:all .2s !important;
}
.btn-pdf button:hover{transform:translateY(-2px) !important;box-shadow:0 8px 28px rgba(255,209,102,.45) !important;}

.btn-clear button{
  background:var(--red-d) !important;
  border:1px solid rgba(255,107,107,.2) !important; color:var(--red) !important;
  border-radius:12px !important; font-size:.82rem !important;
  font-weight:600 !important; transition:all .2s !important;
}
.btn-clear button:hover{background:rgba(255,107,107,.14) !important;border-color:rgba(255,107,107,.38) !important;}

.stDownloadButton button{
  background:linear-gradient(135deg, #00FFC6, #00D4FF) !important;
  border:none !important; color:#060810 !important; font-weight:800 !important;
  border-radius:12px !important; font-size:.84rem !important;
  box-shadow:0 4px 20px rgba(0,255,198,.22) !important;
}
.stDownloadButton button:hover{transform:translateY(-2px) !important;}

/* ── PROGRESS STEPS ── */
.prog-wrap{
  background:rgba(10,13,28,.85); border:1px solid var(--glass-border);
  border-radius:14px; padding:.85rem 1rem; animation:slideUp .3s ease both;
}
.prog-title{font-family:'JetBrains Mono',monospace;font-size:.58rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.6rem;}
.prog{display:flex;flex-direction:column;gap:.35rem;}
.pstep{display:flex;align-items:center;gap:9px;font-family:'JetBrains Mono',monospace;font-size:.61rem;}
.picon{width:18px;height:18px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.53rem;flex-shrink:0;}
.p-done{background:var(--green-d);color:var(--green);border:1px solid rgba(0,255,198,.2);}
.p-active{background:var(--blue-d);color:var(--blue);border:1px solid rgba(79,140,255,.3);animation:glow 1s infinite;}
.p-wait{background:rgba(255,255,255,.04);color:var(--text-muted);border:1px solid var(--glass-border);}
.pl-done{color:var(--green);}.pl-active{color:var(--blue);}.pl-wait{color:var(--text-muted);}

/* ── REPORT CARD ── */
.report-card{
  border-radius:18px; border:1px solid rgba(255,209,102,.1);
  background:linear-gradient(135deg, rgba(11,15,32,.97), rgba(8,11,25,.95));
  padding:1.2rem 1.4rem; margin-top:.6rem; margin-bottom:1.2rem;
  animation:slideUp .4s ease both; position:relative; overflow:hidden;
}
.report-card::before{
  content:''; position:absolute; top:0; left:0; right:0; height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,209,102,.25),transparent);
}
.rh{display:flex;align-items:center;justify-content:space-between;margin-bottom:.8rem;padding-bottom:.6rem;border-bottom:1px solid var(--glass-border);}
.rh-left{display:flex;align-items:center;gap:9px;}
.rh-icon{
  width:30px;height:30px;border-radius:8px;flex-shrink:0;
  background:linear-gradient(135deg,rgba(255,209,102,.18),rgba(255,159,67,.12));
  border:1px solid rgba(255,209,102,.18);
  display:flex;align-items:center;justify-content:center;font-size:.8rem;
}
.rh-title{font-size:.88rem;font-weight:800;color:var(--text-primary);}
.rh-meta{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--text-muted);margin-top:1px;}
.conf-row{display:flex;align-items:center;gap:8px;}
.conf-track{flex:1;height:3px;background:rgba(255,255,255,.05);border-radius:99px;overflow:hidden;}
.conf-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--cyan));}
.conf-txt{font-family:'JetBrains Mono',monospace;font-size:.49rem;color:var(--text-muted);}

.rsec{font-size:.82rem;line-height:1.8;color:var(--text-secondary);}
.rsec strong{color:var(--text-primary);}
.rsec table{width:100%;border-collapse:collapse;font-size:.77rem;margin:.5rem 0;}
.rsec th{background:var(--blue-d);color:var(--cyan);padding:.38rem .72rem;font-family:'JetBrains Mono',monospace;font-size:.51rem;text-transform:uppercase;letter-spacing:.7px;border:1px solid rgba(255,255,255,.05);text-align:left;}
.rsec td{padding:.3rem .72rem;border:1px solid rgba(255,255,255,.04);}
.rsec tr:nth-child(even) td{background:rgba(255,255,255,.01);}
.rsec tr.top td{color:var(--green);font-weight:600;}
.rsec tr.alert td{color:var(--red);}
.rsec tr.warn td{color:var(--gold);}

details{
  background:rgba(255,255,255,.012) !important;border:1px solid var(--glass-border) !important;
  border-radius:11px !important; margin-bottom:.4rem !important; overflow:hidden !important;
}
details summary{
  font-family:'JetBrains Mono',monospace !important; font-size:.63rem !important; color:var(--cyan) !important;
  padding:.5rem .8rem !important; cursor:pointer !important;
}
details[open] summary{border-bottom:1px solid var(--glass-border) !important; color:var(--gold) !important;}

/* ══ CHAT ══ */
.chat-section-label{
  font-family:'JetBrains Mono',monospace;font-size:.6rem;color:var(--text-muted);
  letter-spacing:2.5px;text-transform:uppercase;margin:.3rem 0 .8rem;
  display:flex;align-items:center;gap:8px;
}
.chat-section-label::before{content:'◆';font-size:.5rem;color:var(--cyan);}

.cmsg{display:flex;gap:12px;animation:slideUp .25s ease both;margin-bottom:1.3rem;}
.cmsg.user{flex-direction:row-reverse;}

.cmsg-av{
  width:38px;height:38px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:.95rem;font-weight:700;margin-top:2px;
}
.av-ai{
  background:linear-gradient(135deg,rgba(79,140,255,.25),rgba(0,212,255,.2));
  border:1px solid rgba(0,212,255,.3);color:var(--cyan);
  animation:glowCyan 3.5s ease infinite;
}
.av-user{
  background:linear-gradient(135deg,rgba(79,140,255,.2),rgba(123,97,255,.15));
  border:1px solid rgba(79,140,255,.22);color:var(--blue);
}

.cmsg-body{flex:1;min-width:0;max-width:85%;}
.cmsg.user .cmsg-body{display:flex;flex-direction:column;align-items:flex-end;}

.bubble-user{
  background:linear-gradient(135deg,rgba(79,140,255,.15),rgba(123,97,255,.11));
  border:1px solid rgba(79,140,255,.22);
  border-radius:20px 5px 20px 20px;
  padding:.85rem 1.2rem;
  font-size:1rem; color:var(--text-primary); line-height:1.7;
  display:inline-block;max-width:100%;word-break:break-word;
}

.bubble-ai{
  background:rgba(10,13,28,.88);
  border:1px solid rgba(79,140,255,.1);
  border-radius:5px 20px 20px 20px;
  padding:1rem 1.3rem;
  font-size:1rem; color:var(--text-secondary); line-height:1.85;
  position:relative;overflow:hidden;word-break:break-word;
}
.bubble-ai::before{
  content:''; position:absolute; top:0; left:0; right:0; height:1px;
  background:linear-gradient(90deg,transparent,rgba(0,212,255,.28),transparent);
}
.bubble-ai strong,.bubble-user strong{color:var(--text-primary);font-weight:700;}
.bubble-ai em{color:var(--cyan);font-style:normal;}
.bubble-ai table{width:100%;border-collapse:collapse;margin:.7rem 0;font-size:.88rem;}
.bubble-ai th{
  background:var(--blue-d);color:var(--cyan);
  font-family:'JetBrains Mono',monospace;font-size:.56rem;
  text-transform:uppercase;letter-spacing:.7px;
  padding:.42rem .8rem;text-align:left;border:1px solid rgba(255,255,255,.05);
}
.bubble-ai td{padding:.34rem .8rem;border:1px solid rgba(255,255,255,.04);color:var(--text-secondary);}
.bubble-ai tr:nth-child(even) td{background:rgba(255,255,255,.012);}
.bubble-ai tr.top td{color:var(--green);font-weight:600;}
.bubble-ai tr.alert td{color:var(--red);}
.bubble-ai tr.warn td{color:var(--gold);}

.cmsg-ts{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--text-muted);margin-top:5px;padding:0 2px;}
.cmsg.user .cmsg-ts{text-align:right;}

.typing-bubble{
  background:rgba(10,13,28,.88);border:1px solid rgba(79,140,255,.1);
  border-radius:5px 20px 20px 20px;
  padding:.8rem 1.2rem;display:inline-flex;align-items:center;gap:9px;
}
.tdot{width:9px;height:9px;border-radius:50%;background:var(--blue);animation:bounce3 1.1s ease infinite;}
.tdot:nth-child(2){animation-delay:.14s;background:var(--purple);}
.tdot:nth-child(3){animation-delay:.28s;background:var(--cyan);}
.typing-txt{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--text-muted);}

.sug-wrap{margin:.5rem 0 1rem 50px;animation:slideUp .3s .1s ease both;}
.sug-label{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.8px;margin-bottom:.4rem;}
.sq-grid .stButton button{
  background:var(--blue-d) !important;border:1px solid rgba(79,140,255,.18) !important;
  color:#A8C5FF !important;border-radius:9px !important;font-size:.74rem !important;
  font-weight:500 !important;text-align:left !important;padding:.5rem .75rem !important;
  transition:all .15s !important;
}
.sq-grid .stButton button:hover{background:rgba(79,140,255,.16) !important;border-color:rgba(79,140,255,.4) !important;transform:translateY(-1px) !important;}

.stChatInput>div{
  background:rgba(8,11,24,.92) !important;
  border:1px solid rgba(79,140,255,.18) !important;
  border-radius:16px !important; backdrop-filter:blur(20px) !important;
  transition:all .2s !important;
}
.stChatInput>div:focus-within{
  border-color:rgba(79,140,255,.45) !important;
  box-shadow:0 0 30px rgba(79,140,255,.1) !important;
}
.stChatInput textarea{color:var(--text-primary) !important;font-family:'Manrope',sans-serif !important;font-size:1rem !important;}

.bot-nav .stButton button{
  background:rgba(255,255,255,.018) !important;border:1px solid var(--glass-border) !important;
  color:var(--text-muted) !important;border-radius:10px !important;font-size:.72rem !important;
  font-weight:500 !important;transition:all .15s !important;
}
.bot-nav .stButton button:hover{background:rgba(79,140,255,.06) !important;border-color:rgba(79,140,255,.22) !important;color:var(--blue) !important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# GUARD
# ══════════════════════════════════════════════════════════════════
if "df" not in st.session_state:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;animation:slideUp .5s ease both;">
      <div style="font-size:3rem;margin-bottom:1rem;filter:drop-shadow(0 0 20px rgba(79,140,255,.4));">◆</div>
      <div style="font-size:1.2rem;font-weight:900;color:#FFFFFF;margin-bottom:.5rem;letter-spacing:-.4px;">ARIA needs your data</div>
      <div style="font-size:.82rem;color:#8A97B5;margin-bottom:1.6rem;">Upload an Excel sales file to unlock the full AI intelligence dashboard.</div>
    </div>
    """, unsafe_allow_html=True)
    c = st.columns([1, 2, 1])[1]
    with c:
        if st.button("← Upload Dataset", use_container_width=True):
            st.switch_page("app.py")
    st.stop()

df       = st.session_state["df"]
filename = st.session_state.get("filename", "dataset.xlsx")

if st.session_state.get("_last_seen_file") != filename:
    st.session_state["chat_history"] = []
    st.session_state["bi_report_txt"] = None
    st.session_state["_last_seen_file"] = filename
    st.cache_data.clear()

# ══════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def compute_stats(_key):
    return (
        get_salesperson_totals(df),
        get_daily_totals(df),
        get_category_totals(df),
        get_zero_sales(df),
        get_data_summary_for_ai(df),
    )

_key = f"{filename}_{df.shape}_{list(df.columns)}"
totals, daily, cat_totals, zero_list, data_summary = compute_stats(_key)

total_rev      = float(totals["Total"].sum())     if not totals.empty else 0.0
mtd            = get_mtd_total(df)
ytd            = get_ytd_total(df)
top_seller     = totals.iloc[0]["Salesperson"]    if not totals.empty else "—"
top_val        = float(totals.iloc[0]["Total"])   if not totals.empty else 0.0
avg_daily      = float(daily.mean())              if len(daily) > 0   else 0.0
active_sellers = int((totals["Total"] > 0).sum()) if not totals.empty else 0
rev_per_seller = (total_rev / active_sellers)     if active_sellers   else 0
top_multiplier = (top_val / rev_per_seller)       if rev_per_seller   else 0
mtd_display    = f"₹{mtd:,.0f}" if mtd > 0 else "N/A"
mtd_for_ai     = f"₹{mtd:,.0f}" if mtd > 0 else "Not available"

never_sold, bad_day = [], []
for s in zero_list:
    if not totals.empty:
        row = totals[totals["Salesperson"] == s]
        if not row.empty and float(row.iloc[0]["Total"]) == 0:
            never_sold.append(s)
        else:
            bad_day.append(s)

zero_rate   = (len(never_sold) / active_sellers * 100) if active_sellers else 0
alert_count = len(never_sold) + len(bad_day)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
for k, v in {"chat_history": [], "bi_report_txt": None, "_pending_ai": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

msg_count = sum(1 for m in st.session_state["chat_history"] if m["role"] == "user")

# ══════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = f"""
════════════════════════════════════════════════════════
ARIA — SALES INTELLIGENCE AI COPILOT
Homeopathic Pharmaceutical Company · Internal BI Platform
════════════════════════════════════════════════════════

YOU ARE: ARIA (Analytical Revenue Intelligence Assistant)
A precision-built AI engine for pharmaceutical sales intelligence.
Not a general assistant. Every response drives a business decision.

ACTIVE DATASET: {filename}
GENERATED: {datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")}

IDENTITY & PERSONA:
- Senior sales intelligence analyst, 15 years in pharmaceutical distribution.
- You know every salesperson by name. Direct. Evidence-based. Opinionated.
- You never say "Great question!", "As an AI", "I hope this helps".
- You NEVER repeat the user's question. START immediately with the first insight.

RESPONSE RULES:
- Greetings: 2 sentences max
- Single fact: 3 lines max
- Comparisons: HTML table FIRST, then 2-3 key callouts
- Full analysis: complete detail, nothing truncated

NEVER DO:
- Round numbers unless asked
- Give vague statements ("some sellers", "a few")
- Write long paragraphs — use tables, bullets, structure
- Fabricate data beyond the dataset

ALWAYS DO:
- NAME SPECIFIC PEOPLE — never "a salesperson", always the real name
- Contextualize every number (vs team avg, as % of total)
- Flag alerts proactively when relevant

HTML FORMATTING:
Tables: <table><tr><th>Col</th></tr><tr class="top"><td>Best</td></tr><tr class="alert"><td>Critical</td></tr><tr class="warn"><td>Warning</td></tr></table>
Section headers: <strong>── SECTION NAME ──</strong>
Currency: ₹ Indian format (₹3,47,594)

PERFORMANCE THRESHOLDS:
- Star Performer: > 130% of team avg → highlight
- Underperformer: < 80% of team avg → flag
- Never Sold: ₹0 total → CRITICAL
- Bad Day: ₹0 on one day → monitor

LIVE DATA:
File: {filename}
{data_summary}

KEY NUMBERS:
  Total Revenue  : ₹{total_rev:,.0f}
  MTD Revenue    : {mtd_for_ai}
  YTD Revenue    : ₹{ytd:,.0f}
  Daily Average  : ₹{avg_daily:,.0f}
  Top Seller     : {top_seller} (₹{top_val:,.0f})
  Active Sellers : {active_sellers}
  Rev / Seller   : ₹{rev_per_seller:,.0f}
  Top Multiplier : {top_multiplier:.2f}× average
  Zero-Sale Rate : {zero_rate:.1f}%

ALERTS:
  Never Sold (₹0 total) : {', '.join(never_sold) if never_sold else 'None'}
  Had Bad Day (₹0 day)  : {', '.join(bad_day) if bad_day else 'None'}

SUGGESTED FOLLOW-UPS:
After EVERY response (except greetings), append EXACTLY:
<div id="aria-sq" style="display:none">SUGGESTED:
Q1: [specific follow-up based on what you just answered]
Q2: [dig deeper question]
Q3: [different angle or action-focused]
</div>
Keep each question under 60 chars. Never show this block visually.

FULL REPORT (when requested):
Generate ALL 10 sections, no truncation:
1. EXECUTIVE SUMMARY
2. KPI SCORECARD
3. SALESPERSON PERFORMANCE LEADERBOARD
4. CATEGORY REVENUE ANALYSIS
5. DAILY TREND ANALYSIS
6. ZERO-SALES & CRITICAL ALERTS
7. AI INSIGHT ENGINE — ROOT CAUSE ANALYSIS
8. GROWTH OPPORTUNITIES
9. STRATEGIC RECOMMENDATIONS
10. NEXT BEST ACTIONS (TODAY)
════════════════════════════════════════════════════════
"""

# ══════════════════════════════════════════════════════════════════
# AI HELPERS
# ══════════════════════════════════════════════════════════════════
def get_ai_response(user_text: str) -> str:
    groq_hist = []
    for m in st.session_state["chat_history"][-10:]:
        content = re.sub(r'<div id="aria-sq".*?</div>', '', m["content"], flags=re.DOTALL).strip()
        if len(content) > 400:
            content = content[:400] + "…"
        groq_hist.append({"role": m["role"], "content": content})
    try:
        return ask_groq(user_text, SYSTEM_PROMPT, chat_history=groq_hist)
    except Exception as e:
        return f'<span style="color:#FF6B6B;font-family:JetBrains Mono,monospace;font-size:.78rem;">⚠ ARIA error: {str(e)[:200]}</span>'

def extract_sqs(text: str):
    match = re.search(r'<div id="aria-sq"[^>]*>SUGGESTED:\s*(.*?)</div>', text, re.DOTALL)
    if not match:
        return []
    return [q.strip() for q in re.findall(r'Q\d+:\s*(.+)', match.group(1)) if q.strip()]

def strip_sq(text: str) -> str:
    return re.sub(r'<div id="aria-sq".*?</div>', '', text, flags=re.DOTALL).strip()

def render_message_html(role: str, content: str, ts: str) -> str:
    if role == "user":
        safe_content = content.replace("\n", "<br>")
        return (
            f'<div class="cmsg user">'
            f'<div class="cmsg-body">'
            f'<div class="bubble-user">{safe_content}</div>'
            f'<div class="cmsg-ts">{ts}</div>'
            f'</div>'
            f'<div class="cmsg-av av-user">👤</div>'
            f'</div>'
        )
    clean     = strip_sq(content)
    safe_clean = clean.replace("\n", "<br>")
    return (
        f'<div class="cmsg">'
        f'<div class="cmsg-av av-ai">◆</div>'
        f'<div class="cmsg-body">'
        f'<div class="bubble-ai">{safe_clean}</div>'
        f'<div class="cmsg-ts">ARIA · {ts}</div>'
        f'</div>'
        f'</div>'
    )

# ══════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div class="tb-left">
    <div class="tb-logo">A</div>
    <span class="tb-name">ARIA</span>
    <span class="tb-tag">SALES INTELLIGENCE</span>
  </div>
  <div class="tb-right">
    <span class="tb-pill">💬 {msg_count} msgs</span>
    <span class="tb-pill">{'🚨 ' + str(alert_count) + ' alerts' if alert_count else '✅ Clean'}</span>
    <span class="tb-live"><span class="tb-dot"></span>LLaMA 3.3 · Live</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR — redesigned with health ring, mini leaderboard,
#           categorised quick-ask, session stats, KPI badges
# ══════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Brand ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-brand-logo">A</div>
      <div>
        <div class="sb-brand-name">ARIA</div>
        <div class="sb-brand-sub">Sales Intelligence Copilot</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Team Health Ring ──────────────────────────────────────────
    if not totals.empty:
        never_pct    = len(never_sold) / max(active_sellers, 1)
        bad_pct      = len(bad_day)    / max(active_sellers, 1)
        health_raw   = 100 - (never_pct * 60 + bad_pct * 20)
        health_raw  += min(20, (top_multiplier / 3) * 10)
        health_score = max(0, min(100, int(health_raw)))
    else:
        health_score = 0

    if health_score >= 80:
        ring_color, mood_label = "#00FFC6", "Strong"
    elif health_score >= 55:
        ring_color, mood_label = "#FFD166", "Monitor"
    else:
        ring_color, mood_label = "#FF6B6B", "Critical"

    # ring circumference = 2π × 21 ≈ 131.9
    offset = 131.9 - (131.9 * health_score / 100)

    st.markdown(f"""
    <div class="sec">⚡ Team Health</div>
    <div class="health-ring-wrap">
      <svg width="54" height="54" viewBox="0 0 54 54" style="flex-shrink:0;">
        <circle cx="27" cy="27" r="21" fill="none"
          stroke="rgba(255,255,255,.07)" stroke-width="5"/>
        <circle cx="27" cy="27" r="21" fill="none"
          stroke="{ring_color}" stroke-width="5"
          stroke-dasharray="131.9"
          stroke-dashoffset="{offset:.1f}"
          stroke-linecap="round"
          transform="rotate(-90 27 27)"
          style="transition:stroke-dashoffset .6s ease;"/>
        <text x="27" y="32" text-anchor="middle"
          fill="#FFFFFF" font-size="11" font-weight="700"
          font-family="Manrope,sans-serif">{health_score}</text>
      </svg>
      <div>
        <div class="health-label">Performance Score</div>
        <div class="health-score" style="color:{ring_color};">{health_score}/100</div>
        <div class="health-mood" style="color:{ring_color};">
          <span class="mood-dot" style="background:{ring_color};box-shadow:0 0 6px {ring_color};"></span>
          {mood_label} · {active_sellers} active sellers
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Mini Leaderboard ──────────────────────────────────────────
    st.markdown('<div class="sec">🏆 Top Sellers</div>', unsafe_allow_html=True)
    if not totals.empty:
        lb_html = '<div class="mini-lb">'
        for i, row in enumerate(totals.head(3).itertuples()):
            is_gold   = (i == 0)
            gold_cls  = "gold" if is_gold else ""
            row_cls   = "mlb-gold" if is_gold else ""
            initial   = row.Salesperson[0].upper() if row.Salesperson else "?"
            rank_lbl  = "#1" if is_gold else f"#{i + 1}"
            val_lakh  = row.Total / 1e5
            lb_html += (
                f'<div class="mlb-row {row_cls}">'
                f'<div class="mlb-rank {gold_cls}">{rank_lbl}</div>'
                f'<div class="mlb-av {gold_cls}">{initial}</div>'
                f'<div class="mlb-name">{row.Salesperson}</div>'
                f'<div class="mlb-val">₹{val_lakh:.1f}L</div>'
                f'</div>'
            )
        lb_html += '</div>'
        st.markdown(lb_html, unsafe_allow_html=True)

    # ── Quick Ask — categorised tiles ─────────────────────────────
    # (icon, label, css_color_idx)
    QUICK_CATEGORIES = {
        "📊 Analysis": [
            ("📊", "Revenue\nBreakdown", 0),
            ("📈", "Daily\nTrend",       4),
            ("🗂️", "Category\nHealth",  0),
            ("📋", "Compare\nSellers",   3),
        ],
        "🏅 Performance": [
            ("🏆", "Top\nPerformer",     1),
            ("💡", "Growth\nIdeas",      5),
            ("🎯", "Focus\nToday",       0),
            ("📦", "Weakest\nCategory",  1),
        ],
        "🚨 Alerts & Action": [
            ("🚨", "Zero-Sales\nAlerts", 2),
            ("⚠️", "Biggest\nRisks",    2),
        ],
    }

    QUICK_FULL = {
        "Revenue\nBreakdown": "Full revenue breakdown",
        "Top\nPerformer":     "Top performer deep dive",
        "Zero-Sales\nAlerts": "Zero-sales alert summary",
        "Compare\nSellers":   "Compare all sellers",
        "Category\nHealth":   "Category performance",
        "Daily\nTrend":       "Daily trend analysis",
        "Growth\nIdeas":      "Top 3 growth opportunities",
        "Biggest\nRisks":     "What are the biggest risks?",
        "Focus\nToday":       "What should I focus on today?",
        "Weakest\nCategory":  "Which category is weakest?",
    }

    st.markdown('<div class="sec">⚡ Quick Ask</div>', unsafe_allow_html=True)

    for cat_name, tiles in QUICK_CATEGORIES.items():
        st.markdown(f'<div class="qcat-label">{cat_name}</div>', unsafe_allow_html=True)
        pairs = [tiles[i:i + 2] for i in range(0, len(tiles), 2)]
        for pair in pairs:
            cols = st.columns(2)
            for col, (icon, label, color_idx) in zip(cols, pair):
                with col:
                    st.markdown(
                        f'<div class="qtile-wrap qtile-{color_idx}">',
                        unsafe_allow_html=True,
                    )
                    btn_key = f"qs_{cat_name}_{label}"
                    if st.button(
                        f"{icon}\n{label}",
                        key=btn_key,
                        use_container_width=True,
                    ):
                        full_q = QUICK_FULL.get(label, label)
                        now_ts = datetime.datetime.now().strftime("%I:%M %p")
                        st.session_state["chat_history"].append(
                            {"role": "user", "content": full_q, "ts": now_ts}
                        )
                        st.session_state["_pending_ai"] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # ── Session Stats ─────────────────────────────────────────────
    msg_q   = sum(1 for m in st.session_state["chat_history"] if m["role"] == "user")
    msg_a   = sum(1 for m in st.session_state["chat_history"] if m["role"] == "assistant")
    has_rpt = 1 if st.session_state.get("bi_report_txt") else 0

    st.markdown(f"""
    <div class="sec">📡 This Session</div>
    <div class="sess-stats">
      <div class="sess-card">
        <div class="sess-num">{msg_q}</div>
        <div class="sess-lbl">Questions</div>
      </div>
      <div class="sess-card">
        <div class="sess-num" style="color:#00D4FF;">{msg_a}</div>
        <div class="sess-lbl">Insights</div>
      </div>
      <div class="sess-card">
        <div class="sess-num" style="color:#FFD166;">{has_rpt}</div>
        <div class="sess-lbl">Reports</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Live KPIs ─────────────────────────────────────────────────
    st.markdown('<div class="sec">📊 Live KPIs</div>', unsafe_allow_html=True)

    kpi_rows = [
        ("Total Revenue", f"₹{total_rev:,.0f}",                                    "up",   "Active"),
        ("MTD Revenue",   mtd_display,                                               "up",   "Strong"),
        ("Top Seller",    top_seller,                                                "up",   f"₹{top_val / 1e5:.1f}L"),
        ("Daily Average", f"₹{avg_daily:,.0f}",                                     "up",   "Avg"),
        ("Zero Alerts",
         f"{len(never_sold)} never · {len(bad_day)} bad day",
         "warn" if alert_count else "up",
         "Monitor" if alert_count else "✅ Clean"),
    ]

    kpi_html = ""
    for lbl, val, badge_type, badge_txt in kpi_rows:
        kpi_html += (
            f'<div class="sb-kpi">'
            f'<div>'
            f'<div class="sb-kpi-label">{lbl}</div>'
            f'<div class="sb-kpi-value">{val}</div>'
            f'</div>'
            f'<span class="kpi-badge kpi-{badge_type}">{badge_txt}</span>'
            f'</div>'
        )
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Navigate ──────────────────────────────────────────────────
    st.markdown('<div class="sec">🧭 Navigate</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-nav">', unsafe_allow_html=True)
    if st.button("📊  Dashboard",  use_container_width=True, key="sb_dash"):
        st.switch_page("pages/1_Dashboard.py")
    if st.button("📤  New Upload",  use_container_width=True, key="sb_upload"):
        st.switch_page("app.py")
    if st.button("🗑️  Clear Chat", use_container_width=True, key="sb_clear"):
        st.session_state["chat_history"] = []
        st.session_state["bi_report_txt"] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin:.6rem .5rem 0;padding:.5rem .7rem;
      background:rgba(255,255,255,.018);border:1px solid var(--glass-border);
      border-radius:10px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:.48rem;
        color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">
        Active File
      </div>
      <div style="font-size:.68rem;color:var(--text-secondary);word-break:break-all;">
        {filename}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# REPORT DOCK
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gen-banner">
  <div class="gen-eyebrow">ARIA Intelligence Engine</div>
  <div class="gen-title">📊 Generate the Report</div>
  <div class="gen-sub">
    One click → comprehensive AI-powered analysis of your entire dataset.<br>
    KPI scorecard · leaderboard · trends · alerts · root cause · action plan.
  </div>
  <div class="gen-features">
    <span class="gen-feat gf-blue">📊 10 Sections</span>
    <span class="gen-feat gf-cyan">🧠 AI Root Cause</span>
    <span class="gen-feat gf-green">🏆 Leaderboard</span>
    <span class="gen-feat gf-gold">💡 Growth Ops</span>
    <span class="gen-feat gf-purple">📈 Trend Analysis</span>
  </div>
</div>
""", unsafe_allow_html=True)

col_g1, col_g2, col_g3 = st.columns([2.2, 1.8, .8])
with col_g1:
    st.markdown('<div class="btn-generate">', unsafe_allow_html=True)
    gen_report = st.button("🚀 Generate Full Report", use_container_width=True, key="gen_btn")
    st.markdown('</div>', unsafe_allow_html=True)
with col_g2:
    st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
    dl_pdf = st.button("📄 Export PDF (w/ chat)", use_container_width=True, key="pdf_btn")
    st.markdown('</div>', unsafe_allow_html=True)
with col_g3:
    st.markdown('<div class="btn-clear">', unsafe_allow_html=True)
    if st.button("🗑️", use_container_width=True, key="clr_rpt"):
        st.session_state["bi_report_txt"] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

REPORT_STEPS = [
    ("🔍", "Reading salesperson data…"),
    ("📊", "Computing category splits…"),
    ("📈", "Analysing daily trends…"),
    ("🧠", "Running AI insight engine…"),
    ("💡", "Building recommendations…"),
    ("✅", "Finalising report…"),
]
PDF_STEPS = [
    ("🎨", "Building cover page…"),
    ("📋", "Compiling KPI tables…"),
    ("📊", "Rendering charts…"),
    ("💬", "Embedding chat transcript…"),
    ("🧠", "Embedding AI report…"),
    ("📄", "Exporting PDF bytes…"),
]

def render_steps(steps, done_count, title="Processing"):
    rows = ""
    for i, (icon, label) in enumerate(steps):
        if i < done_count:
            ic, lc, di = "p-done",   "pl-done",   "✓"
        elif i == done_count:
            ic, lc, di = "p-active", "pl-active", icon
        else:
            ic, lc, di = "p-wait",   "pl-wait",   icon
        rows += (
            f'<div class="pstep">'
            f'<div class="picon {ic}">{di}</div>'
            f'<span class="{lc}">{label}</span>'
            f'</div>'
        )
    return (
        f'<div class="prog-wrap">'
        f'<div class="prog-title">{title}</div>'
        f'<div class="prog">{rows}</div>'
        f'</div>'
    )

if gen_report:
    FULL_REPORT_PROMPT = f"""
Generate the COMPLETE ARIA Intelligence Report.
Date: {datetime.date.today().strftime('%d %B %Y')}
Currency: ₹ Indian lakh format.
Tables: HTML with class="top"/"alert"/"warn" on rows.
Section headers: <strong>── N. SECTION NAME ──</strong>

ALL 10 SECTIONS REQUIRED:
1. EXECUTIVE SUMMARY
2. KPI SCORECARD
3. SALESPERSON PERFORMANCE LEADERBOARD
4. CATEGORY REVENUE ANALYSIS
5. DAILY TREND ANALYSIS
6. ZERO-SALES & CRITICAL ALERTS
7. AI INSIGHT ENGINE — ROOT CAUSE ANALYSIS
8. GROWTH OPPORTUNITIES
9. STRATEGIC RECOMMENDATIONS
10. NEXT BEST ACTIONS (TODAY)

Each section must be fully detailed. Every person named. Every number contextualized.
Minimum 100 words per section. Tables mandatory in sections 2,3,4,6,8,9,10.
"""
    prog_ph = st.empty()
    for si in range(len(REPORT_STEPS)):
        prog_ph.markdown(
            render_steps(REPORT_STEPS, si, "Generating ARIA Report"),
            unsafe_allow_html=True,
        )
        time.sleep(0.28)

    try:
        report_txt = ask_groq(FULL_REPORT_PROMPT, SYSTEM_PROMPT, chat_history=[])
    except Exception as e:
        report_txt = f'<span style="color:#FF6B6B;">⚠ Report generation failed: {str(e)[:300]}</span>'

    prog_ph.markdown(
        render_steps(REPORT_STEPS, len(REPORT_STEPS), "Generating ARIA Report"),
        unsafe_allow_html=True,
    )
    time.sleep(0.3)
    prog_ph.empty()
    st.session_state["bi_report_txt"] = report_txt
    st.rerun()

# ── DISPLAY REPORT ─────────────────────────────────────────────────
if st.session_state.get("bi_report_txt"):
    rpt = st.session_state["bi_report_txt"]

    st.markdown(f"""
    <div class="report-card">
      <div class="rh">
        <div class="rh-left">
          <div class="rh-icon">🤖</div>
          <div>
            <div class="rh-title">ARIA Intelligence Report</div>
            <div class="rh-meta">Generated {datetime.date.today().strftime('%d %B %Y')} · LLaMA 3.3-70B via Groq</div>
          </div>
        </div>
      </div>
      <div class="conf-row">
        <div class="conf-track"><div class="conf-fill" style="width:94%;"></div></div>
        <div class="conf-txt">94% Confidence · Full dataset analysis</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    sec_re = re.compile(r'(<strong>──\s*\d+\..*?──</strong>)', re.DOTALL)
    parts  = sec_re.split(rpt)

    if len(parts) > 1:
        intro = parts[0].strip()
        if intro:
            st.markdown(
                f'<div class="rsec" style="padding:.5rem 0;">{intro}</div>',
                unsafe_allow_html=True,
            )
        i = 1
        while i < len(parts):
            header  = parts[i].strip()
            content = parts[i + 1].strip() if (i + 1) < len(parts) else ""
            clean_h = re.sub(r'<[^>]+>', '', header).strip().lstrip('─').strip()
            with st.expander(f"▸ {clean_h}", expanded=(i <= 3)):
                st.markdown(f'<div class="rsec">{content}</div>', unsafe_allow_html=True)
            i += 2
    else:
        st.markdown(f'<div class="rsec">{rpt}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# DOCK SEAM
# ══════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="dock-seam"><span class="dock-seam-label">Chat with ARIA</span></div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# WELCOME
# ══════════════════════════════════════════════════════════════════
if not st.session_state["chat_history"]:
    st.markdown(f"""
    <div style="border-radius:18px;padding:1.3rem 1.5rem;margin-bottom:1rem;
      border:1px solid rgba(79,140,255,.14);
      background:linear-gradient(135deg,rgba(79,140,255,.06),rgba(123,97,255,.04),rgba(0,212,255,.03));">
      <div style="font-size:1rem;font-weight:900;color:#FFFFFF;margin-bottom:.4rem;">
        ARIA — Sales Intelligence Copilot
      </div>
      <div style="font-size:.85rem;color:#8A97B5;line-height:1.7;">
        Analysing <strong style="color:#FFFFFF;">{filename}</strong> in real time.
        Ask anything about your sales data below, or use a Quick Ask tile in the sidebar.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CHAT CONVERSATION
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="chat-section-label">Conversation</div>', unsafe_allow_html=True)

for msg in st.session_state["chat_history"]:
    st.markdown(
        render_message_html(msg["role"], msg["content"], msg.get("ts", "")),
        unsafe_allow_html=True,
    )

if st.session_state["chat_history"]:
    last_msg = st.session_state["chat_history"][-1]
    if last_msg["role"] == "assistant":
        sqs = extract_sqs(last_msg["content"])
        if sqs:
            st.markdown(
                '<div class="sug-wrap"><div class="sug-label">Suggested follow-ups</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="sq-grid">', unsafe_allow_html=True)
            cols = st.columns(len(sqs))
            for ci, (col, sq) in enumerate(zip(cols, sqs)):
                with col:
                    if st.button(
                        sq,
                        key=f"sqb_{len(st.session_state['chat_history'])}_{ci}",
                        use_container_width=True,
                    ):
                        now_ts = datetime.datetime.now().strftime("%I:%M %p")
                        st.session_state["chat_history"].append(
                            {"role": "user", "content": sq, "ts": now_ts}
                        )
                        st.session_state["_pending_ai"] = True
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PENDING AI
# ══════════════════════════════════════════════════════════════════
if st.session_state["_pending_ai"]:
    st.session_state["_pending_ai"] = False
    last_q = st.session_state["chat_history"][-1]["content"]

    typing_ph = st.empty()
    typing_ph.markdown("""
    <div class="cmsg">
      <div class="cmsg-av av-ai">◆</div>
      <div class="cmsg-body">
        <div class="typing-bubble">
          <div class="tdot"></div><div class="tdot"></div><div class="tdot"></div>
          <span class="typing-txt">ARIA is thinking…</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    response = get_ai_response(last_q)
    typing_ph.empty()

    now_ts = datetime.datetime.now().strftime("%I:%M %p")
    st.session_state["chat_history"].append(
        {"role": "assistant", "content": response, "ts": now_ts}
    )
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# CHAT INPUT
# ══════════════════════════════════════════════════════════════════
user_input = st.chat_input("Ask ARIA anything about your sales data…")

if user_input:
    now_ts = datetime.datetime.now().strftime("%I:%M %p")
    st.session_state["chat_history"].append(
        {"role": "user", "content": user_input, "ts": now_ts}
    )
    st.session_state["_pending_ai"] = True
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# PDF BUILDER — fixed AI text section
# ══════════════════════════════════════════════════════════════════
def build_pdf(report_txt: str, fname: str, chat_log: list):
    import io as _io
    warns = []
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table,
            TableStyle, Image as RLImage, HRFlowable, PageBreak,
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError as ie:
        return None, f"Missing: {ie}. Run: pip install reportlab matplotlib"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    fp_reg   = os.path.join(base_dir, "..", "assets", "fonts", "DejaVuSans.ttf")
    fp_bold  = os.path.join(base_dir, "..", "assets", "fonts", "DejaVuSans-Bold.ttf")
    USE_DJ   = False
    if os.path.exists(fp_reg):
        try:
            pdfmetrics.registerFont(TTFont("DJ", fp_reg))
            if os.path.exists(fp_bold):
                pdfmetrics.registerFont(TTFont("DJB", fp_bold))
            USE_DJ = True
        except Exception as fe:
            warns.append(f"Font fallback: {fe}")
    F  = "DJ"  if USE_DJ else "Helvetica"
    FB = "DJB" if USE_DJ else "Helvetica-Bold"
    INR = "Rs."

    C_BG    = colors.HexColor("#050816")
    C_DARK  = colors.HexColor("#0D1225")
    C_PANEL = colors.HexColor("#111828")
    C_BLUE  = colors.HexColor("#4F8CFF")
    C_CYAN  = colors.HexColor("#00D4FF")
    C_GREEN = colors.HexColor("#00FFC6")
    C_GOLD  = colors.HexColor("#FFD166")
    C_RED   = colors.HexColor("#FF6B6B")
    C_TEXT  = colors.HexColor("#C8D4E8")
    C_WHITE = colors.HexColor("#FFFFFF")
    C_MUTED = colors.HexColor("#8A97B5")
    GRID    = colors.HexColor("#1A2242")

    def S(n, **kw):  return ParagraphStyle(n, fontName=F,  **kw)
    def SB(n, **kw): return ParagraphStyle(n, fontName=FB, **kw)

    s_h1       = SB("h1",    fontSize=11,  textColor=C_CYAN,  spaceBefore=14, spaceAfter=6)
    s_sec_hdr  = SB("sechdr",fontSize=9.5, textColor=C_GOLD,  spaceBefore=10, spaceAfter=4, leading=14)
    s_body     = S("body",   fontSize=8.5, textColor=C_TEXT,  leading=13, spaceAfter=3)
    s_sub      = S("sub",    fontSize=8,   textColor=C_MUTED, spaceAfter=3)
    s_chat_u   = S("chatu",  fontSize=8.5, textColor=C_GOLD,  leading=13, spaceAfter=2)
    s_chat_a   = S("chata",  fontSize=8.5, textColor=C_TEXT,  leading=13, spaceAfter=8)

    buf = _io.BytesIO()
    try:
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
            topMargin=1.6 * cm, bottomMargin=2.4 * cm,
        )
    except Exception as e:
        return None, f"PDF init failed: {e}"

    story = []
    W = A4[0] - 3.6 * cm

    # ── Cover ──────────────────────────────────────────────────────
    try:
        ct = Table(
            [[Paragraph("ARIA Intelligence Report",
                SB("ct", fontSize=18, textColor=C_WHITE, leading=22))]],
            colWidths=[W], rowHeights=[3.2 * cm],
        )
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), C_BLUE),
            ("LEFTPADDING", (0, 0), (0, 0), 18),
            ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ]))
        story += [
            ct,
            Spacer(1, .4 * cm),
            Paragraph(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}", s_sub),
            Paragraph(f"File: {fname}", s_sub),
            Spacer(1, .3 * cm),
            HRFlowable(width=W, thickness=1.5, color=C_BLUE, spaceAfter=10),
        ]
    except Exception as e:
        warns.append(f"Cover: {e}")

    # ── KPI Table ──────────────────────────────────────────────────
    try:
        story.append(Paragraph("Key Performance Indicators", s_h1))
        kd = [
            ["Metric",         "Value",                       "Metric",      "Value"],
            ["Total Revenue",  f"{INR}{total_rev:,.0f}",      "Daily Avg",   f"{INR}{avg_daily:,.0f}"],
            ["YTD Revenue",    f"{INR}{ytd:,.0f}",            "Top Seller",  top_seller],
            ["Active Sellers", str(active_sellers),           "Rev/Seller",  f"{INR}{rev_per_seller:,.0f}"],
            ["Never Sold",     str(len(never_sold)),          "Bad Day",     str(len(bad_day))],
            ["Top Value",      f"{INR}{top_val:,.0f}",        "Multiplier",  f"{top_multiplier:.2f}x avg"],
        ]
        cw = [W * .22, W * .28, W * .22, W * .28]
        kt = Table(kd, colWidths=cw)
        kt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0), C_CYAN),
            ("FONTNAME",      (0, 0), (-1, 0), FB),
            ("FONTNAME",      (0, 1), (-1, -1), F),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("TEXTCOLOR",     (0, 1), (-1, -1), C_WHITE),
            ("TEXTCOLOR",     (1, 1), (1, -1),  C_GREEN),
            ("TEXTCOLOR",     (3, 1), (3, -1),  C_GOLD),
            ("BACKGROUND",    (0, 2), (-1, 2),  C_PANEL),
            ("BACKGROUND",    (0, 4), (-1, 4),  C_PANEL),
            ("GRID",          (0, 0), (-1, -1), .3, GRID),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ]))
        story += [kt, Spacer(1, .5 * cm)]
    except Exception as e:
        warns.append(f"KPI: {e}")

    # ── Leaderboard ────────────────────────────────────────────────
    try:
        story.append(Paragraph("Salesperson Leaderboard", s_h1))
        if not totals.empty:
            t_sum = totals["Total"].sum()
            lh    = [["Rank", "Salesperson", "Revenue", "Share%", "vs Avg"]]
            lrows = []
            for i, rw in enumerate(totals.head(20).itertuples()):
                share = (rw.Total / t_sum * 100) if t_sum else 0
                vs    = ((rw.Total / rev_per_seller - 1) * 100) if rev_per_seller else 0
                lrows.append([
                    f"#{i + 1}",
                    rw.Salesperson,
                    f"{INR}{rw.Total:,.0f}",
                    f"{share:.1f}%",
                    f"+{vs:.0f}%" if vs >= 0 else f"{vs:.0f}%",
                ])
            lt = Table(lh + lrows, colWidths=[W * .09, W * .36, W * .24, W * .16, W * .15])
            lt.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), C_DARK),
                ("TEXTCOLOR",     (0, 0), (-1, 0), C_GOLD),
                ("FONTNAME",      (0, 0), (-1, 0), FB),
                ("FONTNAME",      (0, 1), (-1, -1), F),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("TEXTCOLOR",     (0, 1), (-1, -1), C_WHITE),
                ("TEXTCOLOR",     (2, 1), (2, -1),  C_GREEN),
                ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor("#071A0A")),
                ("GRID",          (0, 0), (-1, -1), .3, GRID),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ]))
            story.append(lt)
        story.append(PageBreak())
    except Exception as e:
        warns.append(f"Leaderboard: {e}")

    # ── Category Table ─────────────────────────────────────────────
    try:
        story.append(Paragraph("Category Performance", s_h1))
        if not cat_totals.empty:
            c_sum = float(cat_totals["Total"].sum())
            c_max = float(cat_totals["Total"].max())
            ch    = [["Category", "Revenue", "Share%", "Health"]]
            crows = []
            for rw in cat_totals.itertuples():
                sh = (rw.Total / c_sum * 100) if c_sum else 0
                r  = (rw.Total / c_max)       if c_max  else 0
                ht = "Strong" if r >= .6 else ("Moderate" if r >= .25 else "Low")
                crows.append([str(rw.Category), f"{INR}{rw.Total:,.0f}", f"{sh:.1f}%", ht])
            ctt = Table(ch + crows, colWidths=[W * .32, W * .28, W * .18, W * .22])
            ctt.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), C_DARK),
                ("TEXTCOLOR",     (0, 0), (-1, 0), C_CYAN),
                ("FONTNAME",      (0, 0), (-1, 0), FB),
                ("FONTNAME",      (0, 1), (-1, -1), F),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("TEXTCOLOR",     (0, 1), (-1, -1), C_WHITE),
                ("TEXTCOLOR",     (1, 1), (1, -1),  C_GREEN),
                ("GRID",          (0, 0), (-1, -1), .3, GRID),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ]))
            story.append(ctt)
        story += [Spacer(1, .5 * cm)]
    except Exception as e:
        warns.append(f"Category: {e}")

    CHART_BG = "#050816"
    PANEL_BG = "#0D1225"
    TICK     = "#8A97B5"
    GRIDC    = "#1A2242"

    def fig_bytes(fig):
        ib = _io.BytesIO()
        fig.savefig(ib, format="png", bbox_inches="tight", dpi=150, facecolor=CHART_BG)
        ib.seek(0)
        plt.close(fig)
        return ib

    # ── Daily Trend Chart ──────────────────────────────────────────
    try:
        story.append(Paragraph("Daily Sales Trend", s_h1))
        if len(daily) > 0:
            fig, ax = plt.subplots(figsize=(13, 3.8), facecolor=CHART_BG)
            ax.set_facecolor(PANEL_BG)
            xs = list(range(len(daily)))
            ys = list(daily.values)
            ax.fill_between(xs, ys, alpha=.1, color="#4F8CFF")
            ax.plot(xs, ys, color="#00D4FF", linewidth=2.2, zorder=4)
            ax.scatter(xs, ys, color="#4F8CFF", s=20, zorder=5)
            if len(daily) >= 7:
                ma7 = daily.rolling(7).mean()
                ax.plot(xs, ma7, color="#FFD166", linewidth=1.5,
                        linestyle="--", label="7-Day MA", zorder=3)
                ax.legend(facecolor=PANEL_BG, edgecolor=GRIDC,
                          labelcolor="#C8D4E8", fontsize=8)
            ax.tick_params(colors=TICK, labelsize=7)
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: f"{v / 1e3:.0f}K" if v >= 1000 else str(int(v)))
            )
            for sp in ax.spines.values():
                sp.set_color(GRIDC)
            ax.grid(axis="y", color=GRIDC, linewidth=.5, alpha=.7)
            ax.set_xlabel("Day",     color=TICK, fontsize=7)
            ax.set_ylabel("Revenue", color=TICK, fontsize=7)
            story.append(RLImage(fig_bytes(fig), width=W, height=4.5 * cm))
        story.append(Spacer(1, .4 * cm))
    except Exception as e:
        warns.append(f"Trend chart: {e}")

    # ── Category Bar Chart ─────────────────────────────────────────
    try:
        story.append(Paragraph("Category Revenue Breakdown", s_h1))
        if not cat_totals.empty:
            cats = cat_totals["Category"].astype(str).tolist()
            vals = [float(v) for v in cat_totals["Total"].tolist()]
            PAL  = ["#4F8CFF", "#7B61FF", "#00D4FF", "#00FFC6",
                    "#FFD166", "#FF6B6B", "#A78BFA", "#38BDF8"]
            fig2, ax2 = plt.subplots(
                figsize=(12, max(3, len(cats) * .55)), facecolor=CHART_BG,
            )
            ax2.set_facecolor(PANEL_BG)
            bars = ax2.barh(
                cats, vals,
                color=[PAL[i % len(PAL)] for i in range(len(cats))],
                alpha=.85, edgecolor="none", height=.6,
            )
            for bar, val in zip(bars, vals):
                ax2.text(
                    bar.get_width() * 1.012,
                    bar.get_y() + bar.get_height() / 2,
                    f"{INR}{val / 1e3:.1f}K",
                    va="center", color="#C8D4E8", fontsize=7.5,
                )
            ax2.tick_params(colors=TICK, labelsize=7)
            for sp in ax2.spines.values():
                sp.set_color(GRIDC)
            ax2.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: f"{v / 1e3:.0f}K")
            )
            ax2.grid(axis="x", color=GRIDC, linewidth=.5, alpha=.7)
            story.append(
                RLImage(fig_bytes(fig2), width=W, height=max(4 * cm, len(cats) * .7 * cm))
            )
        story.append(PageBreak())
    except Exception as e:
        warns.append(f"Cat chart: {e}")

    # ── Zero-Sales Alerts ──────────────────────────────────────────
    try:
        story.append(Paragraph("Zero-Sales Alerts", s_h1))
        a_data = (
            [["Salesperson", "Alert Type", "Urgency", "Action"]]
            + [[n, "Never Sold",   "CRITICAL", "Immediate review"]    for n in never_sold]
            + [[n, "Had Bad Day",  "MONITOR",  "Follow up this week"] for n in bad_day]
        )
        if len(a_data) > 1:
            zt = Table(a_data, colWidths=[W * .28, W * .20, W * .16, W * .36])
            zt.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), C_DARK),
                ("TEXTCOLOR",     (0, 0), (-1, 0), C_RED),
                ("FONTNAME",      (0, 0), (-1, 0), FB),
                ("FONTNAME",      (0, 1), (-1, -1), F),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("TEXTCOLOR",     (0, 1), (-1, -1), C_WHITE),
                ("GRID",          (0, 0), (-1, -1), .3, colors.HexColor("#2A1020")),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ]))
            story.append(zt)
        else:
            story.append(
                Paragraph("No zero-sales alerts — all sellers have recorded revenue.", s_body)
            )
        story += [
            Spacer(1, .6 * cm),
            HRFlowable(width=W, thickness=1, color=C_BLUE, spaceAfter=10),
        ]
    except Exception as e:
        warns.append(f"Alerts: {e}")

    # ══ AI Intelligence Analysis — fixed, section-by-section ══════
    try:
        story.append(Paragraph("AI Intelligence Analysis", s_h1))
        story.append(Spacer(1, .25 * cm))

        raw = report_txt or ""

        # Split on ARIA's standard section headers: <strong>── N. NAME ──</strong>
        sec_re_pdf = re.compile(
            r'<strong>──\s*(\d+\.\s*[^<]+?)──</strong>',
            re.DOTALL,
        )
        parts_pdf = sec_re_pdf.split(raw)

        def _plain(html_str: str) -> str:
            """Strip HTML tags and collapse whitespace."""
            txt = re.sub(r'<[^>]+>', ' ', html_str)
            txt = re.sub(r'\s{2,}', ' ', txt)
            return txt.strip()

        def _build_rl_table(table_html: str) -> Table | None:
            """Convert a single HTML <table>…</table> block to a ReportLab Table."""
            rows_raw = re.findall(
                r'<tr([^>]*)>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE
            )
            tbl_data   = []
            row_styles = []
            for ri, (tr_attrs, tr_inner) in enumerate(rows_raw):
                cells = re.findall(
                    r'<t[hd][^>]*>(.*?)</t[hd]>', tr_inner, re.DOTALL | re.IGNORECASE
                )
                cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                if not cleaned:
                    continue
                tbl_data.append(cleaned)
                if 'class="top"'   in tr_attrs:
                    row_styles.append(("TEXTCOLOR", (0, ri), (-1, ri), C_GREEN))
                elif 'class="alert"' in tr_attrs:
                    row_styles.append(("TEXTCOLOR", (0, ri), (-1, ri), C_RED))
                elif 'class="warn"'  in tr_attrs:
                    row_styles.append(("TEXTCOLOR", (0, ri), (-1, ri), C_GOLD))

            if not tbl_data:
                return None

            col_count = max(len(r) for r in tbl_data)
            tbl_data  = [r + [""] * (col_count - len(r)) for r in tbl_data]
            col_w     = W / col_count

            t_obj = Table(tbl_data, colWidths=[col_w] * col_count)
            base_style = [
                ("BACKGROUND",     (0, 0), (-1, 0), C_DARK),
                ("TEXTCOLOR",      (0, 0), (-1, 0), C_CYAN),
                ("FONTNAME",       (0, 0), (-1, 0), FB),
                ("FONTNAME",       (0, 1), (-1, -1), F),
                ("FONTSIZE",       (0, 0), (-1, -1), 8),
                ("TEXTCOLOR",      (0, 1), (-1, -1), C_WHITE),
                ("GRID",           (0, 0), (-1, -1), .3, GRID),
                ("TOPPADDING",     (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
                ("LEFTPADDING",    (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [C_PANEL, colors.HexColor("#080B19")]),
            ]
            t_obj.setStyle(TableStyle(base_style + row_styles))
            return t_obj

        def _render_section_content(sec_content: str):
            """Emit story items for one section's HTML content."""
            table_re = re.compile(
                r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE
            )
            cursor = 0
            for tm in table_re.finditer(sec_content):
                # Plain text before this table
                before = _plain(sec_content[cursor:tm.start()])
                if before:
                    for line in before.split("•"):
                        chunk = line.strip()
                        if chunk:
                            prefix = "• " if "•" in before else ""
                            story.append(Paragraph(f"{prefix}{chunk}", s_body))
                cursor = tm.end()

                # Table
                try:
                    tbl = _build_rl_table(tm.group(1))
                    if tbl:
                        story.append(tbl)
                        story.append(Spacer(1, .2 * cm))
                except Exception as te:
                    warns.append(f"Inline table: {te}")

            # Remaining plain text after last table
            remaining = _plain(sec_content[cursor:])
            if remaining:
                for line in remaining.split("•"):
                    chunk = line.strip()
                    if chunk:
                        prefix = "• " if "•" in remaining else ""
                        story.append(Paragraph(f"{prefix}{chunk}", s_body))

        if len(parts_pdf) > 1:
            # Preamble before first section
            intro = _plain(parts_pdf[0])
            if intro:
                story.append(Paragraph(intro, s_body))
                story.append(Spacer(1, .15 * cm))

            i = 1
            while i < len(parts_pdf):
                sec_title   = parts_pdf[i].strip()
                sec_content = parts_pdf[i + 1].strip() if (i + 1) < len(parts_pdf) else ""
                i += 2

                # Gold section header
                story.append(Paragraph(f"── {sec_title} ──", s_sec_hdr))
                _render_section_content(sec_content)
                story.append(Spacer(1, .18 * cm))
        else:
            # Fallback: no section headers — render as plain paragraphs
            clean = _plain(raw)
            for line in clean.split("\n"):
                p = line.strip()
                if p:
                    story.append(Paragraph(p, s_body))
                    story.append(Spacer(1, .06 * cm))

    except Exception as e:
        warns.append(f"AI text: {e}")

    # ── Chat Transcript ────────────────────────────────────────────
    try:
        if chat_log:
            story.append(PageBreak())
            story.append(Paragraph("Conversation Transcript", s_h1))
            story.append(
                Paragraph(
                    "Full chat history between you and ARIA, included for reference.",
                    s_sub,
                )
            )
            story.append(Spacer(1, .2 * cm))
            for m in chat_log:
                text = re.sub(r'<div id="aria-sq".*?</div>', '', m["content"], flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                role_label = "You" if m["role"] == "user" else "ARIA"
                style      = s_chat_u if m["role"] == "user" else s_chat_a
                story.append(
                    Paragraph(f"<b>{role_label}</b> ({m.get('ts', '')}): {text}", style)
                )
        else:
            story.append(Spacer(1, .4 * cm))
            story.append(
                Paragraph("No chat conversation recorded in this session.", s_sub)
            )
    except Exception as e:
        warns.append(f"Chat transcript: {e}")

    # ── Footer ─────────────────────────────────────────────────────
    story.append(Spacer(1, .6 * cm))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_MUTED))
    story.append(Spacer(1, .2 * cm))
    story.append(Paragraph(
        f"ARIA Sales Intelligence Platform · Report generated "
        f"{datetime.datetime.now().strftime('%d %B %Y')} · Powered by LLaMA 3.3-70B",
        S("footer", fontSize=7, textColor=C_MUTED, alignment=1),
    ))

    def draw_page(cv, doc_obj):
        try:
            cv.saveState()
            cv.setFillColor(C_BG)
            cv.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            cv.setFillColor(C_PANEL)
            cv.rect(0, 0, A4[0], 1.8 * cm, fill=1, stroke=0)
            cv.setStrokeColor(C_BLUE)
            cv.setLineWidth(.8)
            cv.line(1.8 * cm, 1.8 * cm, A4[0] - 1.8 * cm, 1.8 * cm)
            cv.setFont(F if USE_DJ else "Helvetica", 6.5)
            cv.setFillColor(C_MUTED)
            cv.drawCentredString(
                A4[0] / 2, .7 * cm,
                f"ARIA Sales Intelligence · {datetime.datetime.now().strftime('%d %B %Y')} · LLaMA 3.3-70B",
            )
            cv.setFillColor(C_CYAN)
            cv.drawRightString(A4[0] - 1.8 * cm, .7 * cm, f"Page {doc_obj.page}")
            cv.restoreState()
        except Exception:
            pass

    if not story:
        return None, "All sections failed:\n" + "\n".join(warns)

    try:
        doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    except Exception:
        return None, f"doc.build() failed:\n\n{traceback.format_exc()}"

    return buf.getvalue(), ("Warnings:\n" + "\n".join(warns)) if warns else None


# ── PDF trigger ────────────────────────────────────────────────────
if dl_pdf:
    report_src = st.session_state.get("bi_report_txt") or ""
    if not report_src:
        with st.spinner("Generating summary for PDF…"):
            try:
                report_src = ask_groq(
                    "Provide a concise executive summary in 5 key bullet points.",
                    SYSTEM_PROMPT,
                    chat_history=[],
                )
            except Exception as e:
                report_src = f"Summary unavailable: {e}"

    pdf_prog = st.empty()
    for si in range(len(PDF_STEPS)):
        pdf_prog.markdown(
            render_steps(PDF_STEPS, si, "Building PDF"),
            unsafe_allow_html=True,
        )
        time.sleep(0.2)

    pdf_bytes, err = build_pdf(report_src, filename, st.session_state["chat_history"])
    pdf_prog.markdown(
        render_steps(PDF_STEPS, len(PDF_STEPS), "Building PDF"),
        unsafe_allow_html=True,
    )
    time.sleep(0.3)
    pdf_prog.empty()

    if pdf_bytes is None:
        st.error("PDF failed. Full traceback:")
        st.code(err or "Unknown error", language="text")
    else:
        if err:
            st.warning(err)
        st.success("✅ PDF ready — includes your chat transcript!")
        st.download_button(
            label="⬇️  Download ARIA Intelligence Report (PDF)",
            data=pdf_bytes,
            file_name=f"ARIA_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ── Bottom nav ─────────────────────────────────────────────────────
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="bot-nav">', unsafe_allow_html=True)
if st.button("← Back to Dashboard", use_container_width=True, key="bot_nav"):
    st.switch_page("pages/1_Dashboard.py")
st.markdown('</div>', unsafe_allow_html=True)