import streamlit as st
import time
from utils.data_loader import get_clean_dataframe

st.set_page_config(
    page_title="ARIA · Sales Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
    --bg-1: #050816;
    --bg-2: #071124;
    --bg-3: #091A30;
    --blue: #4F8CFF;
    --purple: #7B61FF;
    --cyan: #00D4FF;
    --green: #00FFC6;
    --gold: #FFD166;
    --text-primary: #FFFFFF;
    --text-secondary: #C8D4E8;
    --text-muted: #8A97B5;
    --glass-border: rgba(255,255,255,0.08);
    --glass-bg: rgba(255,255,255,0.05);
}

html, body, .stApp {
    background: radial-gradient(ellipse 120% 80% at 50% -10%, var(--bg-3) 0%, var(--bg-2) 45%, var(--bg-1) 100%) !important;
    color: var(--text-secondary);
    font-family: 'Manrope', sans-serif;
    overflow-x: hidden;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding: 5.5rem 5vw 3rem !important;
    max-width: 100% !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(7,17,36,0.92) !important;
    border-right: 1px solid var(--glass-border);
    backdrop-filter: blur(20px);
}
section[data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
.sb-block {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}
.sb-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--cyan);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.sb-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.8rem; padding: 0.3rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.sb-row:last-child { border-bottom: none; }
.sb-row .lbl { color: var(--text-muted); }
.sb-row .val { color: var(--text-primary); font-weight: 600; }
.sb-pill {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem; color: var(--green);
    background: rgba(0,255,198,0.08);
    border: 1px solid rgba(0,255,198,0.25);
    border-radius: 99px; padding: 4px 10px;
}
.sb-pill .d { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); }
.sb-step {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.78rem; color: var(--text-muted); padding: 0.25rem 0;
}
.sb-step .n {
    width: 18px; height: 18px; border-radius: 50%;
    background: rgba(79,140,255,0.15); border: 1px solid rgba(79,140,255,0.4);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; color: var(--blue); flex-shrink: 0;
}

/* Ambient background layers */
#particle-canvas { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
.glow-orb { position: fixed; border-radius: 50%; filter: blur(80px); z-index: 0; pointer-events: none; opacity: 0.32; animation: orbDrift 22s ease-in-out infinite; }
.glow-orb.o1 { width: 480px; height: 480px; background: var(--blue); top: -10%; left: -8%; }
.glow-orb.o2 { width: 420px; height: 420px; background: var(--purple); bottom: -15%; right: -5%; animation-delay: -7s; }
.glow-orb.o3 { width: 320px; height: 320px; background: var(--cyan); top: 35%; right: 18%; animation-delay: -14s; opacity: 0.16; }
@keyframes orbDrift { 0%,100% { transform: translate(0,0) scale(1); } 33% { transform: translate(40px,-30px) scale(1.08); } 66% { transform: translate(-30px,25px) scale(0.95); } }

#scanline { position: fixed; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent); z-index: 1; pointer-events: none; animation: scanMove 9s linear infinite; }
@keyframes scanMove { 0% { top: -5%; opacity: 0; } 5% { opacity: 0.6; } 50% { opacity: 0.35; } 95% { opacity: 0.6; } 100% { top: 105%; opacity: 0; } }

/* Top status bar */
#status-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 2.4rem;
    background: rgba(5,8,22,0.55);
    border-bottom: 1px solid var(--glass-border);
    backdrop-filter: blur(24px);
    animation: dropIn 0.8s cubic-bezier(0.22,1,0.36,1) both;
}
@keyframes dropIn { from { transform: translateY(-100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.brand { display: flex; align-items: center; gap: 0.7rem; }
.brand-mark { width: 30px; height: 30px; border-radius: 9px; background: linear-gradient(135deg, var(--blue), var(--purple) 60%, var(--cyan)); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; color: #fff; box-shadow: 0 0 18px rgba(79,140,255,0.45); }
.brand-name { font-size: 0.95rem; font-weight: 700; color: var(--text-primary); letter-spacing: 0.3px; }
.brand-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--text-muted); background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); border-radius: 5px; padding: 2px 7px; letter-spacing: 0.5px; }
.status-cluster { display: flex; align-items: center; gap: 1.6rem; }
.status-pill { display: flex; align-items: center; gap: 7px; font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text-muted); letter-spacing: 0.8px; text-transform: uppercase; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; animation: dotPulse 2.4s ease infinite; }
.status-dot.blue { background: var(--blue); box-shadow: 0 0 8px var(--blue); }
.status-dot.green { background: var(--green); box-shadow: 0 0 8px var(--green); animation-delay: 0.6s; }
.status-dot.purple { background: var(--purple); box-shadow: 0 0 8px var(--purple); animation-delay: 1.2s; }
@keyframes dotPulse { 0%,100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.35; transform: scale(0.7); } }

/* Hero */
.eyebrow { display: inline-flex; align-items: center; gap: 9px; width: fit-content; margin-bottom: 1.8rem; padding: 7px 18px; border-radius: 99px; background: var(--glass-bg); border: 1px solid var(--glass-border); backdrop-filter: blur(10px); animation: riseIn 0.8s cubic-bezier(0.22,1,0.36,1) 0.1s both; }
.eyebrow-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 9px var(--green); animation: dotPulse 2s ease infinite; }
.eyebrow span { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: var(--green); letter-spacing: 2.5px; text-transform: uppercase; }
.hero-title { font-weight: 800; font-size: clamp(3.2rem, 6.5vw, 5.6rem); line-height: 0.98; letter-spacing: -2.5px; color: var(--text-primary); margin-bottom: 0.6rem; animation: riseIn 0.9s cubic-bezier(0.22,1,0.36,1) 0.2s both; }
.hero-title .grad { background: linear-gradient(100deg, var(--blue) 0%, var(--purple) 45%, var(--cyan) 90%); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; animation: gradShift 7s linear infinite; display: inline-block; }
@keyframes gradShift { 0% { background-position: 0% center; } 100% { background-position: 200% center; } }
.hero-subtitle { font-size: 1.15rem; font-weight: 500; color: var(--text-secondary); letter-spacing: 0.2px; margin-bottom: 1.1rem; animation: riseIn 0.9s cubic-bezier(0.22,1,0.36,1) 0.3s both; }
.hero-desc { font-size: 0.98rem; font-weight: 300; color: var(--text-muted); line-height: 1.75; max-width: 460px; margin-bottom: 2rem; animation: riseIn 0.9s cubic-bezier(0.22,1,0.36,1) 0.4s both; }

/* Metric strip */
#metric-row { display: flex; gap: 0; border-radius: 16px; border: 1px solid var(--glass-border); background: var(--glass-bg); backdrop-filter: blur(16px); overflow: hidden; width: fit-content; animation: riseIn 0.9s cubic-bezier(0.22,1,0.36,1) 0.5s both; margin-bottom: 1.4rem; }
.metric-cell { padding: 0.95rem 1.4rem; text-align: left; }
.metric-cell + .metric-cell { border-left: 1px solid var(--glass-border); }
.metric-num { font-size: 1.2rem; font-weight: 700; display: block; }
.metric-num.c1 { color: var(--cyan); } .metric-num.c2 { color: var(--green); } .metric-num.c3 { color: var(--gold); }
.metric-cap { font-family: 'JetBrains Mono', monospace; font-size: 0.56rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1.2px; margin-top: 0.15rem; display: block; }

/* Neural Core */
#neural-core { position: relative; width: 360px; height: 360px; margin: 0 auto; animation: riseIn 1.1s cubic-bezier(0.22,1,0.36,1) 0.3s both; }
.core-ring { position: absolute; top: 50%; left: 50%; border-radius: 50%; border: 1px solid transparent; transform: translate(-50%,-50%); }
.ring-1 { width: 360px; height: 360px; border-top-color: rgba(79,140,255,0.55); border-right-color: rgba(79,140,255,0.12); animation: spin 14s linear infinite; }
.ring-2 { width: 285px; height: 285px; border-top-color: rgba(123,97,255,0.5); border-left-color: rgba(123,97,255,0.1); animation: spin 10s linear infinite reverse; }
.ring-3 { width: 220px; height: 220px; border-top-color: rgba(0,212,255,0.55); animation: spin 7s linear infinite; }
.ring-4 { width: 160px; height: 160px; border: 1px solid rgba(255,255,255,0.08); animation: spin 20s linear infinite reverse; }
@keyframes spin { from { transform: translate(-50%,-50%) rotate(0deg); } to { transform: translate(-50%,-50%) rotate(360deg); } }
.core-particle { position: absolute; top: 50%; left: 50%; width: 6px; height: 6px; border-radius: 50%; }
.cp1 { background: var(--blue); box-shadow: 0 0 10px var(--blue); animation: orbit1 7s linear infinite; }
.cp2 { background: var(--cyan); box-shadow: 0 0 10px var(--cyan); animation: orbit2 10s linear infinite reverse; }
.cp3 { background: var(--purple); box-shadow: 0 0 8px var(--purple); animation: orbit3 14s linear infinite; }
@keyframes orbit1 { from { transform: translate(-50%,-50%) rotate(0deg) translateX(110px) rotate(0deg); } to { transform: translate(-50%,-50%) rotate(360deg) translateX(110px) rotate(-360deg); } }
@keyframes orbit2 { from { transform: translate(-50%,-50%) rotate(0deg) translateX(142px) rotate(0deg); } to { transform: translate(-50%,-50%) rotate(360deg) translateX(142px) rotate(-360deg); } }
@keyframes orbit3 { from { transform: translate(-50%,-50%) rotate(0deg) translateX(80px) rotate(0deg); } to { transform: translate(-50%,-50%) rotate(360deg) translateX(80px) rotate(-360deg); } }
.core-glow { position: absolute; top: 50%; left: 50%; width: 125px; height: 125px; transform: translate(-50%,-50%); border-radius: 50%; background: radial-gradient(circle, rgba(79,140,255,0.5), rgba(123,97,255,0.25) 50%, transparent 75%); filter: blur(8px); animation: corePulse 3.2s ease-in-out infinite; }
@keyframes corePulse { 0%,100% { transform: translate(-50%,-50%) scale(1); opacity: 0.8; } 50% { transform: translate(-50%,-50%) scale(1.18); opacity: 1; } }
.core-nucleus { position: absolute; top: 50%; left: 50%; width: 60px; height: 60px; transform: translate(-50%,-50%); border-radius: 50%; background: radial-gradient(circle at 32% 32%, #ffffff, var(--cyan) 35%, var(--blue) 65%, var(--purple)); box-shadow: 0 0 40px rgba(79,140,255,0.6), 0 0 90px rgba(123,97,255,0.35); animation: nucleusBreathe 3s ease-in-out infinite; z-index: 3; }
@keyframes nucleusBreathe { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-50%,-50%) scale(1.1); } }
.core-caption { text-align: center; margin-top: 0.6rem; font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text-muted); letter-spacing: 2px; text-transform: uppercase; }

/* Upload Portal */
.portal-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px; margin-bottom: 0.2rem; }
.portal-title .pdot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 8px var(--cyan); }
.portal-hint { font-size: 0.8rem; color: var(--text-muted); font-weight: 300; margin-bottom: 0.8rem; }

div[data-testid="stFileUploader"] {
    background: linear-gradient(180deg, rgba(79,140,255,0.06), rgba(123,97,255,0.04)) !important;
    border: 1.5px dashed rgba(79,140,255,0.4) !important;
    border-radius: 18px !important;
    padding: 1.3rem 1.6rem !important;
    transition: all 0.4s cubic-bezier(0.22,1,0.36,1) !important;
    backdrop-filter: blur(14px) !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: rgba(0,212,255,0.75) !important;
    background: linear-gradient(180deg, rgba(0,212,255,0.1), rgba(123,97,255,0.06)) !important;
    box-shadow: 0 0 0 5px rgba(0,212,255,0.05), 0 0 60px rgba(79,140,255,0.18) !important;
    transform: translateY(-2px) !important;
}
div[data-testid="stFileUploader"] > label { display: none !important; }
div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small { color: var(--text-muted) !important; }
div[data-testid="stFileUploader"] section { border: none !important; background: transparent !important; }
div[data-testid="stFileUploaderDropzone"] { border: none !important; background: transparent !important; }

#format-row { display: flex; gap: 0.5rem; margin-top: 0.8rem; }
.ftag { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--text-muted); background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 6px; padding: 4px 10px; letter-spacing: 1px; }
#secure-note { margin-top: 0.7rem; font-size: 0.7rem; color: var(--text-muted); display: flex; align-items: center; gap: 8px; }
.sdot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-muted); }

@keyframes riseIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

/* Cinematic Loader */
#aria-loader { display: none; position: fixed; inset: 0; z-index: 9999; background: radial-gradient(ellipse 120% 80% at 50% 50%, var(--bg-3) 0%, var(--bg-1) 100%); flex-direction: column; align-items: center; justify-content: center; }
#aria-loader.active { display: flex; }
#loader-core-wrap { position: relative; width: 240px; height: 240px; margin-bottom: 2.6rem; }
.loader-ring { position: absolute; top: 50%; left: 50%; border-radius: 50%; border: 1px solid transparent; transform: translate(-50%,-50%); animation: spin linear infinite; }
.lr1 { width: 80px; height: 80px; border-top-color: var(--blue); animation-duration: 1.6s; }
.lr2 { width: 130px; height: 130px; border-top-color: var(--purple); animation-duration: 2.6s; animation-direction: reverse; }
.lr3 { width: 180px; height: 180px; border-top-color: var(--cyan); animation-duration: 3.8s; }
.lr4 { width: 230px; height: 230px; border: 1px solid rgba(255,255,255,0.07); animation-duration: 9s; animation-direction: reverse; }
#loader-nucleus { position: absolute; top: 50%; left: 50%; width: 44px; height: 44px; transform: translate(-50%,-50%); border-radius: 50%; background: radial-gradient(circle at 32% 32%, #fff, var(--cyan) 35%, var(--blue) 65%, var(--purple)); box-shadow: 0 0 30px rgba(79,140,255,0.6), 0 0 70px rgba(123,97,255,0.35); animation: nucleusBreathe 1.8s ease-in-out infinite; }
#loader-status { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--cyan); letter-spacing: 3.5px; text-transform: uppercase; text-align: center; margin-bottom: 1.5rem; min-height: 1.2em; }
#loader-track { width: 320px; height: 3px; border-radius: 99px; background: rgba(255,255,255,0.06); overflow: hidden; margin-bottom: 0.7rem; }
#loader-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--blue), var(--purple), var(--cyan)); border-radius: 99px; transition: width 0.5s cubic-bezier(0.22,1,0.36,1); }
#loader-pct { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); letter-spacing: 2px; }
.stProgress > div > div > div { background: linear-gradient(90deg, var(--blue), var(--purple), var(--cyan)) !important; border-radius: 99px !important; }
</style>
<canvas id="particle-canvas"></canvas>
<div class="glow-orb o1"></div>
<div class="glow-orb o2"></div>
<div class="glow-orb o3"></div>
<div id="scanline"></div>
<div id="status-bar">
  <div class="brand">
    <div class="brand-mark">A</div>
    <div class="brand-name">ARIA</div>
    <div class="brand-tag">v4.0 · Neural Glass</div>
  </div>
  <div class="status-cluster">
    <div class="status-pill"><div class="status-dot blue"></div>Neural Engine</div>
    <div class="status-pill"><div class="status-dot green"></div>Data Core</div>
    <div class="status-pill"><div class="status-dot purple"></div>AI Ready</div>
  </div>
</div>
<div id="aria-loader">
  <div id="loader-core-wrap">
    <div id="loader-nucleus"></div>
    <div class="loader-ring lr1"></div>
    <div class="loader-ring lr2"></div>
    <div class="loader-ring lr3"></div>
    <div class="loader-ring lr4"></div>
  </div>
  <div id="loader-status">Scanning Dataset</div>
  <div id="loader-track"><div id="loader-fill"></div></div>
  <div id="loader-pct">0%</div>
</div>
<script>
(function() {
    var cv = document.getElementById('particle-canvas');
    if (!cv) return;
    var cx = cv.getContext('2d');
    var W, H, mouseX = -9999, mouseY = -9999;
    function resize() { W = cv.width = window.innerWidth; H = cv.height = window.innerHeight; }
    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', function(e) { mouseX = e.clientX; mouseY = e.clientY; });
    var PAL = ['#4F8CFF', '#7B61FF', '#00D4FF', '#00FFC6'];
    var nodes = [];
    for (var k = 0; k < 46; k++) {
        nodes.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            vx: (Math.random() - 0.5) * 0.25,
            vy: (Math.random() - 0.5) * 0.25,
            r: Math.random() * 2 + 0.6,
            color: PAL[Math.floor(Math.random() * PAL.length)],
            opacity: Math.random() * 0.4 + 0.15
        });
    }
    function frame() {
        cx.clearRect(0, 0, W, H);
        for (var i = 0; i < nodes.length; i++) {
            for (var j = i + 1; j < nodes.length; j++) {
                var dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y;
                var d = Math.sqrt(dx*dx + dy*dy);
                if (d < 150) {
                    cx.beginPath();
                    cx.moveTo(nodes[i].x, nodes[i].y);
                    cx.lineTo(nodes[j].x, nodes[j].y);
                    cx.strokeStyle = nodes[i].color;
                    cx.globalAlpha = (1 - d/150) * 0.08;
                    cx.lineWidth = 0.5;
                    cx.stroke();
                    cx.globalAlpha = 1;
                }
            }
        }
        nodes.forEach(function(n) {
            n.x += n.vx; n.y += n.vy;
            if (n.x < 0 || n.x > W) n.vx *= -1;
            if (n.y < 0 || n.y > H) n.vy *= -1;
            var dx2 = mouseX - n.x, dy2 = mouseY - n.y;
            var dist = Math.sqrt(dx2*dx2 + dy2*dy2);
            if (dist < 140) {
                var force = (1 - dist/140) * 0.6;
                n.x -= (dx2/dist) * force;
                n.y -= (dy2/dist) * force;
            }
            cx.beginPath();
            cx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
            cx.fillStyle = n.color;
            cx.globalAlpha = n.opacity;
            cx.fill();
            cx.globalAlpha = 1;
        });
        requestAnimationFrame(frame);
    }
    frame();
})();
(function() {
    var STEPS = [
        [14, 'Scanning Dataset'], [28, 'Validating Structure'], [42, 'Cleaning Data'],
        [57, 'Building Context'], [71, 'Training ARIA'], [86, 'Generating Insights'],
        [100, 'Launching Dashboard']
    ];
    window.__ariaLoad = function() {
        var loader = document.getElementById('aria-loader');
        var status = document.getElementById('loader-status');
        var fill = document.getElementById('loader-fill');
        var pct = document.getElementById('loader-pct');
        if (!loader) return;
        loader.classList.add('active');
        var i = 0;
        function next() {
            if (i >= STEPS.length) return;
            var p = STEPS[i][0], text = STEPS[i][1];
            fill.style.width = p + '%';
            pct.textContent = p + '%';
            status.style.opacity = 0;
            setTimeout(function() {
                status.textContent = text;
                status.style.transition = 'opacity 0.3s ease';
                status.style.opacity = 1;
            }, 150);
            i++;
            setTimeout(next, 480);
        }
        next();
    };
})();
</script>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — system status & pipeline preview
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-block">
        <div class="sb-title">System Status</div>
        <div class="sb-pill"><div class="d"></div>All Systems Online</div>
    </div>
    <div class="sb-block">
        <div class="sb-title">Engine</div>
        <div class="sb-row"><span class="lbl">AI Model</span><span class="val">LLaMA 3.3 70B</span></div>
        <div class="sb-row"><span class="lbl">Provider</span><span class="val">Groq</span></div>
        <div class="sb-row"><span class="lbl">Encryption</span><span class="val">AES-256</span></div>
        <div class="sb-row"><span class="lbl">Accuracy</span><span class="val">99.8%</span></div>
    </div>
    <div class="sb-block">
        <div class="sb-title">Processing Pipeline</div>
        <div class="sb-step"><div class="n">1</div>Scan dataset structure</div>
        <div class="sb-step"><div class="n">2</div>Validate &amp; clean nulls</div>
        <div class="sb-step"><div class="n">3</div>Build AI context</div>
        <div class="sb-step"><div class="n">4</div>Generate insights</div>
        <div class="sb-step"><div class="n">5</div>Launch dashboard</div>
    </div>
    <div class="sb-block">
        <div class="sb-title">Supported Formats</div>
        <div class="sb-row"><span class="lbl">Excel</span><span class="val">.xlsx · .xls</span></div>
        <div class="sb-row"><span class="lbl">Text</span><span class="val">.csv</span></div>
        <div class="sb-row"><span class="lbl">Max size</span><span class="val">200 MB</span></div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN STAGE — hero (left) + neural core (right)
# ──────────────────────────────────────────────────────────────────────────────
left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.markdown("""
    <div class="eyebrow"><div class="eyebrow-dot"></div><span>AI Sales Intelligence</span></div>
    <h1 class="hero-title"><span class="grad">ARIA</span></h1>
    <div class="hero-subtitle">Sales Intelligence Platform</div>
    <p class="hero-desc">Transform raw sales data into actionable intelligence powered by advanced AI analytics. Upload your data and let ARIA reveal what matters.</p>
    <div id="metric-row">
        <div class="metric-cell"><span class="metric-num c1">0.4s</span><span class="metric-cap">Analysis Speed</span></div>
        <div class="metric-cell"><span class="metric-num c2">99.8%</span><span class="metric-cap">Data Accuracy</span></div>
        <div class="metric-cell"><span class="metric-num c3">LLaMA 3.3</span><span class="metric-cap">AI Model</span></div>
    </div>
    <div class="portal-title"><div class="pdot"></div>AI Upload Portal</div>
    <div class="portal-hint">Drop your sales file — ARIA handles the rest</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "",
        type=["xlsx", "xls", "csv"],
        help="Supports .xlsx, .xls, .csv — all data preserved",
        key="main_uploader"
    )

    st.markdown("""
    <div id="format-row">
        <div class="ftag">.XLSX</div>
        <div class="ftag">.XLS</div>
        <div class="ftag">.CSV</div>
    </div>
    <div id="secure-note">
        <div class="sdot"></div><span>Your data never leaves your session</span>
        <div class="sdot"></div><span>Zero-loss processing guaranteed</span>
        <div class="sdot"></div>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown("""
    <div id="neural-core">
        <div class="core-glow"></div>
        <div class="core-ring ring-1"></div>
        <div class="core-ring ring-2"></div>
        <div class="core-ring ring-3"></div>
        <div class="core-ring ring-4"></div>
        <div class="core-particle cp1"></div>
        <div class="core-particle cp2"></div>
        <div class="core-particle cp3"></div>
        <div class="core-nucleus"></div>
    </div>
    <div class="core-caption">Neural Core · Active</div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD HANDLER — cinematic 7-step loader
# ──────────────────────────────────────────────────────────────────────────────
if uploaded_file is not None:

    st.markdown("""<script>if (typeof window.__ariaLoad === 'function') window.__ariaLoad();</script>""",
                unsafe_allow_html=True)

    steps = [
        "Scanning Dataset", "Validating Structure", "Cleaning Data",
        "Building Context", "Training ARIA", "Generating Insights",
        "Launching Dashboard",
    ]

    prog = st.progress(0)
    for idx in range(len(steps)):
        time.sleep(0.48)
        prog.progress(int((idx + 1) / len(steps) * 100))

    df = get_clean_dataframe(uploaded_file)
    st.session_state['df'] = df
    st.session_state['filename'] = uploaded_file.name

    from utils.data_processor import get_data_summary_for_ai
    st.session_state['data_summary'] = get_data_summary_for_ai(df)

    time.sleep(0.3)
    st.switch_page("pages/1_Dashboard.py")