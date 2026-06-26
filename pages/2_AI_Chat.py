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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

:root{
  --bg:#060810; --surf:#0A0D1C; --panel:#0E1328; --panel2:#111930;
  --border:rgba(255,255,255,0.06); --border2:rgba(255,255,255,0.10);
  --blue:#4F8CFF; --blue-d:rgba(79,140,255,0.12);
  --purple:#7B61FF; --purple-d:rgba(123,97,255,0.12);
  --cyan:#00D4FF; --cyan-d:rgba(0,212,255,0.10);
  --green:#00FFC6; --green-d:rgba(0,255,198,0.10);
  --gold:#FFD166; --gold-d:rgba(255,209,102,0.10);
  --pink:#FF6EB4; --pink-d:rgba(255,110,180,0.10);
  --red:#FF6B6B; --red-d:rgba(255,107,107,0.10);
  --orange:#FF9F43;
  --t1:#F0F4FF; --t2:#9BA8C4; --t3:#4E5A75;
}

html,body,.stApp{
  background:var(--bg) !important;
  font-family:'Inter',sans-serif;
  color:var(--t2);
}

.stApp::before{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background:
    radial-gradient(ellipse 60% 40% at 15% 20%,rgba(79,140,255,0.05) 0%,transparent 65%),
    radial-gradient(ellipse 50% 35% at 85% 75%,rgba(123,97,255,0.04) 0%,transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%,rgba(0,212,255,0.03) 0%,transparent 55%);
}

#MainMenu,footer,header,.stDeployButton{visibility:hidden;}

.block-container{
  padding:0.8rem 2vw 5rem !important;
  max-width:860px !important;
  margin:0 auto !important;
  position:relative; z-index:1;
}

/* ── ANIMATIONS ── */
@keyframes pulse      {0%,100%{opacity:1;}50%{opacity:.2;}}
@keyframes glow       {0%,100%{box-shadow:0 0 10px rgba(79,140,255,.3);}50%{box-shadow:0 0 24px rgba(79,140,255,.7);}}
@keyframes glowCyan   {0%,100%{box-shadow:0 0 10px rgba(0,212,255,.25);}50%{box-shadow:0 0 22px rgba(0,212,255,.6);}}
@keyframes glowGold   {0%,100%{box-shadow:0 0 10px rgba(255,209,102,.25);}50%{box-shadow:0 0 20px rgba(255,209,102,.55);}}
@keyframes bounce3    {0%,60%,100%{transform:translateY(0);}30%{transform:translateY(-7px);}}
@keyframes slideUp    {from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
@keyframes morphGrad  {0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}
@keyframes shimmer    {0%{opacity:0.4;}50%{opacity:1;}100%{opacity:0.4;}}
@keyframes chipGlow   {0%,100%{box-shadow:none;}50%{box-shadow:var(--glow);}}

/* ══════════════════
   TOPBAR
══════════════════ */
.topbar{
  display:flex; align-items:center; justify-content:space-between;
  padding:.5rem 1.1rem; margin-bottom:.8rem;
  background:rgba(10,13,28,0.92);
  border:1px solid rgba(79,140,255,0.14);
  border-radius:16px; backdrop-filter:blur(24px);
  animation:slideUp .4s ease both; position:relative; overflow:hidden;
}
.topbar::before{
  content:''; position:absolute; inset:0;
  background:linear-gradient(90deg,rgba(79,140,255,.03) 0%,transparent 50%,rgba(0,212,255,.02) 100%);
  pointer-events:none;
}
.tb-left{display:flex;align-items:center;gap:.65rem;}
.tb-logo{
  width:32px;height:32px;border-radius:9px;flex-shrink:0;
  background:linear-gradient(135deg,#4F8CFF 0%,#7B61FF 55%,#00D4FF 100%);
  display:flex;align-items:center;justify-content:center;
  font-size:.8rem;font-weight:900;color:#fff;animation:glow 3s ease infinite;
  position:relative;
}
.tb-logo::after{
  content:'';position:absolute;inset:-2px;border-radius:11px;z-index:-1;
  background:linear-gradient(135deg,#4F8CFF,#7B61FF,#00D4FF);
  filter:blur(5px);opacity:.45;
}
.tb-name{font-size:.95rem;font-weight:900;color:var(--t1);letter-spacing:-.4px;}
.tb-tag{
  font-family:'JetBrains Mono',monospace;font-size:.5rem;font-weight:600;
  padding:2px 9px;border-radius:99px;
  background:linear-gradient(90deg,rgba(0,212,255,.1),rgba(79,140,255,.1));
  border:1px solid rgba(0,212,255,.2);color:var(--cyan);letter-spacing:.5px;
}
.tb-right{display:flex;align-items:center;gap:6px;}
.tb-pill{
  font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--t3);
  background:rgba(255,255,255,.025);border:1px solid var(--border);
  padding:3px 8px;border-radius:6px;
}
.tb-live{
  display:flex;align-items:center;gap:5px;
  font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--green);
  background:var(--green-d);border:1px solid rgba(0,255,198,.18);
  padding:3px 8px;border-radius:6px;
}
.tb-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 1.8s infinite;}

/* ══════════════════
   SIDEBAR
══════════════════ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#07091A 0%,#060810 100%) !important;
  border-right:1px solid rgba(79,140,255,0.1) !important;
}
section[data-testid="stSidebar"] *{color:var(--t2) !important;}

.sb-brand{
  display:flex;align-items:center;gap:9px;
  padding:.9rem .8rem .5rem;
  border-bottom:1px solid rgba(255,255,255,.04);
  margin-bottom:.3rem;
}
.sb-brand-logo{
  width:34px;height:34px;border-radius:9px;flex-shrink:0;
  background:linear-gradient(135deg,#4F8CFF,#7B61FF 55%,#00D4FF);
  display:flex;align-items:center;justify-content:center;
  font-size:.85rem;font-weight:900;color:#fff;
  box-shadow:0 0 14px rgba(79,140,255,.38);
}
.sb-brand-name{font-size:.88rem;font-weight:800;color:var(--t1);}
.sb-brand-sub{font-family:'JetBrains Mono',monospace;font-size:.46rem;color:var(--t3);margin-top:1px;}

.sb-section{
  font-family:'JetBrains Mono',monospace;font-size:.47rem;
  letter-spacing:2.5px;text-transform:uppercase;
  padding:.55rem .8rem .2rem;color:var(--t3) !important;
  display:flex;align-items:center;gap:6px;
}
.sb-section::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,.05),transparent);}

/* ── QUICK ASK CHIPS — fully redesigned ── */
.qa-wrap{padding:0 .4rem .2rem;}

.qa-chip{
  display:flex;align-items:center;gap:8px;
  padding:.38rem .65rem;border-radius:10px;cursor:pointer;
  margin-bottom:3px;font-size:.68rem;font-weight:500;
  transition:all .16s ease;border:1px solid transparent;
  position:relative;overflow:hidden;
  font-family:'Inter',sans-serif;
}
.qa-chip .chip-icon{
  font-size:.78rem;flex-shrink:0;
  width:22px;height:22px;border-radius:7px;
  display:flex;align-items:center;justify-content:center;
}
.qa-chip .chip-txt{flex:1;line-height:1.3;}
.qa-chip .chip-arr{
  font-size:.6rem;opacity:0;transition:all .15s;
  transform:translateX(-4px);
}
.qa-chip:hover .chip-arr{opacity:.6;transform:translateX(0);}

/* chip color themes */
.qc-blue{background:rgba(79,140,255,.07);border-color:rgba(79,140,255,.16);color:#7AAEFF !important;}
.qc-blue .chip-icon{background:rgba(79,140,255,.15);}
.qc-blue:hover{background:rgba(79,140,255,.13);border-color:rgba(79,140,255,.38);transform:translateX(4px);box-shadow:0 0 16px rgba(79,140,255,.18);}

.qc-cyan{background:rgba(0,212,255,.06);border-color:rgba(0,212,255,.14);color:#3AD9FF !important;}
.qc-cyan .chip-icon{background:rgba(0,212,255,.12);}
.qc-cyan:hover{background:rgba(0,212,255,.12);border-color:rgba(0,212,255,.35);transform:translateX(4px);box-shadow:0 0 16px rgba(0,212,255,.16);}

.qc-green{background:rgba(0,255,198,.06);border-color:rgba(0,255,198,.13);color:#2AFFCE !important;}
.qc-green .chip-icon{background:rgba(0,255,198,.11);}
.qc-green:hover{background:rgba(0,255,198,.12);border-color:rgba(0,255,198,.32);transform:translateX(4px);box-shadow:0 0 16px rgba(0,255,198,.15);}

.qc-gold{background:rgba(255,209,102,.07);border-color:rgba(255,209,102,.16);color:#FFD980 !important;}
.qc-gold .chip-icon{background:rgba(255,209,102,.13);}
.qc-gold:hover{background:rgba(255,209,102,.13);border-color:rgba(255,209,102,.38);transform:translateX(4px);box-shadow:0 0 16px rgba(255,209,102,.16);}

.qc-purple{background:rgba(123,97,255,.07);border-color:rgba(123,97,255,.16);color:#9B80FF !important;}
.qc-purple .chip-icon{background:rgba(123,97,255,.13);}
.qc-purple:hover{background:rgba(123,97,255,.13);border-color:rgba(123,97,255,.38);transform:translateX(4px);box-shadow:0 0 16px rgba(123,97,255,.16);}

.qc-pink{background:rgba(255,110,180,.07);border-color:rgba(255,110,180,.14);color:#FF8EC5 !important;}
.qc-pink .chip-icon{background:rgba(255,110,180,.12);}
.qc-pink:hover{background:rgba(255,110,180,.13);border-color:rgba(255,110,180,.35);transform:translateX(4px);box-shadow:0 0 16px rgba(255,110,180,.14);}

.qc-red{background:rgba(255,107,107,.07);border-color:rgba(255,107,107,.14);color:#FF9090 !important;}
.qc-red .chip-icon{background:rgba(255,107,107,.12);}
.qc-red:hover{background:rgba(255,107,107,.13);border-color:rgba(255,107,107,.35);transform:translateX(4px);box-shadow:0 0 16px rgba(255,107,107,.14);}

.qc-orange{background:rgba(255,159,67,.07);border-color:rgba(255,159,67,.14);color:#FFB870 !important;}
.qc-orange .chip-icon{background:rgba(255,159,67,.12);}
.qc-orange:hover{background:rgba(255,159,67,.13);border-color:rgba(255,159,67,.35);transform:translateX(4px);box-shadow:0 0 16px rgba(255,159,67,.14);}

/* force streamlit buttons to be transparent so our CSS shows */
.qa-wrap .stButton button{
  background:transparent !important;border:none !important;
  padding:0 !important;margin:0 !important;
  width:100% !important;height:auto !important;
  color:inherit !important;font-size:inherit !important;
  font-weight:inherit !important;font-family:inherit !important;
  text-align:left !important;
}
.qa-wrap .stButton>div{margin:0 !important;}

/* sidebar KPIs */
.sb-kpi{
  margin:0 .4rem .3rem;
  background:rgba(255,255,255,.018);
  border:1px solid var(--border);
  border-radius:10px;padding:.5rem .7rem;
  position:relative;overflow:hidden;transition:all .2s;
}
.sb-kpi:hover{background:rgba(255,255,255,.03);border-color:rgba(255,255,255,.08);}
.sb-kpi-bar{position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:10px 0 0 10px;}
.sb-kpi-label{font-family:'JetBrains Mono',monospace;font-size:.45rem;color:var(--t3);text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;}
.sb-kpi-value{font-size:.78rem;font-weight:700;color:var(--t1);line-height:1.2;}

/* nav buttons */
.sb-nav .stButton button{
  background:rgba(255,255,255,.015) !important;border:1px solid var(--border) !important;
  color:var(--t3) !important;border-radius:9px !important;font-size:.7rem !important;
  margin-bottom:4px !important;transition:all .15s !important;font-weight:500 !important;
  text-align:left !important;
}
.sb-nav .stButton button:hover{
  background:rgba(79,140,255,.06) !important;border-color:rgba(79,140,255,.22) !important;
  color:var(--blue) !important;transform:translateX(2px) !important;
}

/* ══════════════════
   WELCOME HERO
══════════════════ */
.hero{
  border-radius:18px;padding:1.3rem 1.5rem;margin-bottom:.9rem;
  position:relative;overflow:hidden;
  border:1px solid rgba(79,140,255,.14);
  animation:slideUp .5s ease both;
  background:linear-gradient(135deg,rgba(79,140,255,.06),rgba(123,97,255,.04),rgba(0,212,255,.03));
}
.hero::before{
  content:'';position:absolute;top:-40px;right:-40px;
  width:180px;height:180px;border-radius:50%;
  background:radial-gradient(circle,rgba(79,140,255,.1),transparent 70%);
  pointer-events:none;
}
.hero-top{display:flex;align-items:center;gap:8px;margin-bottom:.4rem;}
.hero-live{width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 9px var(--green);animation:pulse 1.8s infinite;flex-shrink:0;}
.hero-title{font-size:1rem;font-weight:900;color:var(--t1);letter-spacing:-.4px;}
.hero-sub{font-size:.79rem;color:var(--t3);line-height:1.7;margin-bottom:.9rem;}
.hero-chips{display:flex;flex-wrap:wrap;gap:6px;}
.hchip{font-size:.66rem;padding:3px 10px;border-radius:99px;font-weight:500;}
.hc-blue  {background:rgba(79,140,255,.1); border:1px solid rgba(79,140,255,.2); color:var(--blue);}
.hc-green {background:rgba(0,255,198,.08); border:1px solid rgba(0,255,198,.18); color:var(--green);}
.hc-gold  {background:rgba(255,209,102,.1);border:1px solid rgba(255,209,102,.2);color:var(--gold);}
.hc-red   {background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.2);color:var(--red);}

/* ══════════════════
   CHAT MESSAGES — ChatGPT-style
══════════════════ */
.chat-container{
  display:flex;flex-direction:column;gap:0;
  padding:.2rem 0;
}

/* individual message row */
.cmsg{display:flex;gap:10px;animation:slideUp .25s ease both;margin-bottom:1rem;}
.cmsg.user{flex-direction:row-reverse;}

/* avatars */
.cmsg-av{
  width:32px;height:32px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:.75rem;font-weight:700;margin-top:2px;
}
.av-ai{
  background:linear-gradient(135deg,rgba(79,140,255,.25),rgba(0,212,255,.2));
  border:1px solid rgba(0,212,255,.3);color:var(--cyan);
  animation:glowCyan 3.5s ease infinite;position:relative;
}
.av-ai::after{
  content:'';position:absolute;inset:-2px;border-radius:50%;
  border:1px solid rgba(0,212,255,.18);animation:pulse 2.5s infinite;
}
.av-user{
  background:linear-gradient(135deg,rgba(79,140,255,.2),rgba(123,97,255,.15));
  border:1px solid rgba(79,140,255,.22);color:var(--blue);
}

/* bubble container */
.cmsg-body{flex:1;min-width:0;max-width:82%;}
.cmsg.user .cmsg-body{display:flex;flex-direction:column;align-items:flex-end;}

/* user bubble */
.bubble-user{
  background:linear-gradient(135deg,rgba(79,140,255,.15),rgba(123,97,255,.11));
  border:1px solid rgba(79,140,255,.22);
  border-radius:18px 4px 18px 18px;
  padding:.65rem 1rem;
  font-size:.84rem;color:var(--t1);line-height:1.7;
  display:inline-block;max-width:100%;
  word-break:break-word;
}

/* AI bubble */
.bubble-ai{
  background:rgba(10,13,28,.88);
  border:1px solid rgba(79,140,255,.1);
  border-radius:4px 18px 18px 18px;
  padding:.8rem 1.05rem;
  font-size:.84rem;color:var(--t2);line-height:1.8;
  position:relative;overflow:hidden;
  word-break:break-word;
}
.bubble-ai::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(0,212,255,.28),transparent);
}

/* message text styling */
.bubble-ai strong,.bubble-user strong{color:var(--t1);font-weight:600;}
.bubble-ai em{color:var(--cyan);font-style:normal;}
.bubble-ai table{width:100%;border-collapse:collapse;margin:.6rem 0;font-size:.78rem;}
.bubble-ai th{
  background:rgba(79,140,255,.1);color:var(--cyan);
  font-family:'JetBrains Mono',monospace;font-size:.52rem;
  text-transform:uppercase;letter-spacing:.7px;
  padding:.38rem .75rem;text-align:left;border:1px solid rgba(255,255,255,.05);
}
.bubble-ai td{padding:.3rem .75rem;border:1px solid rgba(255,255,255,.04);color:var(--t2);}
.bubble-ai tr:nth-child(even) td{background:rgba(255,255,255,.012);}
.bubble-ai tr.top td{color:var(--green);font-weight:600;}
.bubble-ai tr.alert td{color:var(--red);}
.bubble-ai tr.warn td{color:var(--gold);}

/* timestamp */
.cmsg-ts{
  font-family:'JetBrains Mono',monospace;font-size:.47rem;color:var(--t3);
  margin-top:3px;padding:0 2px;
}
.cmsg.user .cmsg-ts{text-align:right;}

/* typing indicator */
.typing-bubble{
  background:rgba(10,13,28,.88);border:1px solid rgba(79,140,255,.1);
  border-radius:4px 18px 18px 18px;
  padding:.7rem 1.1rem;display:inline-flex;align-items:center;gap:8px;
}
.tdot{width:8px;height:8px;border-radius:50%;background:var(--blue);animation:bounce3 1.1s ease infinite;}
.tdot:nth-child(2){animation-delay:.14s;background:var(--purple);}
.tdot:nth-child(3){animation-delay:.28s;background:var(--cyan);}
.typing-txt{font-family:'JetBrains Mono',monospace;font-size:.56rem;color:var(--t3);}

/* suggested follow-ups */
.sug-wrap{margin:.5rem 0 .2rem 42px;animation:slideUp .3s .1s ease both;}
.sug-label{font-family:'JetBrains Mono',monospace;font-size:.47rem;color:var(--t3);text-transform:uppercase;letter-spacing:1.8px;margin-bottom:.35rem;display:flex;align-items:center;gap:5px;}
.sug-label::before{content:'◆';font-size:.42rem;color:var(--cyan);}
.sug-chips{display:flex;flex-wrap:wrap;gap:6px;}
.sug-chip{
  font-size:.68rem;padding:4px 11px;border-radius:8px;cursor:pointer;
  background:rgba(79,140,255,.07);border:1px solid rgba(79,140,255,.15);
  color:var(--blue);transition:all .15s;font-weight:500;white-space:nowrap;
}
.sug-chip:hover{background:rgba(79,140,255,.14);border-color:rgba(79,140,255,.36);transform:translateY(-2px);box-shadow:0 4px 12px rgba(79,140,255,.14);}

/* ── CHAT INPUT ── */
.stChatInput>div{
  background:rgba(8,11,24,.92) !important;
  border:1px solid rgba(79,140,255,.18) !important;
  border-radius:14px !important;backdrop-filter:blur(20px) !important;
  transition:all .2s !important;
}
.stChatInput>div:focus-within{
  border-color:rgba(79,140,255,.45) !important;
  box-shadow:0 0 28px rgba(79,140,255,.09) !important;
}
.stChatInput textarea{color:var(--t1) !important;font-family:'Inter',sans-serif !important;font-size:.84rem !important;}
[data-testid="stChatInputSubmitButton"] svg{color:var(--blue) !important;}

/* ══════════════════
   DIVIDER
══════════════════ */
.div-line{height:1px;margin:.9rem 0;background:linear-gradient(90deg,transparent,rgba(79,140,255,.15),rgba(0,212,255,.1),transparent);}

/* ══════════════════
   REPORT BANNER — vibrant
══════════════════ */
.gen-banner{
  border-radius:18px;padding:1.3rem 1.5rem;margin:.8rem 0 .6rem;
  position:relative;overflow:hidden;
  border:1px solid rgba(255,209,102,.18);
  background:linear-gradient(135deg,
    rgba(255,209,102,.07) 0%,rgba(255,107,107,.04) 30%,
    rgba(79,140,255,.06) 65%,rgba(0,212,255,.04) 100%);
  animation:slideUp .5s ease both;
}
.gen-banner::before{
  content:'';position:absolute;top:-60px;right:-40px;
  width:200px;height:200px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,209,102,.09),transparent 65%);
  pointer-events:none;
}
.gen-banner::after{
  content:'';position:absolute;bottom:-40px;left:-30px;
  width:150px;height:150px;border-radius:50%;
  background:radial-gradient(circle,rgba(79,140,255,.07),transparent 65%);
  pointer-events:none;
}
.gen-inner{position:relative;z-index:1;}
.gen-eyebrow{
  font-family:'JetBrains Mono',monospace;font-size:.5rem;
  color:var(--gold);letter-spacing:2px;text-transform:uppercase;
  margin-bottom:.35rem;display:flex;align-items:center;gap:6px;
}
.gen-eyebrow::before{content:'◆';font-size:.4rem;animation:shimmer 2s ease infinite;}
.gen-title{font-size:1rem;font-weight:900;color:var(--t1);margin-bottom:.25rem;letter-spacing:-.3px;}
.gen-sub{font-size:.76rem;color:var(--t3);line-height:1.6;margin-bottom:.9rem;}
.gen-pills{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:.85rem;}
.gp{font-size:.62rem;padding:3px 9px;border-radius:99px;font-weight:500;}
.gp-b{background:rgba(79,140,255,.1); border:1px solid rgba(79,140,255,.2); color:var(--blue);}
.gp-c{background:rgba(0,212,255,.09); border:1px solid rgba(0,212,255,.18); color:var(--cyan);}
.gp-g{background:rgba(0,255,198,.08); border:1px solid rgba(0,255,198,.17); color:var(--green);}
.gp-o{background:rgba(255,209,102,.09);border:1px solid rgba(255,209,102,.18);color:var(--gold);}
.gp-p{background:rgba(123,97,255,.09); border:1px solid rgba(123,97,255,.18); color:var(--purple);}
.gp-k{background:rgba(255,110,180,.09);border:1px solid rgba(255,110,180,.17);color:var(--pink);}

/* generate button */
.btn-gen .stButton button{
  background:linear-gradient(135deg,#4F8CFF,#7B61FF 50%,#00D4FF) !important;
  background-size:200% auto !important;animation:morphGrad 4s ease infinite !important;
  border:none !important;color:#fff !important;
  box-shadow:0 4px 20px rgba(79,140,255,.3),0 0 0 1px rgba(255,255,255,.07) inset !important;
  border-radius:11px !important;font-weight:800 !important;font-size:.82rem !important;
  transition:all .2s !important;
}
.btn-gen .stButton button:hover{transform:translateY(-2px) !important;box-shadow:0 8px 30px rgba(79,140,255,.48) !important;}

/* pdf button */
.btn-pdf .stButton button{
  background:linear-gradient(135deg,#FFD166,#FF9F43) !important;
  border:none !important;color:#0A0D1C !important;
  box-shadow:0 4px 16px rgba(255,209,102,.25) !important;
  border-radius:11px !important;font-weight:800 !important;font-size:.82rem !important;
  transition:all .2s !important;
}
.btn-pdf .stButton button:hover{transform:translateY(-2px) !important;box-shadow:0 8px 26px rgba(255,209,102,.42) !important;}

/* clear button */
.btn-clr .stButton button{
  background:rgba(255,107,107,.07) !important;border:1px solid rgba(255,107,107,.2) !important;
  color:var(--red) !important;border-radius:11px !important;font-size:.8rem !important;
  font-weight:600 !important;transition:all .2s !important;
}
.btn-clr .stButton button:hover{background:rgba(255,107,107,.13) !important;border-color:rgba(255,107,107,.36) !important;transform:translateY(-1px) !important;}

/* download */
.stDownloadButton button{
  background:linear-gradient(135deg,#00FFC6,#00D4FF) !important;
  border:none !important;color:#060810 !important;font-weight:800 !important;
  border-radius:11px !important;font-size:.82rem !important;
  box-shadow:0 4px 18px rgba(0,255,198,.2) !important;
}
.stDownloadButton button:hover{transform:translateY(-2px) !important;}

/* ── PROGRESS STEPS ── */
.prog-wrap{
  background:rgba(10,13,28,.85);border:1px solid var(--border);
  border-radius:13px;padding:.8rem .9rem;animation:slideUp .3s ease both;
}
.prog-title{font-family:'JetBrains Mono',monospace;font-size:.55rem;color:var(--t3);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.55rem;}
.prog{display:flex;flex-direction:column;gap:.3rem;}
.pstep{display:flex;align-items:center;gap:8px;font-family:'JetBrains Mono',monospace;font-size:.59rem;}
.picon{width:17px;height:17px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.5rem;flex-shrink:0;}
.p-done{background:rgba(0,255,198,.12);color:var(--green);border:1px solid rgba(0,255,198,.2);}
.p-active{background:rgba(79,140,255,.16);color:var(--blue);border:1px solid rgba(79,140,255,.28);animation:glow 1s infinite;}
.p-wait{background:rgba(255,255,255,.04);color:var(--t3);border:1px solid var(--border);}
.pl-done{color:var(--green);}.pl-active{color:var(--blue);}.pl-wait{color:var(--t3);}

/* ── REPORT CARD ── */
.report-card{
  border-radius:18px;border:1px solid rgba(255,209,102,.1);
  background:linear-gradient(135deg,rgba(11,15,32,.97),rgba(8,11,25,.95));
  padding:1.2rem 1.4rem;margin-top:.7rem;
  animation:slideUp .4s ease both;position:relative;overflow:hidden;
}
.report-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,209,102,.25),transparent);
}
.rh{display:flex;align-items:center;justify-content:space-between;margin-bottom:.8rem;padding-bottom:.6rem;border-bottom:1px solid var(--border);}
.rh-left{display:flex;align-items:center;gap:9px;}
.rh-icon{
  width:30px;height:30px;border-radius:8px;flex-shrink:0;
  background:linear-gradient(135deg,rgba(255,209,102,.18),rgba(255,159,67,.12));
  border:1px solid rgba(255,209,102,.18);
  display:flex;align-items:center;justify-content:center;font-size:.8rem;
}
.rh-title{font-size:.88rem;font-weight:800;color:var(--t1);}
.rh-meta{font-family:'JetBrains Mono',monospace;font-size:.5rem;color:var(--t3);margin-top:1px;}
.conf-row{display:flex;align-items:center;gap:8px;}
.conf-track{flex:1;height:3px;background:rgba(255,255,255,.05);border-radius:99px;overflow:hidden;}
.conf-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--cyan));box-shadow:0 0 7px rgba(0,212,255,.35);}
.conf-txt{font-family:'JetBrains Mono',monospace;font-size:.49rem;color:var(--t3);}

/* nav btn fallback */
.bot-nav .stButton button{
  background:rgba(255,255,255,.015) !important;border:1px solid var(--border) !important;
  color:var(--t3) !important;border-radius:9px !important;font-size:.7rem !important;
  font-weight:500 !important;transition:all .15s !important;
}
.bot-nav .stButton button:hover{background:rgba(79,140,255,.06) !important;border-color:rgba(79,140,255,.22) !important;color:var(--blue) !important;}

/* report section body */
.rsec{font-size:.82rem;line-height:1.8;color:var(--t2);}
.rsec strong{color:var(--t1);}
.rsec table{width:100%;border-collapse:collapse;font-size:.77rem;margin:.5rem 0;}
.rsec th{background:rgba(79,140,255,.1);color:var(--cyan);padding:.38rem .72rem;font-family:'JetBrains Mono',monospace;font-size:.51rem;text-transform:uppercase;letter-spacing:.7px;border:1px solid rgba(255,255,255,.05);text-align:left;}
.rsec td{padding:.3rem .72rem;border:1px solid rgba(255,255,255,.04);}
.rsec tr:nth-child(even) td{background:rgba(255,255,255,.01);}
.rsec tr.top td{color:var(--green);font-weight:600;}
.rsec tr.alert td{color:var(--red);}
.rsec tr.warn td{color:var(--gold);}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# GUARD
# ══════════════════════════════════════════════════════════════════
if "df" not in st.session_state:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;animation:slideUp .5s ease both;">
      <div style="font-size:3rem;margin-bottom:1rem;filter:drop-shadow(0 0 20px rgba(79,140,255,.4));">◆</div>
      <div style="font-size:1.15rem;font-weight:900;color:#F0F4FF;margin-bottom:.5rem;">ARIA needs your data</div>
      <div style="font-size:.8rem;color:#4E5A75;margin-bottom:1.5rem;">Upload a sales file to unlock the AI intelligence dashboard.</div>
    </div>
    """, unsafe_allow_html=True)
    c = st.columns([1,2,1])[1]
    with c:
        if st.button("← Upload Dataset", use_container_width=True):
            st.switch_page("app.py")
    st.stop()

df       = st.session_state["df"]
filename = st.session_state.get("filename","dataset.xlsx")

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

_key = f"{df.shape}_{list(df.columns)}"
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
for k, v in {"chat_history":[], "bi_report_txt":None, "_pending_ai":False}.items():
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
        return f'<span style="color:#FF6B6B;font-family:JetBrains Mono,monospace;font-size:.78rem;">⚠️ ARIA error: {str(e)[:200]}</span>'

def extract_sqs(text: str):
    match = re.search(r'<div id="aria-sq"[^>]*>SUGGESTED:\s*(.*?)</div>', text, re.DOTALL)
    if not match:
        return []
    return [q.strip() for q in re.findall(r'Q\d+:\s*(.+)', match.group(1)) if q.strip()]

def strip_sq(text: str) -> str:
    return re.sub(r'<div id="aria-sq".*?</div>', '', text, flags=re.DOTALL).strip()

# ══════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div class="tb-left">
    <div class="tb-logo">◆</div>
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
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-brand-logo">◆</div>
      <div>
        <div class="sb-brand-name">ARIA</div>
        <div class="sb-brand-sub">Sales Intelligence Copilot</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Ask ──────────────────────────────────────────────────
    st.markdown('<div class="sb-section">⚡ Quick Ask</div>', unsafe_allow_html=True)

    QUICK_QS = [
        ("📊", "Full revenue breakdown",            "qc-blue",   0),
        ("🏆", "Top performer deep dive",            "qc-gold",   1),
        ("🚨", "Zero-sales alert summary",           "qc-red",    2),
        ("📋", "Compare all sellers",                "qc-cyan",   3),
        ("🗂️", "Category performance",              "qc-purple", 4),
        ("📈", "Daily trend analysis",               "qc-green",  5),
        ("💡", "Top 3 growth opportunities",         "qc-blue",   6),
        ("⚠️", "What are the biggest risks?",        "qc-orange", 7),
        ("🎯", "What should I focus on today?",      "qc-pink",   8),
        ("📦", "Which category is weakest?",         "qc-cyan",   9),
    ]

    st.markdown('<div class="qa-wrap">', unsafe_allow_html=True)
    for icon, label, color_cls, idx in QUICK_QS:
        # Render the styled chip visually
        st.markdown(f"""
        <div class="qa-chip {color_cls}">
          <span class="chip-icon">{icon}</span>
          <span class="chip-txt">{label}</span>
          <span class="chip-arr">›</span>
        </div>
        """, unsafe_allow_html=True)
        # Invisible button on top to capture click
        if st.button(label, key=f"qs_{idx}", use_container_width=True):
            now_ts = datetime.datetime.now().strftime("%I:%M %p")
            st.session_state["chat_history"].append({"role": "user", "content": label, "ts": now_ts})
            st.session_state["_pending_ai"] = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Live KPIs ──────────────────────────────────────────────────
    st.markdown('<div class="sb-section">📊 Live KPIs</div>', unsafe_allow_html=True)
    kpis = [
        ("var(--cyan)",   "Total Revenue",    f"₹{total_rev:,.0f}"),
        ("var(--gold)",   "MTD Revenue",      mtd_display),
        ("var(--green)",  "Top Seller",       f"{top_seller} · ₹{top_val:,.0f}"),
        ("var(--red)" if zero_list else "var(--green)", "Zero Alerts", f"{len(never_sold)} never · {len(bad_day)} bad day"),
        ("var(--purple)", "Daily Average",    f"₹{avg_daily:,.0f}"),
    ]
    kpi_html = ""
    for col, lbl, val in kpis:
        kpi_html += f"""
        <div class="sb-kpi">
          <div class="sb-kpi-bar" style="background:{col};"></div>
          <div class="sb-kpi-label">{lbl}</div>
          <div class="sb-kpi-value" style="color:{col};">{val}</div>
        </div>"""
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Navigate ───────────────────────────────────────────────────
    st.markdown('<div class="sb-section">🧭 Navigate</div>', unsafe_allow_html=True)
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
    <div style="margin:.5rem .4rem 0;padding:.45rem .6rem;background:rgba(255,255,255,.015);
      border:1px solid var(--border);border-radius:9px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:.44rem;color:var(--t3);
        text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;">Active File</div>
      <div style="font-size:.65rem;color:var(--t2);word-break:break-all;">{filename}</div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# WELCOME HERO
# ══════════════════════════════════════════════════════════════════
if not st.session_state["chat_history"]:
    st.markdown(f"""
    <div class="hero">
      <div class="hero-top">
        <div class="hero-live"></div>
        <div class="hero-title">ARIA — Sales Intelligence Copilot</div>
      </div>
      <div class="hero-sub">
        Analysing <strong style="color:#F0F4FF;">{filename}</strong> in real time.
        Ask anything about your sales data — or tap a Quick Ask in the sidebar.
        Use <strong style="color:var(--gold);">Generate Full Report</strong> below for a complete AI breakdown.
      </div>
      <div class="hero-chips">
        <span class="hchip hc-blue">📊 {active_sellers} Active Sellers</span>
        <span class="hchip hc-green">💰 ₹{total_rev:,.0f} Revenue</span>
        <span class="hchip hc-gold">🏆 {top_seller} leads</span>
        {'<span class="hchip hc-red">🚨 ' + str(alert_count) + ' Alerts</span>' if alert_count else '<span class="hchip hc-green">✅ All Clear</span>'}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CHAT HISTORY RENDER  ← proper ChatGPT-style
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for idx, msg in enumerate(st.session_state["chat_history"]):
    is_last = (idx == len(st.session_state["chat_history"]) - 1)
    ts      = msg.get("ts", "")

    if msg["role"] == "user":
        st.markdown(f"""
        <div class="cmsg user">
          <div class="cmsg-body">
            <div class="bubble-user">{msg["content"]}</div>
            <div class="cmsg-ts">{ts}</div>
          </div>
          <div class="cmsg-av av-user">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        clean = strip_sq(msg["content"])
        st.markdown(f"""
        <div class="cmsg">
          <div class="cmsg-av av-ai">◆</div>
          <div class="cmsg-body">
            <div class="bubble-ai">{clean}</div>
            <div class="cmsg-ts">ARIA · {ts}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggested follow-ups after last AI message
        if is_last:
            sqs = extract_sqs(msg["content"])
            if sqs:
                chips_html = "".join([f'<span class="sug-chip">{q}</span>' for q in sqs])
                st.markdown(f"""
                <div class="sug-wrap">
                  <div class="sug-label">Suggested follow-ups</div>
                  <div class="sug-chips">{chips_html}</div>
                </div>
                """, unsafe_allow_html=True)
                # Clickable invisible buttons
                cols = st.columns(len(sqs))
                for ci, (col, sq) in enumerate(zip(cols, sqs)):
                    with col:
                        if st.button(sq, key=f"sqb_{idx}_{ci}", use_container_width=True):
                            now_ts = datetime.datetime.now().strftime("%I:%M %p")
                            st.session_state["chat_history"].append({"role":"user","content":sq,"ts":now_ts})
                            st.session_state["_pending_ai"] = True
                            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PENDING AI (Quick Ask / Suggested Q)
# ══════════════════════════════════════════════════════════════════
if st.session_state["_pending_ai"]:
    st.session_state["_pending_ai"] = False
    last_q = st.session_state["chat_history"][-1]["content"]

    st.markdown(f"""
    <div class="cmsg user">
      <div class="cmsg-body">
        <div class="bubble-user">{last_q}</div>
      </div>
      <div class="cmsg-av av-user">👤</div>
    </div>
    """, unsafe_allow_html=True)

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
    clean  = strip_sq(response)

    st.markdown(f"""
    <div class="cmsg">
      <div class="cmsg-av av-ai">◆</div>
      <div class="cmsg-body">
        <div class="bubble-ai">{clean}</div>
        <div class="cmsg-ts">ARIA · {now_ts}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state["chat_history"].append({"role":"assistant","content":response,"ts":now_ts})
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# CHAT INPUT  ← sits here, new msgs appear right above
# ══════════════════════════════════════════════════════════════════
user_input = st.chat_input("Ask ARIA anything about your sales data…")

if user_input:
    now_ts = datetime.datetime.now().strftime("%I:%M %p")
    st.session_state["chat_history"].append({"role":"user","content":user_input,"ts":now_ts})

    # Render user bubble immediately
    st.markdown(f"""
    <div class="cmsg user">
      <div class="cmsg-body">
        <div class="bubble-user">{user_input}</div>
        <div class="cmsg-ts">{now_ts}</div>
      </div>
      <div class="cmsg-av av-user">👤</div>
    </div>
    """, unsafe_allow_html=True)

    # Typing
    typing_ph2 = st.empty()
    typing_ph2.markdown("""
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

    response = get_ai_response(user_input)
    typing_ph2.empty()
    clean = strip_sq(response)

    st.markdown(f"""
    <div class="cmsg">
      <div class="cmsg-av av-ai">◆</div>
      <div class="cmsg-body">
        <div class="bubble-ai">{clean}</div>
        <div class="cmsg-ts">ARIA · {now_ts}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state["chat_history"].append({"role":"assistant","content":response,"ts":now_ts})
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# DIVIDER → REPORT SECTION
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="div-line" style="margin:1.4rem 0;"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# GENERATE REPORT BANNER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gen-banner">
  <div class="gen-inner">
    <div class="gen-eyebrow">ARIA Intelligence Engine · Full Analysis</div>
    <div class="gen-title">📊 Generate Complete Business Report</div>
    <div class="gen-sub">
      One click → comprehensive AI-powered analysis of your entire dataset.<br>
      KPI scorecard · leaderboard · trends · alerts · root cause · action plan.
    </div>
    <div class="gen-pills">
      <span class="gp gp-b">📊 10 Sections</span>
      <span class="gp gp-c">🧠 AI Root Cause</span>
      <span class="gp gp-g">🏆 Leaderboard</span>
      <span class="gp gp-o">💡 Growth Ops</span>
      <span class="gp gp-p">📈 Trend Analysis</span>
      <span class="gp gp-k">🎯 Action Plan</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

c_g1, c_g2, c_g3 = st.columns([2.2, 1.8, .8])
with c_g1:
    st.markdown('<div class="btn-gen">', unsafe_allow_html=True)
    gen_report = st.button("🚀  Generate Full Report", use_container_width=True, key="gen_btn")
    st.markdown('</div>', unsafe_allow_html=True)
with c_g2:
    st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
    dl_pdf = st.button("📄  Export PDF", use_container_width=True, key="pdf_btn")
    st.markdown('</div>', unsafe_allow_html=True)
with c_g3:
    st.markdown('<div class="btn-clr">', unsafe_allow_html=True)
    if st.button("🗑️", use_container_width=True, key="clr_rpt"):
        st.session_state["bi_report_txt"] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── PROGRESS STEPS helper ──
REPORT_STEPS = [
    ("🔍","Reading salesperson data…"),
    ("📊","Computing category splits…"),
    ("📈","Analysing daily trends…"),
    ("🧠","Running AI insight engine…"),
    ("💡","Building recommendations…"),
    ("✅","Finalising report…"),
]
PDF_STEPS = [
    ("🎨","Building cover page…"),
    ("📋","Compiling KPI tables…"),
    ("📊","Rendering charts…"),
    ("🧠","Embedding AI report…"),
    ("📄","Exporting PDF bytes…"),
]

def render_steps(steps, done_count, title="Processing"):
    rows = ""
    for i, (icon, label) in enumerate(steps):
        if i < done_count:   ic, lc, di = "p-done",   "pl-done",   "✓"
        elif i == done_count: ic, lc, di = "p-active", "pl-active", icon
        else:                 ic, lc, di = "p-wait",   "pl-wait",   icon
        rows += f'<div class="pstep"><div class="picon {ic}">{di}</div><span class="{lc}">{label}</span></div>'
    return f'<div class="prog-wrap"><div class="prog-title">{title}</div><div class="prog">{rows}</div></div>'

# ── GENERATE REPORT ──
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
        prog_ph.markdown(render_steps(REPORT_STEPS, si, "Generating ARIA Report"), unsafe_allow_html=True)
        time.sleep(0.28)

    try:
        report_txt = ask_groq(FULL_REPORT_PROMPT, SYSTEM_PROMPT, chat_history=[])
    except Exception as e:
        report_txt = f'<span style="color:#FF6B6B;">⚠️ Report generation failed: {str(e)[:300]}</span>'

    prog_ph.markdown(render_steps(REPORT_STEPS, len(REPORT_STEPS), "Generating ARIA Report"), unsafe_allow_html=True)
    time.sleep(0.3)
    prog_ph.empty()
    st.session_state["bi_report_txt"] = report_txt
    st.rerun()

# ── DISPLAY REPORT ──
if st.session_state.get("bi_report_txt"):
    rpt = st.session_state["bi_report_txt"]

    st.markdown(f"""
    <div class="report-card">
      <div class="rh">
        <div class="rh-left">
          <div class="rh-icon">◆</div>
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
            st.markdown(f'<div class="rsec" style="padding:.5rem 0;">{intro}</div>', unsafe_allow_html=True)
        i = 1
        while i < len(parts):
            header  = parts[i].strip()
            content = parts[i+1].strip() if (i+1) < len(parts) else ""
            clean_h = re.sub(r'<[^>]+>', '', header).strip().lstrip('─').strip()
            with st.expander(f"▸ {clean_h}", expanded=(i <= 3)):
                st.markdown(f'<div class="rsec">{content}</div>', unsafe_allow_html=True)
            i += 2
    else:
        st.markdown(f'<div class="rsec">{rpt}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PDF BUILDER  (same logic as before, no changes)
# ══════════════════════════════════════════════════════════════════
def build_pdf(report_txt: str, fname: str):
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
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                         TableStyle, Image as RLImage, HRFlowable, PageBreak)
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
    F  = "DJ" if USE_DJ else "Helvetica"
    FB = "DJB" if USE_DJ else "Helvetica-Bold"
    INR = "Rs."

    C_BG   = colors.HexColor("#080C1A"); C_DARK  = colors.HexColor("#0D1225")
    C_PANEL= colors.HexColor("#111828"); C_BLUE  = colors.HexColor("#4F8CFF")
    C_CYAN = colors.HexColor("#00D4FF"); C_GREEN = colors.HexColor("#00FFC6")
    C_GOLD = colors.HexColor("#FFD166"); C_RED   = colors.HexColor("#FF6B6B")
    C_TEXT = colors.HexColor("#9BA8C4"); C_WHITE = colors.HexColor("#F0F4FF")
    C_MUTED= colors.HexColor("#5C6884"); GRID    = colors.HexColor("#1A2242")

    def S(n,**kw):  return ParagraphStyle(n, fontName=F,  **kw)
    def SB(n,**kw): return ParagraphStyle(n, fontName=FB, **kw)
    s_h1   = SB("h1",  fontSize=11, textColor=C_CYAN,  spaceBefore=14, spaceAfter=6)
    s_body = S("body", fontSize=8.5, textColor=C_TEXT,  leading=13, spaceAfter=3)
    s_sub  = S("sub",  fontSize=8,   textColor=C_MUTED, spaceAfter=3)

    buf = _io.BytesIO()
    try:
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm,
                                 topMargin=1.6*cm, bottomMargin=2.4*cm)
    except Exception as e:
        return None, f"PDF init failed: {e}"

    story = []; W = A4[0] - 3.6*cm

    try:
        ct = Table([[Paragraph("ARIA Intelligence Report",
                     SB("ct", fontSize=18, textColor=C_WHITE, leading=22))]],
                   colWidths=[W], rowHeights=[3.2*cm])
        ct.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),C_BLUE),("LEFTPADDING",(0,0),(0,0),18),("VALIGN",(0,0),(0,0),"MIDDLE")]))
        story += [ct, Spacer(1,.4*cm),
                  Paragraph(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}", s_sub),
                  Paragraph(f"File: {fname}", s_sub), Spacer(1,.3*cm),
                  HRFlowable(width=W, thickness=1.5, color=C_BLUE, spaceAfter=10)]
    except Exception as e:
        warns.append(f"Cover: {e}")

    try:
        story.append(Paragraph("Key Performance Indicators", s_h1))
        kd = [["Metric","Value","Metric","Value"],
              ["Total Revenue",f"{INR}{total_rev:,.0f}","Daily Avg",f"{INR}{avg_daily:,.0f}"],
              ["YTD Revenue",f"{INR}{ytd:,.0f}","Top Seller",top_seller],
              ["Active Sellers",str(active_sellers),"Rev/Seller",f"{INR}{rev_per_seller:,.0f}"],
              ["Never Sold",str(len(never_sold)),"Bad Day",str(len(bad_day))],
              ["Top Value",f"{INR}{top_val:,.0f}","Multiplier",f"{top_multiplier:.2f}x avg"]]
        cw = [W*.22,W*.28,W*.22,W*.28]
        kt = Table(kd,colWidths=cw)
        kt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),C_DARK),("TEXTCOLOR",(0,0),(-1,0),C_CYAN),
            ("FONTNAME",(0,0),(-1,0),FB),("FONTNAME",(0,1),(-1,-1),F),
            ("FONTSIZE",(0,0),(-1,-1),8),("TEXTCOLOR",(0,1),(-1,-1),C_WHITE),
            ("TEXTCOLOR",(1,1),(1,-1),C_GREEN),("TEXTCOLOR",(3,1),(3,-1),C_GOLD),
            ("BACKGROUND",(0,2),(-1,2),C_PANEL),("BACKGROUND",(0,4),(-1,4),C_PANEL),
            ("GRID",(0,0),(-1,-1),.3,GRID),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)
        ]))
        story += [kt, Spacer(1,.5*cm)]
    except Exception as e:
        warns.append(f"KPI: {e}")

    try:
        story.append(Paragraph("Salesperson Leaderboard", s_h1))
        if not totals.empty:
            t_sum = totals["Total"].sum()
            lh = [["Rank","Salesperson","Revenue","Share%","vs Avg"]]
            lrows = []
            for i, rw in enumerate(totals.head(20).itertuples()):
                share = (rw.Total/t_sum*100) if t_sum else 0
                vs    = ((rw.Total/rev_per_seller-1)*100) if rev_per_seller else 0
                lrows.append([f"#{i+1}", rw.Salesperson, f"{INR}{rw.Total:,.0f}",
                               f"{share:.1f}%", f"+{vs:.0f}%" if vs>=0 else f"{vs:.0f}%"])
            lt = Table(lh+lrows, colWidths=[W*.09,W*.36,W*.24,W*.16,W*.15])
            lt.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),C_DARK),("TEXTCOLOR",(0,0),(-1,0),C_GOLD),
                ("FONTNAME",(0,0),(-1,0),FB),("FONTNAME",(0,1),(-1,-1),F),
                ("FONTSIZE",(0,0),(-1,-1),8),("TEXTCOLOR",(0,1),(-1,-1),C_WHITE),
                ("TEXTCOLOR",(2,1),(2,-1),C_GREEN),
                ("BACKGROUND",(0,1),(-1,1),colors.HexColor("#071A0A")),
                ("GRID",(0,0),(-1,-1),.3,GRID),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),6)
            ]))
            story.append(lt)
        story.append(PageBreak())
    except Exception as e:
        warns.append(f"Leaderboard: {e}")

    try:
        story.append(Paragraph("Category Performance", s_h1))
        if not cat_totals.empty:
            c_sum = float(cat_totals["Total"].sum()); c_max = float(cat_totals["Total"].max())
            ch = [["Category","Revenue","Share%","Health"]]
            crows = []
            for rw in cat_totals.itertuples():
                sh = (rw.Total/c_sum*100) if c_sum else 0
                r  = (rw.Total/c_max)     if c_max  else 0
                ht = "Strong" if r>=.6 else ("Moderate" if r>=.25 else "Low")
                crows.append([str(rw.Category), f"{INR}{rw.Total:,.0f}", f"{sh:.1f}%", ht])
            ctt = Table(ch+crows, colWidths=[W*.32,W*.28,W*.18,W*.22])
            ctt.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),C_DARK),("TEXTCOLOR",(0,0),(-1,0),C_CYAN),
                ("FONTNAME",(0,0),(-1,0),FB),("FONTNAME",(0,1),(-1,-1),F),
                ("FONTSIZE",(0,0),(-1,-1),8),("TEXTCOLOR",(0,1),(-1,-1),C_WHITE),
                ("TEXTCOLOR",(1,1),(1,-1),C_GREEN),
                ("GRID",(0,0),(-1,-1),.3,GRID),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),6)
            ]))
            story.append(ctt)
        story += [Spacer(1,.5*cm)]
    except Exception as e:
        warns.append(f"Category: {e}")

    CHART_BG="#080C1A"; PANEL_BG="#0D1225"; TICK="#5C6884"; GRIDC="#1A2242"

    def fig_bytes(fig):
        ib = _io.BytesIO()
        fig.savefig(ib, format="png", bbox_inches="tight", dpi=150, facecolor=CHART_BG)
        ib.seek(0); plt.close(fig); return ib

    try:
        story.append(Paragraph("Daily Sales Trend", s_h1))
        if len(daily) > 0:
            fig, ax = plt.subplots(figsize=(13,3.8), facecolor=CHART_BG)
            ax.set_facecolor(PANEL_BG)
            xs = list(range(len(daily))); ys = list(daily.values)
            ax.fill_between(xs, ys, alpha=.1, color="#4F8CFF")
            ax.plot(xs, ys, color="#00D4FF", linewidth=2.2, zorder=4)
            ax.scatter(xs, ys, color="#4F8CFF", s=20, zorder=5)
            if len(daily) >= 7:
                ma7 = daily.rolling(7).mean()
                ax.plot(xs, ma7, color="#FFD166", linewidth=1.5, linestyle="--", label="7-Day MA", zorder=3)
                ax.legend(facecolor=PANEL_BG, edgecolor=GRIDC, labelcolor="#9BA8C4", fontsize=8)
            ax.tick_params(colors=TICK, labelsize=7)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{v/1e3:.0f}K" if v>=1000 else str(int(v))))
            for sp in ax.spines.values(): sp.set_color(GRIDC)
            ax.grid(axis="y", color=GRIDC, linewidth=.5, alpha=.7)
            ax.set_xlabel("Day", color=TICK, fontsize=7); ax.set_ylabel("Revenue", color=TICK, fontsize=7)
            story.append(RLImage(fig_bytes(fig), width=W, height=4.5*cm))
        story.append(Spacer(1,.4*cm))
    except Exception as e:
        warns.append(f"Trend chart: {e}")

    try:
        story.append(Paragraph("Category Revenue Breakdown", s_h1))
        if not cat_totals.empty:
            cats = cat_totals["Category"].astype(str).tolist()
            vals = [float(v) for v in cat_totals["Total"].tolist()]
            PAL  = ["#4F8CFF","#7B61FF","#00D4FF","#00FFC6","#FFD166","#FF6B6B","#A78BFA","#34D399"]
            fig2, ax2 = plt.subplots(figsize=(12, max(3, len(cats)*.55)), facecolor=CHART_BG)
            ax2.set_facecolor(PANEL_BG)
            bars = ax2.barh(cats, vals, color=[PAL[i%len(PAL)] for i in range(len(cats))], alpha=.85, edgecolor="none", height=.6)
            for bar, val in zip(bars, vals):
                ax2.text(bar.get_width()*1.012, bar.get_y()+bar.get_height()/2,
                         f"{INR}{val/1e3:.1f}K", va="center", color="#9BA8C4", fontsize=7.5)
            ax2.tick_params(colors=TICK, labelsize=7)
            for sp in ax2.spines.values(): sp.set_color(GRIDC)
            ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{v/1e3:.0f}K"))
            ax2.grid(axis="x", color=GRIDC, linewidth=.5, alpha=.7)
            story.append(RLImage(fig_bytes(fig2), width=W, height=max(4*cm, len(cats)*.7*cm)))
        story.append(PageBreak())
    except Exception as e:
        warns.append(f"Cat chart: {e}")

    try:
        story.append(Paragraph("Zero-Sales Alerts", s_h1))
        a_data = ([["Salesperson","Alert Type","Urgency","Action"]]
                  + [[n,"Never Sold","CRITICAL","Immediate review"] for n in never_sold]
                  + [[n,"Had Bad Day","MONITOR","Follow up this week"] for n in bad_day])
        if len(a_data) > 1:
            zt = Table(a_data, colWidths=[W*.28,W*.20,W*.16,W*.36])
            zt.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),C_DARK),("TEXTCOLOR",(0,0),(-1,0),C_RED),
                ("FONTNAME",(0,0),(-1,0),FB),("FONTNAME",(0,1),(-1,-1),F),
                ("FONTSIZE",(0,0),(-1,-1),8),("TEXTCOLOR",(0,1),(-1,-1),C_WHITE),
                ("GRID",(0,0),(-1,-1),.3,colors.HexColor("#2A1020")),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),6)
            ]))
            story.append(zt)
        else:
            story.append(Paragraph("No zero-sales alerts — all sellers have recorded revenue.", s_body))
        story += [Spacer(1,.6*cm), HRFlowable(width=W, thickness=1, color=C_BLUE, spaceAfter=10)]
    except Exception as e:
        warns.append(f"Alerts: {e}")

    try:
        story.append(Paragraph("AI Intelligence Analysis", s_h1))
        story.append(Spacer(1,.2*cm))
        clean = re.sub(r'<[^>]+>',' ', report_txt or "").strip()
        clean = re.sub(r'\s+', ' ', clean)
        for para in clean.split('\n'):
            p = para.strip()
            if p:
                story.append(Paragraph(p, s_body))
                story.append(Spacer(1,.06*cm))
    except Exception as e:
        warns.append(f"AI text: {e}")

    def draw_page(cv, doc_obj):
        try:
            cv.saveState()
            cv.setFillColor(C_BG); cv.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            cv.setFillColor(C_PANEL); cv.rect(0, 0, A4[0], 1.8*cm, fill=1, stroke=0)
            cv.setStrokeColor(C_BLUE); cv.setLineWidth(.8)
            cv.line(1.8*cm, 1.8*cm, A4[0]-1.8*cm, 1.8*cm)
            cv.setFont(F if USE_DJ else "Helvetica", 6.5); cv.setFillColor(C_MUTED)
            cv.drawCentredString(A4[0]/2, .7*cm, f"ARIA Sales Intelligence · {datetime.datetime.now().strftime('%d %B %Y')} · LLaMA 3.3-70B")
            cv.setFillColor(C_CYAN); cv.drawRightString(A4[0]-1.8*cm, .7*cm, f"Page {doc_obj.page}")
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

# ── TRIGGER PDF ──
if dl_pdf:
    report_src = st.session_state.get("bi_report_txt") or ""
    if not report_src:
        with st.spinner("Generating summary for PDF…"):
            try:
                report_src = ask_groq("Provide a concise executive summary in 5 key bullet points.",
                                       SYSTEM_PROMPT, chat_history=[])
            except Exception as e:
                report_src = f"Summary unavailable: {e}"

    pdf_prog = st.empty()
    for si in range(len(PDF_STEPS)):
        pdf_prog.markdown(render_steps(PDF_STEPS, si, "Building PDF"), unsafe_allow_html=True)
        time.sleep(0.22)

    pdf_bytes, err = build_pdf(report_src, filename)
    pdf_prog.markdown(render_steps(PDF_STEPS, len(PDF_STEPS), "Building PDF"), unsafe_allow_html=True)
    time.sleep(0.3); pdf_prog.empty()

    if pdf_bytes is None:
        st.error("PDF failed. Full traceback:")
        st.code(err or "Unknown error", language="text")
    else:
        if err: st.warning(err)
        st.success("✅ PDF ready!")
        st.download_button(
            label="⬇️  Download ARIA Intelligence Report (PDF)",
            data=pdf_bytes,
            file_name=f"ARIA_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ── BOTTOM NAV ──
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="bot-nav">', unsafe_allow_html=True)
if st.button("← Back to Dashboard", use_container_width=True, key="bot_nav"):
    st.switch_page("pages/1_Dashboard.py")
st.markdown('</div>', unsafe_allow_html=True)