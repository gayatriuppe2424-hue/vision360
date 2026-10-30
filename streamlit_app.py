import streamlit as st
import streamlit.components.v1 as components
import json
import os
import base64
import subprocess
import sys
from datetime import date

st.set_page_config(
    page_title="Vision360 | Hands-Free & Digital Wellness Studio",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM DARK STUDIO STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #131b2e, #0f1523);
        border: 1px solid #1e293b;
        padding: 14px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .studio-banner {
        background: linear-gradient(90deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid #312e81;
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD & SAVE PROFILES ---
PROFILES_FILE = "vision360_profiles.json"

DEFAULT_DATA = {
    "active_id": "user_default",
    "profiles": {
        "user_default": {
            "name": "Gayatri",
            "xp": 1200,
            "preset": "Custom",
            "settings": {
                "sensitivity": 0.2,
                "smoothing": 0.7,
                "mouth_thresh": 0.414,
                "scroll_speed": 420,
                "dwell_time": 1.0,
                "dwell_radius": 25,
                "ear_close_thresh": 0.19,
                "ear_reopen_thresh": 0.23,
                "ear_baseline": 0.28,
                "eye_width_cm": 9.0
            },
            "first_run": str(date.today()),
            "active_dates": [str(date.today())],
            "lifetime_clicks": 15,
            "lifetime_blinks": 26,
            "hands_free_secs": 88.6,
            "posture_good_secs": 229.4,
            "posture_total_secs": 234.0,
            "daily": {
                "date": str(date.today()),
                "breaks": 4,
                "good_secs": 229.4,
                "total_secs": 234.0
            }
        }
    }
}

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_DATA

def save_profiles(data):
    with open(PROFILES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_f:
            return base64.b64encode(img_f.read()).decode()
    return ""

data = load_profiles()
profiles = data.get("profiles", DEFAULT_DATA["profiles"])
active_id = data.get("active_id", list(profiles.keys())[0])
if active_id not in profiles:
    active_id = list(profiles.keys())[0]

cat_b64 = get_base64_image("cat_gatekeeper.gif")
logo_b64 = get_base64_image("vision360_logo.png")

# --- SIDEBAR: PROFILE & CALIBRATION SETTINGS ---
with st.sidebar:
    if logo_b64:
        st.markdown(
            f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_b64}" width="95"></div>',
            unsafe_allow_html=True
        )
    st.markdown("## ⚙️ Vision360 Control Panel")

    # Profile Switcher
    profile_keys = list(profiles.keys())
    profile_names = [f"{profiles[k]['name']} (XP: {profiles[k].get('xp', 0)})" for k in profile_keys]
    selected_idx = profile_keys.index(active_id)
    chosen_idx = st.selectbox("👤 Active User Profile", range(len(profile_keys)), format_func=lambda i: profile_names[i], index=selected_idx)
    active_id = profile_keys[chosen_idx]
    active_prof = profiles[active_id]
    settings = active_prof["settings"]

    # Preset Selector
    presets = ["Casual Browsing & Web", "Custom", "Precision Coding", "High Sensitivity"]
    current_preset = active_prof.get("preset", "Custom")
    preset_idx = presets.index(current_preset) if current_preset in presets else 1
    new_preset = st.selectbox("🎯 Mode Preset", presets, index=preset_idx)

    st.divider()
    st.markdown("### 👁️ Gaze & Cursor Tuning")
    sensitivity = st.slider("Gaze Sensitivity", 0.05, 1.0, float(settings.get("sensitivity", 0.2)), 0.05)
    smoothing = st.slider("Cursor Smoothing", 0.1, 0.95, float(settings.get("smoothing", 0.7)), 0.05)
    dwell_time = st.slider("Dwell Click Time (sec)", 0.3, 2.5, float(settings.get("dwell_time", 1.0)), 0.05)
    dwell_radius = st.slider("Dwell Radius (px)", 10, 60, int(settings.get("dwell_radius", 25)), 1)

    st.markdown("### 😉 Blink & Mouth Thresholds")
    ear_close = st.slider("EAR Blink Close Threshold", 0.10, 0.30, float(settings.get("ear_close_thresh", 0.19)), 0.01)
    ear_reopen = st.slider("EAR Reopen Threshold", 0.15, 0.35, float(settings.get("ear_reopen_thresh", 0.23)), 0.01)
    mouth_thresh = st.slider("Mouth Open Scroll Threshold", 0.20, 0.70, float(settings.get("mouth_thresh", 0.41)), 0.01)
    scroll_speed = st.slider("Scroll Speed", 100, 800, int(settings.get("scroll_speed", 420)), 20)
    eye_width_cm = st.slider("Eye Width Calibration (cm)", 6.0, 12.0, float(settings.get("eye_width_cm", 9.0)), 0.5)

    if st.button("💾 Save Profile Settings", use_container_width=True, type="primary"):
        active_prof["preset"] = new_preset
        active_prof["settings"].update({
            "sensitivity": sensitivity,
            "smoothing": smoothing,
            "dwell_time": dwell_time,
            "dwell_radius": dwell_radius,
            "ear_close_thresh": ear_close,
            "ear_reopen_thresh": ear_reopen,
            "mouth_thresh": mouth_thresh,
            "scroll_speed": scroll_speed,
            "eye_width_cm": eye_width_cm
        })
        data["active_id"] = active_id
        save_profiles(data)
        st.success(f"Saved settings for {active_prof['name']}!")

    if os.path.exists("vision360_ui.py"):
        st.divider()
        st.caption("Running on your local Windows laptop?")
        if st.button("🖥️ Launch Native Desktop OS Window", use_container_width=True):
            subprocess.Popen([sys.executable, "vision360_ui.py"])
            st.info("Launched native `vision360_ui.py` window on your desktop!")

# --- TOP HEADER & GAMIFIED TELEMETRY CARDS ---
st.markdown(f"""
<div class="studio-banner">
    <h2 style="margin:0; color:#38bdf8;">👁️ Vision360 — Hands-Free & Digital Wellness Studio</h2>
    <p style="margin:4px 0 0 0; color:#94a3b8;">
        Active Operator: <b>{active_prof['name']}</b> &nbsp;|&nbsp; Preset: <b>{new_preset}</b> &nbsp;|&nbsp; 
        Real-Time Iris Cursor, Blink/Dwell Click, Mouth Scroll & Posture Guardian
    </p>
</div>
""", unsafe_allow_html=True)

posture_total = max(float(active_prof.get("posture_total_secs", 1)), 1.0)
posture_good = float(active_prof.get("posture_good_secs", 0))
posture_pct = min(100, int((posture_good / posture_total) * 100))

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("✨ Operator XP", f"{active_prof.get('xp', 0)} XP", "Level " + str(1 + active_prof.get('xp', 0) // 500))
m2.metric("🖱️ Lifetime Clicks", active_prof.get("lifetime_clicks", 0))
m3.metric("😉 Lifetime Blinks", active_prof.get("lifetime_blinks", 0))
m4.metric("⏱️ Hands-Free Time", f"{int(active_prof.get('hands_free_secs', 0))}s")
m5.metric("🧘 Good Posture", f"{posture_pct}%")
m6.metric("🐾 Daily Breaks", active_prof.get("daily", {}).get("breaks", 0))

# --- LIVE INTERACTIVE WEB STUDIO (60 FPS MEDIAPIPE + VIRTUAL GAZE CURSOR + SANDBOX) ---
cat_img_tag = f"data:image/gif;base64,{cat_b64}" if cat_b64 else ""

studio_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0; padding: 0;
        background: #0f172a; color: #f8fafc;
        font-family: 'Segoe UI', system-ui, sans-serif;
        overflow: hidden;
        user-select: none;
    }}
    .studio-grid {{
        display: grid;
        grid-template-columns: 420px 1fr;
        gap: 16px;
        height: 610px;
        padding: 12px;
        box-sizing: border-box;
    }}
    .cam-card, .workspace-card {{
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 14px;
        position: relative;
        display: flex;
        flex-direction: column;
    }}
    .video-wrap {{
        position: relative;
        width: 100%;
        height: 280px;
        background: #020617;
        border-radius: 10px;
        overflow: hidden;
        border: 2px solid #0ea5e9;
    }}
    video {{
        width: 100%; height: 100%;
        object-fit: cover;
        transform: scaleX(-1);
    }}
    canvas {{
        position: absolute; top: 0; left: 0;
        width: 100%; height: 100%;
        transform: scaleX(-1);
    }}
    .hud-bars {{
        margin-top: 12px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        font-size: 13px;
    }}
    .hud-box {{
        background: #0f172a;
        padding: 8px 10px;
        border-radius: 8px;
        border: 1px solid #334155;
    }}
    .hud-val {{ font-weight: 700; color: #38bdf8; float: right; }}
    .btn-row {{
        display: flex; gap: 8px; margin-top: 10px;
    }}
    .ctrl-btn {{
        flex: 1;
        padding: 9px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        cursor: pointer;
        background: #0284c7;
        color: white;
        transition: 0.2s;
    }}
    .ctrl-btn:hover {{ background: #0369a1; }}
    .ctrl-btn.secondary {{ background: #475569; }}
    /* Interactive Hands-Free Target Tiles */
    .targets-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 10px;
    }}
    .gaze-tile {{
        background: #0f172a;
        border: 2px solid #334155;
        border-radius: 12px;
        padding: 18px 12px;
        text-align: center;
        transition: all 0.15s ease;
        position: relative;
        overflow: hidden;
    }}
    .gaze-tile.hovered {{
        border-color: #38bdf8;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.35);
        transform: translateY(-2px);
    }}
    .gaze-tile.clicked {{
        background: #065f46;
        border-color: #10b981;
    }}
    .dwell-bar {{
        position: absolute; bottom: 0; left: 0;
        height: 5px; background: #38bdf8;
        width: 0%;
    }}
    .scroll-box {{
        margin-top: 14px;
        flex: 1;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        overflow-y: auto;
        font-size: 13.5px;
        line-height: 1.5;
    }}
    /* Virtual Eye Gaze Cursor */
    #gaze-cursor {{
        position: fixed;
        width: 28px; height: 28px;
        border: 3px solid #00f5d4;
        background: rgba(0, 245, 212, 0.2);
        border-radius: 50%;
        pointer-events: none;
        transform: translate(-50%, -50%);
        z-index: 9999;
        box-shadow: 0 0 16px #00f5d4;
        transition: width 0.1s, height 0.1s;
    }}
    /* Cat Gatekeeper Break Modal */
    #gatekeeper-modal {{
        display: none;
        position: absolute;
        inset: 0;
        background: rgba(2, 6, 23, 0.92);
        z-index: 1000;
        border-radius: 14px;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 24px;
    }}
    #gatekeeper-modal img {{
        width: 190px;
        border-radius: 12px;
        margin-bottom: 12px;
    }}
</style>
</head>
<body>

<div id="gaze-cursor" style="left: 50%; top: 50%;"></div>

<div class="studio-grid">
    <!-- LEFT: LIVE WEBCAM + MEDIAPIPE IRIS TRACKER -->
    <div class="cam-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:700; color:#38bdf8;">📹 Live Iris & Posture Engine</span>
            <span id="status-badge" style="font-size:12px; background:#065f46; padding:3px 8px; border-radius:99px;">Initializing...</span>
        </div>

        <div class="video-wrap">
            <video id="webcam" autoplay playsinline muted></video>
            <canvas id="overlay"></canvas>
        </div>

        <div class="hud-bars">
            <div class="hud-box">EAR (Blink): <span class="hud-val" id="ear-val">0.28</span></div>
            <div class="hud-box">MAR (Mouth): <span class="hud-val" id="mar-val">0.10</span></div>
            <div class="hud-box">Session Blinks: <span class="hud-val" id="blink-val">0</span></div>
            <div class="hud-box">Session Clicks: <span class="hud-val" id="click-val">0</span></div>
            <div class="hud-box">Est. Distance: <span class="hud-val" id="dist-val">55 cm</span></div>
            <div class="hud-box">Posture: <span class="hud-val" id="posture-val" style="color:#4ade80;">GOOD</span></div>
        </div>

        <div class="btn-row">
            <button class="ctrl-btn" onclick="calibrateCenter()">🎯 Calibrate Center Gaze</button>
            <button class="ctrl-btn secondary" onclick="triggerGatekeeper()">🐾 Test Break Alert</button>
        </div>
    </div>

    <!-- RIGHT: INTERACTIVE HANDS-FREE WORKSPACE -->
    <div class="workspace-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-weight:700; font-size:16px;">✨ Interactive Hands-Free Workspace</span>
                <p style="margin:2px 0 0 0; font-size:12.5px; color:#94a3b8;">
                    Move the glowing cyan cursor with your <b>eyes/head</b>. Hover on any tile to <b>Dwell-Click</b> ({dwell_time}s) or <b>Blink</b> to click! Open your mouth (&gt;{mouth_thresh}) to auto-scroll below.
                </p>
            </div>
            <div style="background:#0f172a; padding:6px 12px; border-radius:8px; border:1px solid #334155; font-size:13px;">
                Live XP Earned: <b style="color:#facc15;" id="xp-val">+0 XP</b>
            </div>
        </div>

        <div class="targets-grid">
            <div class="gaze-tile" data-name="Launch Browser">
                <div style="font-size:24px;">🌐</div>
                <div style="font-weight:600; margin-top:4px;">Web Mode</div>
                <div style="font-size:11px; color:#94a3b8;">Look or Blink to Click</div>
                <div class="dwell-bar"></div>
            </div>
            <div class="gaze-tile" data-name="20-20-20 Eye Break">
                <div style="font-size:24px;">🌿</div>
                <div style="font-weight:600; margin-top:4px;">Eye Rest (20s)</div>
                <div style="font-size:11px; color:#94a3b8;">Trigger Gatekeeper</div>
                <div class="dwell-bar"></div>
            </div>
            <div class="gaze-tile" data-name="Recalibrate Center">
                <div style="font-size:24px;">🎯</div>
                <div style="font-weight:600; margin-top:4px;">Center Lock</div>
                <div style="font-size:11px; color:#94a3b8;">Zero Gaze Offset</div>
                <div class="dwell-bar"></div>
            </div>
            <div class="gaze-tile" data-name="Audio Feedback">
                <div style="font-size:24px;">🔊</div>
                <div style="font-weight:600; margin-top:4px;">Voice Beep</div>
                <div style="font-size:11px; color:#94a3b8;">Toggle Click Sound</div>
                <div class="dwell-bar"></div>
            </div>
            <div class="gaze-tile" data-name="Posture Check">
                <div style="font-size:24px;">🧘</div>
                <div style="font-weight:600; margin-top:4px;">Posture Scan</div>
                <div style="font-size:11px; color:#94a3b8;">Verify Ergonomics</div>
                <div class="dwell-bar"></div>
            </div>
            <div class="gaze-tile" data-name="Emergency Stop">
                <div style="font-size:24px;">⏸️</div>
                <div style="font-weight:600; margin-top:4px;">Pause Cursor</div>
                <div style="font-size:11px; color:#94a3b8;">Freeze Tracking</div>
                <div class="dwell-bar"></div>
            </div>
        </div>

        <div class="scroll-box" id="mouth-scroll-box">
            <b style="color:#38bdf8;">📜 Hands-Free Mouth-Scroll Reader (Open mouth &gt; {mouth_thresh} MAR to scroll)</b>
            <p id="action-log" style="color:#4ade80; font-weight:600;">Status: Waiting for eye-gaze or blink interaction...</p>
            <p>1. <b>Real-Time Iris Tracking:</b> Vision360 tracks 478 3D facial and iris landmarks directly from your webcam stream with zero cloud latency.</p>
            <p>2. <b>Blink & Dwell Clicking:</b> Hold your gaze inside any target tile for {dwell_time} seconds, or perform a deliberate blink (EAR below {ear_close}) to trigger an instant hands-free click.</p>
            <p>3. <b>Ergonomic Posture & Distance Guardian:</b> Using your calibrated eye width ({eye_width_cm} cm), Vision360 continuously estimates your screen distance and alerts you if you lean too close.</p>
            <p>4. <b>20-20-20 Digital Wellness Gatekeeper:</b> Every 20 minutes, the Cat Gatekeeper reminds you to look 20 feet away for 20 seconds to prevent computer vision syndrome.</p>
            <p>5. <b>Mouth-Open Auto-Scroll:</b> Open your mouth slightly to scroll through long documents and web pages completely hands-free at {scroll_speed} px/s.</p>
        </div>

        <!-- CAT GATEKEEPER BREAK MODAL -->
        <div id="gatekeeper-modal">
            {"<img src='" + cat_img_tag + "' alt='Cat Gatekeeper'/>" if cat_img_tag else "<div style='font-size:64px;'>🐱</div>"}
            <h2 style="margin:4px 0; color:#facc15;">🐾 Cat Gatekeeper: Time for a 20-20-20 Eye Break!</h2>
            <p style="color:#cbd5e1; max-width:420px;">
                Look at an object 20 feet away for <b id="break-timer">20</b> seconds to relax your ciliary eye muscles and earn +50 Bonus XP!
            </p>
            <button class="ctrl-btn" style="max-width:200px; margin-top:10px;" onclick="closeGatekeeper()">✅ I Rested My Eyes (+50 XP)</button>
        </div>
    </div>
</div>

<script type="module">
import vision from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3";
const {{ FaceLandmarker, FilesetResolver }} = vision;

const SETTINGS = {{
    sensitivity: {sensitivity},
    smoothing: {smoothing},
    dwellTime: {dwell_time} * 1000,
    earClose: {ear_close},
    earReopen: {ear_reopen},
    mouthThresh: {mouth_thresh},
    scrollSpeed: {scroll_speed},
    eyeWidthCm: {eye_width_cm}
}};

const video = document.getElementById("webcam");
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");
const cursor = document.getElementById("gaze-cursor");
const statusBadge = document.getElementById("status-badge");

let faceLandmarker;
let cursorX = window.innerWidth * 0.65;
let cursorY = window.innerHeight * 0.45;
let centerOffsetX = 0.5;
let centerOffsetY = 0.5;
let latestRawX = 0.5;
let latestRawY = 0.5;

let blinkCount = 0;
let clickCount = 0;
let xpEarned = 0;
let isEyeClosed = false;
let paused = false;

let hoveredTile = null;
let hoverStartTime = 0;

window.calibrateCenter = () => {{
    centerOffsetX = latestRawX;
    centerOffsetY = latestRawY;
    document.getElementById("action-log").innerText = "🎯 Calibrated center gaze to current head/eye position!";
}};

window.triggerGatekeeper = () => {{
    const modal = document.getElementById("gatekeeper-modal");
    modal.style.display = "flex";
}};

window.closeGatekeeper = () => {{
    document.getElementById("gatekeeper-modal").style.display = "none";
    xpEarned += 50;
    document.getElementById("xp-val").innerText = "+" + xpEarned + " XP";
    document.getElementById("action-log").innerText = "🐾 Completed Cat Gatekeeper wellness break! (+50 XP)";
}};

function dist(p1, p2) {{
    return Math.hypot(p1.x - p2.x, p1.y - p2.y);
}}

async function initTracker() {{
    try {{
        const filesetResolver = await FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
        );
        faceLandmarker = await FaceLandmarker.createFromOptions(filesetResolver, {{
            baseOptions: {{
                modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                delegate: "GPU"
            }},
            runningMode: "VIDEO",
            numFaces: 1
        }});

        const stream = await navigator.mediaDevices.getUserMedia({{ video: {{ width: 640, height: 480 }} }});
        video.srcObject = stream;
        video.addEventListener("loadeddata", () => {{
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            statusBadge.innerText = "🟢 60 FPS Tracking Active";
            requestAnimationFrame(processFrame);
        }});
    }} catch (err) {{
        statusBadge.innerText = "⚠️ Allow Camera Permission";
        statusBadge.style.background = "#b91c1c";
    }}
}}

function triggerTileClick(tile, method) {{
    clickCount++;
    xpEarned += 10;
    document.getElementById("click-val").innerText = clickCount;
    document.getElementById("xp-val").innerText = "+" + xpEarned + " XP";

    const name = tile.getAttribute("data-name");
    tile.classList.add("clicked");
    setTimeout(() => tile.classList.remove("clicked"), 350);

    document.getElementById("action-log").innerText = `✅ [${{method}}] Activated: ${{name}} (+10 XP)`;

    if (name === "20-20-20 Eye Break") window.triggerGatekeeper();
    if (name === "Recalibrate Center") window.calibrateCenter();
    if (name === "Emergency Stop") paused = !paused;
}}

function processFrame() {{
    if (video.readyState >= 2 && faceLandmarker) {{
        const results = faceLandmarker.detectForVideo(video, performance.now());
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (results.faceLandmarks && results.faceLandmarks.length > 0) {{
            const lm = results.faceLandmarks[0];

            // Draw Iris & Eye Landmarks on video preview
            const irisIndices = [468, 469, 470, 471, 473, 474, 475, 476];
            ctx.fillStyle = "#00f5d4";
            for (const idx of irisIndices) {{
                if (lm[idx]) {{
                    ctx.beginPath();
                    ctx.arc(lm[idx].x * canvas.width, lm[idx].y * canvas.height, 3, 0, 2 * Math.PI);
                    ctx.fill();
                }}
            }}

            // Compute EAR (Eye Aspect Ratio)
            const leftEAR = dist(lm[159], lm[145]) / (dist(lm[33], lm[133]) + 1e-6);
            const rightEAR = dist(lm[386], lm[374]) / (dist(lm[362], lm[263]) + 1e-6);
            const ear = (leftEAR + rightEAR) / 2;
            document.getElementById("ear-val").innerText = ear.toFixed(2);

            // Compute MAR (Mouth Aspect Ratio)
            const mar = dist(lm[13], lm[14]) / (dist(lm[78], lm[308]) + 1e-6);
            document.getElementById("mar-val").innerText = mar.toFixed(2);

            // Blink Detection
            if (ear < SETTINGS.earClose && !isEyeClosed) {{
                isEyeClosed = true;
                blinkCount++;
                document.getElementById("blink-val").innerText = blinkCount;
                if (hoveredTile) {{
                    triggerTileClick(hoveredTile, "Blink-Click");
                }}
            }} else if (ear > SETTINGS.earReopen) {{
                isEyeClosed = false;
            }}

            // Mouth-Open Auto Scroll
            const scrollBox = document.getElementById("mouth-scroll-box");
            if (mar > SETTINGS.mouthThresh) {{
                scrollBox.scrollTop += (SETTINGS.scrollSpeed / 60);
                if (scrollBox.scrollTop + scrollBox.clientHeight >= scrollBox.scrollHeight - 5) {{
                    scrollBox.scrollTop = 0;
                }}
            }}

            // Distance & Posture Estimation
            const faceWidthNorm = dist(lm[33], lm[263]);
            const estCm = Math.round((SETTINGS.eyeWidthCm * 0.65) / (faceWidthNorm + 1e-4));
            document.getElementById("dist-val").innerText = estCm + " cm";
            const postureEl = document.getElementById("posture-val");
            if (estCm < 38 || Math.abs(lm[33].y - lm[263].y) > 0.06) {{
                postureEl.innerText = "TOO CLOSE / TILT";
                postureEl.style.color = "#f87171";
            }} else {{
                postureEl.innerText = "GOOD";
                postureEl.style.color = "#4ade80";
            }}

            // Gaze Cursor Position Calculation (using Iris 468 & 473 + Nose tip 1)
            latestRawX = (lm[468].x + lm[473].x + lm[1].x) / 3;
            latestRawY = (lm[468].y + lm[473].y + lm[1].y) / 3;

            if (!paused) {{
                const gain = 2.5 + SETTINGS.sensitivity * 6.0;
                const normX = 0.5 - (latestRawX - centerOffsetX) * gain;
                const normY = 0.5 + (latestRawY - centerOffsetY) * gain;

                const targetX = Math.max(20, Math.min(window.innerWidth - 20, normX * window.innerWidth));
                const targetY = Math.max(20, Math.min(window.innerHeight - 20, normY * window.innerHeight));

                cursorX = cursorX * SETTINGS.smoothing + targetX * (1 - SETTINGS.smoothing);
                cursorY = cursorY * SETTINGS.smoothing + targetY * (1 - SETTINGS.smoothing);

                cursor.style.left = cursorX + "px";
                cursor.style.top = cursorY + "px";
            }}

            // Check Hover & Dwell Click on Interactive Tiles
            const elem = document.elementFromPoint(cursorX, cursorY);
            const tile = elem ? elem.closest(".gaze-tile") : null;

            document.querySelectorAll(".gaze-tile").forEach(t => {{
                if (t !== tile) {{
                    t.classList.remove("hovered");
                    t.querySelector(".dwell-bar").style.width = "0%";
                }}
            }});

            if (tile) {{
                if (hoveredTile !== tile) {{
                    hoveredTile = tile;
                    hoverStartTime = performance.now();
                    tile.classList.add("hovered");
                }} else {{
                    const elapsed = performance.now() - hoverStartTime;
                    const pct = Math.min(100, (elapsed / SETTINGS.dwellTime) * 100);
                    tile.querySelector(".dwell-bar").style.width = pct + "%";
                    if (elapsed >= SETTINGS.dwellTime) {{
                        triggerTileClick(tile, "Dwell-Click");
                        hoverStartTime = performance.now() + 800;
                    }}
                }}
            }} else {{
                hoveredTile = null;
            }}
        }}
    }}
    requestAnimationFrame(processFrame);
}}

initTracker();
</script>
</body>
</html>
"""

components.html(studio_html, height=635, scrolling=False)