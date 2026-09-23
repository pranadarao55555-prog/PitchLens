import os
import time
import tempfile

import streamlit as st
from google import genai
from pydantic import BaseModel
if "seek_time" not in st.session_state:
    st.session_state.seek_time = 0
if "pitch_analysis" not in st.session_state:
    st.session_state.pitch_analysis = None

def jump_to_time(clicked_time):
    st.session_state.seek_time = clicked_time


class PitchFeedback(BaseModel):
    time_seconds: int
    issue: str
    correction: str


class VideoAnalysis(BaseModel):
    feedbacks: list[PitchFeedback]


st.set_page_config(page_title="PitchLens: AI Presentation Coach")
st.title("PitchLens: AI Presentation Coach")
st.markdown("""
<style>
/* ================================
   MAIN SPACE BACKGROUND
================================ */
.stApp {
    background: radial-gradient(circle at 50% 50%, #111b4d 0%, #050816 45%, #010208 100%) !important;
    overflow: hidden;
}

/* ================================
   SPACE ANIMATION CONTAINER
================================ */
.space-container {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
}

/* ================================
   STARS
================================ */
.star {
    position: absolute;
    width: 4px;
    height: 4px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 0 8px white, 0 0 18px white;
    animation: twinkle 2s infinite alternate;
}
.star1 { top: 12%; left: 15%; }
.star2 { top: 25%; left: 75%; animation-delay: .5s; }
.star3 { top: 70%; left: 12%; animation-delay: 1s; }
.star4 { top: 18%; left: 48%; animation-delay: 1.5s; }
.star5 { top: 65%; left: 85%; animation-delay: .8s; }
.star6 { top: 40%; left: 32%; animation-delay: 1.2s; }
.star7 { top: 82%; left: 55%; animation-delay: .3s; }
.star8 { top: 10%; left: 88%; animation-delay: 1.7s; }
.star9 { top: 52%; left: 68%; animation-delay: .7s; }
.star10 { top: 88%; left: 22%; animation-delay: 1.4s; }

@keyframes twinkle {
    0% { opacity: .2; transform: scale(.6); box-shadow: 0 0 3px white; }
    100% { opacity: 1; transform: scale(2); box-shadow: 0 0 10px white, 0 0 25px white, 0 0 40px #b9d7ff; }
}

/* ================================
   HUGE SUN
================================ */
.sun {
    position: absolute;
    width: 430px; height: 430px;
    left: -80px; top: 50%;
    transform: translateY(-50%);
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #fffde7 0%, #fff176 12%, #ffd54f 28%, #ff9800 52%, #f4511e 72%, #b71c1c 100%);
    box-shadow: 0 0 30px #ff9800, 0 0 70px #ff9800, 0 0 130px #ff6d00, 0 0 220px rgba(255, 111, 0, .65);
    animation: sunMove 14s ease-in-out infinite alternate;
}
.sun::before {
    content: "";
    position: absolute;
    width: 100%; height: 100%;
    border-radius: 50%;
    background: radial-gradient(circle at 20% 30%, rgba(255,255,255,.5), transparent 8%),
                radial-gradient(circle at 70% 65%, rgba(255,80,0,.5), transparent 12%),
                radial-gradient(circle at 45% 70%, rgba(255,220,50,.5), transparent 10%);
    animation: solarSurface 7s linear infinite;
}
.sun::after {
    content: "";
    position: absolute;
    inset: -45px;
    border-radius: 50%;
    border: 12px solid rgba(255,174,0,.15);
    box-shadow: 0 0 40px rgba(255,140,0,.7), 0 0 90px rgba(255,80,0,.45);
    animation: corona 5s ease-in-out infinite alternate;
}
@keyframes sunMove {
    0% { transform: translateY(-50%) translateX(0) rotate(0deg); }
    100% { transform: translateY(-50%) translateX(130px) rotate(12deg); }
}
@keyframes solarSurface {
    0% { transform: rotate(0deg) scale(1); }
    50% { transform: rotate(180deg) scale(1.04); }
    100% { transform: rotate(360deg) scale(1); }
}
@keyframes corona {
    0% { transform: scale(.96); opacity: .5; }
    100% { transform: scale(1.08); opacity: 1; }
}

/* ================================
   BLUE PLANET
================================ */
.planet {
    position: absolute;
    width: 230px; height: 230px;
    right: -50px; bottom: 30px;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 25%, #d7f9ff 0%, #38bdf8 18%, #2563eb 48%, #172554 78%, #020617 100%);
    box-shadow: inset -35px -35px 55px rgba(0,0,0,.8), 0 0 35px #38bdf8, 0 0 90px rgba(37,99,235,.6);
    animation: planetFloat 18s ease-in-out infinite alternate;
}
@keyframes planetFloat {
    0% { transform: translate(0,0) rotate(0deg); }
    100% { transform: translate(-160px,-100px) rotate(30deg); }
}

/* ================================
   MOVING STARS
================================ */
.shooting-star {
    position: absolute;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 0 10px white, 0 0 25px #8ec5ff;
    animation: shooting 6s linear infinite;
}
.ss1 { left: 25%; bottom: -20px; animation-delay: 1s; }
.ss2 { left: 55%; bottom: -20px; animation-delay: 3s; }
.ss3 { left: 80%; bottom: -20px; animation-delay: 5s; }

@keyframes shooting {
    0% { transform: translateY(0) scale(1); opacity: 0; }
    10% { opacity: 1; }
    70% { transform: translateY(-650px) scale(1); opacity: 1; }
    75% { transform: translateY(-700px) scale(4); opacity: 0; }
    100% { opacity: 0; }
}

/* ================================
   STREAMLIT CONTENT & TEXT
================================ */
.stApp > div { position: relative; z-index: 2; }
h1, h2, h3, p, label {
    color: white !important;
    text-shadow: 0 2px 10px rgba(0,0,0,.9);
}

/* ================================
   FILE UPLOADER & BUTTONS
================================ */
div[data-testid="stFileUploaderDropzone"] {
    background: rgba(5,15,40,.75) !important;
    border: 2px dashed #8b5cf6 !important;
    border-radius: 18px;
    backdrop-filter: blur(15px);
    box-shadow: 0 0 25px rgba(139,92,246,.35);
}
div[data-testid="stFileUploaderDropzone"] *, div[data-testid="stFileUploaderDropzone"] svg {
    color: white !important;
    fill: white !important;
    stroke: white !important;
}
div.stButton > button {
    background: rgba(15,23,42,.85);
    color: white !important;
    border: 1px solid #8b5cf6;
    border-radius: 20px;
    transition: .3s;
}
div.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(139,92,246,.8);
}
div.stAlert {
    border-radius: 15px;
    background-color: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #f8fafc;
}
</style>

<div class="space-container">
    <!-- Twinkling stars -->
    <div class="star star1"></div><div class="star star2"></div>
    <div class="star star3"></div><div class="star star4"></div>
    <div class="star star5"></div><div class="star star6"></div>
    <div class="star star7"></div><div class="star star8"></div>
    <div class="star star9"></div><div class="star star10"></div>
    <!-- HUGE SUN -->
    <div class="sun"></div>
    <!-- BLUE PLANET -->
    <div class="planet"></div>
    <!-- MOVING STARS -->
    <div class="shooting-star ss1"></div>
    <div class="shooting-star ss2"></div>
    <div class="shooting-star ss3"></div>
</div>
""", unsafe_allow_html=True)


uploaded_file = st.file_uploader("Upload your pitch video", type=["mp4"])

if uploaded_file is not None:
    st.video(uploaded_file, start_time=st.session_state.seek_time)

    if st.button("Analyze Pitch"):
        with st.spinner("Analyzing your pitch..."):
            tmp_path = None
            video_file = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                client = genai.Client(api_key="AQ.Ab8RN6JS1yQoWqvNj0R52ptaVnNjvylSnXw8JfBZmJkvBjexuw")

                video_file = client.files.upload(file=tmp_path)

                while video_file.state.name == "PROCESSING":
                    time.sleep(5)
                    video_file = client.files.get(name=video_file.name)

                if video_file.state.name == "FAILED":
                    st.error("Video processing failed. Please try again.")
                else:
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[
                                video_file,
                                "Watch this pitch. Identify 2 or 3 moments where the speaker makes a mistake regarding pacing, filler words, or clarity."
                            ],
                            config={
                                "response_mime_type": "application/json",
                                "response_schema": VideoAnalysis,
                            },
                        )
                        st.session_state['analysis_result'] = response.text
                        st.session_state.pitch_analysis = VideoAnalysis.model_validate_json(response.text)
                        
                    except Exception as e:
                        st.markdown("""
                            <div style="background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); color: white; text-align: center; margin-top: 20px;">
                                <h3 style="margin: 0; color: #fca5a5 !important;">📡 Cosmic Traffic Jam!</h3>
                                <p style="margin: 10px 0 0 0; color: white !important;">The AI servers are handling high traffic right now. Please wait a few seconds and click <b>Analyze Pitch</b> again!</p>
                            </div>
                        """, unsafe_allow_html=True)

            finally:
                if video_file is not None:
                    try:
                        client.files.delete(name=video_file.name)
                    except Exception:
                        pass
                if tmp_path is not None and os.path.exists(tmp_path):
                    os.remove(tmp_path)

if st.session_state.pitch_analysis:
    st.subheader("Feedback")
    for i, feedback in enumerate(st.session_state.pitch_analysis.feedbacks):
        st.button(
            f"⏱️ Jump to {feedback.time_seconds}s",
            key=f"jump_{i}",
            on_click=jump_to_time,
            args=(feedback.time_seconds,)
        )
        st.warning(feedback.issue)
        st.info(feedback.correction)