"""Streamlit Demo Dashboard for Multi-Modal reCAPTCHA Solver (Audio & Visual).

Adheres strictly to DESIGN-SYSTEM.md and ARCHITECTURE.md specifications:
  - Modality colors: Visual (#0D9488 / #06B6D4), Audio (#A855F7 / #EC4899), Router (#10B981)
  - High-contrast, presentation-ready dark theme (#0B0F19 background, #1E293B cards, #F1F5F9 text)
  - Models preloaded ONCE at startup via @st.cache_resource
  - No model logic in UI layer: calls route_and_solve() from solvers.pipeline
  - Graceful input validation handling without stack traces
  - Honest disclosure of limitations and verified benchmarks
  - Visual Architecture Flow Diagram with full color token adherence
"""

import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from solvers.pipeline import route_and_solve, preload_models, SOLVERS
from solvers.base import InvalidInputError


# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS (DESIGN-SYSTEM.md)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="reCAPTCHA-X-LAB — Multi-Modal Solver Demo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Dark Modern Theme Backgrounds */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }

    /* Tabs styling: large, high-contrast, modern */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #111827;
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid #1f2937;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #94a3b8 !important;
        padding: 10px 22px !important;
        border-radius: 8px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    /* Metric & Status Badges */
    .badge-router {
        display: inline-block;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.35));
        color: #10B981;
        border: 1.5px solid #10B981;
        border-radius: 9999px;
        padding: 6px 18px;
        font-size: 1.02rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .badge-visual {
        display: inline-block;
        background: linear-gradient(135deg, rgba(13, 148, 136, 0.2), rgba(6, 182, 212, 0.35));
        color: #2DD4BF;
        border: 1.5px solid #0D9488;
        border-radius: 9999px;
        padding: 6px 18px;
        font-size: 1.02rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .badge-audio {
        display: inline-block;
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(236, 72, 153, 0.35));
        color: #E879F9;
        border: 1.5px solid #A855F7;
        border-radius: 9999px;
        padding: 6px 18px;
        font-size: 1.02rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Result Cards */
    .result-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    .answer-box-visual {
        background: rgba(13, 148, 136, 0.18);
        border: 1.5px solid #0D9488;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        font-size: 1.45rem;
        font-weight: 800;
        color: #2DD4BF;
        margin-bottom: 16px;
    }

    .answer-box-audio {
        background: rgba(168, 85, 247, 0.18);
        border: 1.5px solid #A855F7;
        border-radius: 10px;
        padding: 22px;
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: 0.3em;
        color: #F0ABFC;
        margin-bottom: 16px;
        text-shadow: 0 0 16px rgba(232, 121, 249, 0.4);
    }

    /* Benchmark Metric Card */
    .metric-container {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 22px 18px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    .metric-value {
        font-size: 2.4rem;
        font-weight: 800;
        margin-top: 6px;
    }
    .metric-label {
        font-size: 1.05rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-sub {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Custom Benchmark Table (High Contrast) */
    .benchmark-table {
        width: 100%;
        border-collapse: collapse;
        background: #1e293b;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
        margin-top: 18px;
        margin-bottom: 28px;
    }
    .benchmark-table th {
        background: #0f172a;
        color: #cbd5e1;
        font-size: 1.02rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 16px 20px;
        border-bottom: 2px solid #475569;
        text-align: left;
    }
    .benchmark-table td {
        padding: 16px 20px;
        border-bottom: 1px solid #334155;
        color: #f1f5f9;
        font-size: 1.05rem;
        vertical-align: middle;
    }
    .benchmark-table tr:nth-child(even) {
        background: #243248;
    }
    .benchmark-table tr:hover {
        background: #2e3e57;
    }

    /* Table Metric Badges */
    .pill-green {
        background: rgba(16, 185, 129, 0.22);
        color: #34D399;
        border: 1px solid #10B981;
        border-radius: 6px;
        padding: 4px 12px;
        font-weight: 700;
        font-size: 1.0rem;
        display: inline-block;
    }
    .pill-teal {
        background: rgba(13, 148, 136, 0.22);
        color: #2DD4BF;
        border: 1px solid #0D9488;
        border-radius: 6px;
        padding: 4px 12px;
        font-weight: 700;
        font-size: 1.0rem;
        display: inline-block;
    }
    .pill-purple {
        background: rgba(168, 85, 247, 0.22);
        color: #F0ABFC;
        border: 1px solid #A855F7;
        border-radius: 6px;
        padding: 4px 12px;
        font-weight: 700;
        font-size: 1.0rem;
        display: inline-block;
    }
    .pill-excluded {
        background: rgba(239, 68, 68, 0.2);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.6);
        border-radius: 6px;
        padding: 4px 12px;
        font-weight: 700;
        font-size: 1.0rem;
        display: inline-block;
    }

    /* Known Limitations Box (Dark Theme & High Contrast) */
    .limitations-card {
        background: #1e293b;
        border: 1.5px solid #475569;
        border-radius: 12px;
        padding: 24px;
        margin-top: 14px;
    }
    .limitations-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
        font-size: 1.08rem;
        line-height: 1.75;
        color: #e2e8f0;
    }
    .limitations-item:last-child {
        margin-bottom: 0;
    }
    .limitations-icon {
        min-width: 32px;
        font-size: 1.35rem;
        line-height: 1.4;
    }

    /* Streamlit Expander Dark Overrides */
    div[data-testid="stExpander"] {
        background: #1e293b !important;
        border: 1.5px solid #475569 !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] details {
        background: #1e293b !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] details summary {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        padding: 16px 20px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] details summary:hover {
        background-color: #243248 !important;
    }
    div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] details summary span {
        color: #f8fafc !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stExpander"] details summary svg {
        fill: #f8fafc !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background: #1e293b !important;
        padding: 16px 20px 24px 20px !important;
        border-top: 1px solid #334155 !important;
    }

    /* Graceful Alert styling */
    .validation-alert {
        background: rgba(239, 68, 68, 0.16);
        border: 1.5px solid rgba(239, 68, 68, 0.6);
        border-radius: 10px;
        padding: 20px;
        color: #FEE2E2;
        margin-top: 16px;
        margin-bottom: 16px;
    }

    /* Architecture Visual Diagram Styling */
    .flow-card-router {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(15, 23, 42, 0.95));
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.15);
    }
    .flow-card-audio {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.12), rgba(15, 23, 42, 0.95));
        border: 2px solid #A855F7;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(168, 85, 247, 0.15);
    }
    .flow-card-visual {
        background: linear-gradient(135deg, rgba(13, 148, 136, 0.12), rgba(15, 23, 42, 0.95));
        border: 2px solid #0D9488;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(13, 148, 136, 0.15);
    }
    .flow-arrow-down {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        color: #64748b;
        margin: 6px 0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. One-Time Model Initialization (@st.cache_resource)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="⏳ Initializing specialist deep learning models once at startup...")
def initialize_models():
    """Load model weights for Visual (CLIP) and Audio (Whisper) once and keep cached."""
    statuses = preload_models()
    return statuses

with st.spinner("Preloading deep learning models into memory..."):
    _ = initialize_models()


# -----------------------------------------------------------------------------
# 3. Helper Functions: Image Annotation & Sample Catalog
# -----------------------------------------------------------------------------
def annotate_visual_grid(image_path: str, matched_cells: List[int]) -> Image.Image:
    """Highlight matched 3x3 cells with teal overlay and border markers."""
    base_img = Image.open(image_path).convert("RGBA")
    w, h = base_img.size
    cell_w = w // 3
    cell_h = h // 3

    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Grid divider lines (subtle)
    for r in range(1, 3):
        draw.line([(0, r * cell_h), (w, r * cell_h)], fill=(255, 255, 255, 80), width=2)
    for c in range(1, 3):
        draw.line([(c * cell_w, 0), (c * cell_w, h)], fill=(255, 255, 255, 80), width=2)

    matched_set = set(matched_cells)

    for cell_idx in range(9):
        r = cell_idx // 3
        c = cell_idx % 3
        x0, y0 = c * cell_w, r * cell_h
        x1, y1 = (c + 1) * cell_w, (r + 1) * cell_h

        if cell_idx in matched_set:
            # Highlight with Teal fill & border
            draw.rectangle([x0, y0, x1, y1], fill=(13, 148, 136, 95))
            draw.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=(45, 212, 191, 255), width=5)
            # Badge in upper-left corner of tile
            draw.rectangle([x0 + 6, y0 + 6, x0 + 72, y0 + 30], fill=(13, 148, 136, 240))
            draw.text((x0 + 12, y0 + 10), f"Tile {cell_idx}", fill=(255, 255, 255, 255))
        else:
            # Subtle cell index tag
            draw.rectangle([x0 + 6, y0 + 6, x0 + 60, y0 + 28], fill=(15, 23, 42, 180))
            draw.text((x0 + 10, y0 + 9), f"Tile {cell_idx}", fill=(148, 163, 184, 240))

    combined = Image.alpha_composite(base_img, overlay).convert("RGB")
    return combined


BUNDLED_SAMPLES = {
    # 10 Real reCAPTCHA Visual Grids (10 distinct categories, zero synthetic)
    "Real reCAPTCHA: Chimney (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_chimney.jpg",
        "prompt": "chimney",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Fire Hydrant (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_hydrant.jpg",
        "prompt": "fire hydrant",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Crosswalk (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_crosswalk.jpg",
        "prompt": "crosswalk",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Motorcycle (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_07_motorcycle.jpg",
        "prompt": "motorcycle",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Traffic Light (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_01_traffic_light.jpg",
        "prompt": "traffic light",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Bus (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_02_bus.jpg",
        "prompt": "bus",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Bicycle (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_03_bicycle.jpg",
        "prompt": "bicycle",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Car (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_04_car.jpg",
        "prompt": "car",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Bridge (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_08_bridge.jpg",
        "prompt": "bridge",
        "type": "visual",
        "category": "Visual Challenges"
    },
    "Real reCAPTCHA: Stairs (3x3 Grid)": {
        "path": "data/visual/real_recaptcha_eth_09_stairs.jpg",
        "prompt": "stairs",
        "type": "visual",
        "category": "Visual Challenges"
    },

    # 10 Real SecurImage Audio Challenges (Test split, zero synthetic)
    "Real SecurImage: 71t2 (WAV)": {
        "path": "data/audio/real_audio_017ddc45.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: 1zt5 (WAV)": {
        "path": "data/audio/real_audio_1566a7ac.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: vtu6 (WAV)": {
        "path": "data/audio/real_audio_38a53bb4.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: yx7p (WAV)": {
        "path": "data/audio/real_audio_3df81dfb.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: 13uc (WAV)": {
        "path": "data/audio/real_audio_86a9cf98.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: u38m (WAV)": {
        "path": "data/audio/real_audio_c3587b40.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: twag (WAV)": {
        "path": "data/audio/real_audio_cc818f15.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: 4hh6 (WAV)": {
        "path": "data/audio/real_audio_d76ba939.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: 4s4z (WAV)": {
        "path": "data/audio/real_audio_e35618bb.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
    "Real SecurImage: 5ohb (WAV)": {
        "path": "data/audio/real_audio_eaef535c.wav",
        "prompt": None,
        "type": "audio",
        "category": "Audio Challenges"
    },
}


# -----------------------------------------------------------------------------
# 4. Header & Navigation
# -----------------------------------------------------------------------------
st.title("🛡️ reCAPTCHA-X-LAB — Multi-Modal Solver")
st.markdown(
    "<p style='font-size: 1.15rem; color: #94a3b8; margin-bottom: 24px;'>"
    "Production-grade neural solver pipeline combining an <b>Audio Specialist</b> (Whisper-base + Augmentation), "
    "a <b>Visual Specialist</b> (CLIP Zero-Shot), and a deterministic <b>Binary Router</b>."
    "</p>",
    unsafe_allow_html=True
)

tab_demo, tab_benchmarks, tab_arch = st.tabs([
    "🚀 Interactive Solver Demo",
    "📊 Official Benchmarks & Methodology",
    "🏗️ Pipeline Architecture"
])


# =============================================================================
# TAB 1: INTERACTIVE SOLVER DEMO
# =============================================================================
with tab_demo:
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("1. Select or Upload Challenge")

        input_mode = st.radio(
            "Input Mode:",
            ["📁 Bundled Demo Samples (Curated)", "📤 Upload Custom Challenge File"],
            horizontal=True
        )

        selected_file_path: Optional[str] = None
        target_prompt: str = "traffic light"

        if input_mode == "📁 Bundled Demo Samples (Curated)":
            sample_keys = list(BUNDLED_SAMPLES.keys())
            sample_choice = st.selectbox("Choose a test sample:", sample_keys, index=0)
            meta = BUNDLED_SAMPLES[sample_choice]
            selected_file_path = os.path.join(BASE_DIR, meta["path"])
            
            if meta["prompt"]:
                target_prompt = st.text_input(
                    "Target Object Prompt (for Visual Specialist):",
                    value=meta["prompt"],
                    help="Object category prompt used by CLIP zero-shot cosine clustering."
                )

            # Preview chosen input
            if os.path.exists(selected_file_path):
                if meta["type"] == "visual" or (meta["type"] == "malformed" and selected_file_path.endswith(".png")):
                    st.image(selected_file_path, caption=f"Selected Input: {os.path.basename(selected_file_path)}", width=380)
                elif meta["type"] == "audio":
                    st.audio(selected_file_path)
                elif selected_file_path.endswith(".txt"):
                    st.code(open(selected_file_path).read(), language="text")

        else:
            uploaded_file = st.file_uploader(
                "Drag and drop CAPTCHA challenge file (or test with malformed formats):",
                type=["png", "jpg", "jpeg", "webp", "wav", "mp3", "ogg", "flac", "txt", "pdf", "bin"],
                help="Supports 3x3 image grids and speech audio files. Upload invalid formats to test graceful rejection."
            )
            target_prompt = st.text_input(
                "Target Object Prompt (used if input is an image grid):",
                value="traffic light",
                help="E.g., 'traffic light', 'chimney', 'crosswalk', 'fire hydrant'"
            )

            if uploaded_file is not None:
                # Save temporarily for solver pipeline
                suffix = os.path.splitext(uploaded_file.name)[1]
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tfile.write(uploaded_file.read())
                tfile.close()
                selected_file_path = tfile.name

                ext = suffix.lower()
                if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                    st.image(selected_file_path, caption=f"Uploaded Image: {uploaded_file.name}", width=380)
                elif ext in [".wav", ".mp3", ".ogg", ".flac"]:
                    st.audio(selected_file_path)

        submit_btn = st.button("🚀 Route & Solve Challenge", type="primary", width="stretch")

    # -------------------------------------------------------------------------
    # Execution & Result Presentation
    # -------------------------------------------------------------------------
    with col_result:
        st.subheader("2. Solver Results & Analysis")

        if submit_btn:
            if not selected_file_path or not os.path.exists(selected_file_path):
                st.warning("⚠️ Please select or upload a valid challenge file first.")
            else:
                t0 = time.time()
                try:
                    # UI strictly invokes route_and_solve: NO model logic in UI layer
                    result = route_and_solve(selected_file_path, prompt=target_prompt)
                    duration_sec = time.time() - t0

                    # 1. PREDICTED TYPE (WITH ROUTER CONFIDENCE)
                    pred_type = result["predicted_type"].upper()
                    router_conf = result["router_confidence"]
                    badge_class = "badge-visual" if result["predicted_type"] == "visual" else "badge-audio"

                    st.markdown(
                        f"""
                        <div class="result-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <span class="badge-router">Router: {pred_type}</span>
                                <span style="font-size: 1.15rem; color: #10B981; font-weight: 800;">
                                    Routing Confidence: {router_conf * 100:.1f}%
                                </span>
                            </div>
                            <div style="font-size: 1.05rem; color: #cbd5e1; line-height: 1.6;">
                                <b style="color: #f8fafc;">Routing Method:</b> <code style="font-size: 1.0rem;">{result.get('router_meta', {}).get('method', 'deterministic_classifier')}</code>
                                &nbsp;&nbsp;•&nbsp;&nbsp; <b style="color: #f8fafc;">Latency:</b> <span style="color: #38bdf8; font-weight: 700;">{duration_sec:.2f}s</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # 2. SPECIALIST USED
                    specialist_name = result["specialist_used"].upper()
                    specialist_label = (
                        "Visual Specialist (CLIP Zero-Shot)" if result["specialist_used"] == "visual"
                        else "Audio Specialist (Whisper-base + Gating)"
                    )
                    st.markdown(
                        f"""
                        <div style="margin-bottom: 18px;">
                            <span class="{badge_class}">Specialist Invoked: {specialist_label}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # 3. ANSWER
                    if result["specialist_used"] == "visual":
                        matched_cells = result["answer"]
                        st.markdown(
                            f"""
                            <div class="answer-box-visual">
                                Selected Matching Cells: {matched_cells if matched_cells else 'None Detected'}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Highlighted grid visual
                        annotated_img = annotate_visual_grid(selected_file_path, matched_cells)
                        st.image(
                            annotated_img,
                            caption=f"Challenge Grid with Highlighted Cells for Prompt: '{target_prompt}'",
                            width="stretch"
                        )

                    else:
                        # Audio transcription answer
                        st.markdown(
                            f"""
                            <div class="answer-box-audio">
                                {result['answer']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.audio(selected_file_path)

                        raw_t = result.get("details", {}).get("raw_transcript", "")
                        if raw_t:
                            st.markdown(
                                f"<p style='font-size: 1.05rem; color: #94a3b8;'>Raw ASR Output: "
                                f"<code style='font-size: 1.05rem; color: #f8fafc;'>{raw_t}</code></p>",
                                unsafe_allow_html=True
                            )

                    # 4. CONFIDENCE
                    spec_conf = result["specialist_confidence"]
                    st.markdown(
                        f"<p style='font-size: 1.25rem; font-weight: 700; color: #f8fafc; margin-top: 14px; margin-bottom: 8px;'>"
                        f"Specialist Solution Confidence: <span style='color: #38bdf8;'>{spec_conf * 100:.1f}%</span></p>",
                        unsafe_allow_html=True
                    )
                    st.progress(float(min(max(spec_conf, 0.0), 1.0)))

                    # Format warning check (if output deviated from expected ~4-char format)
                    format_warning = result.get("details", {}).get("format_warning")
                    if format_warning:
                        st.warning(f"⚠️ **Format Advisory:** {format_warning}")

                    # Detailed metadata
                    with st.expander("🔍 Detailed Specialist Diagnostics", expanded=False):
                        st.json(result["details"])

                except InvalidInputError as exc:
                    # Graceful failure handling without stack traces
                    st.markdown(
                        f"""
                        <div class="validation-alert">
                            <h3 style="margin: 0 0 10px 0; color: #F87171; font-size: 1.3rem;">❌ Input Validation Rejected</h3>
                            <p style="margin: 0; font-size: 1.1rem; line-height: 1.6; color: #FEE2E2;">{exc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        "<p style='font-size: 1.05rem; color: #94a3b8; margin-top: 8px;'>"
                        "ℹ️ <b>Graceful Failure Policy:</b> The pipeline validates input formats, grid aspect ratios (~1:1), "
                        "and audio integrity before execution to prevent unhandled runtime exceptions.</p>",
                        unsafe_allow_html=True
                    )

                except Exception as exc:
                    st.error(f"❌ Unexpected Processing Error: {exc}")

        else:
            st.info("👈 Select a challenge from the left panel and click **'Route & Solve Challenge'** to run the live pipeline.")

    # -------------------------------------------------------------------------
    # 5. Known Limitations Expandable Note (High Contrast & Clear Typography)
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("ℹ️ Known Limitations & Honest Methodology Disclosures", expanded=True):
        st.html(
            """
            <div class="limitations-card">
                <div class="limitations-item">
                    <span class="limitations-icon" style="color: #A855F7;">🟣</span>
                    <div>
                        <b style="color: #F8FAFC; font-size: 1.15rem;">Audio Specialist Accuracy Ceiling:</b><br>
                        The audio specialist achieves <b style="color: #E879F9;">80.0% exact match (8/10)</b> 
                        with <b style="color: #E879F9;">5.0% CER</b> on the clean held-out real SecurImage test split. The constrained decoder is 
                        explicitly calibrated for SecurImage's standard <b>~4-character alphanumeric format</b>. Results on 
                        arbitrary unconstrained audio CAPTCHAs (e.g., long variable-length phrases or high-amplitude babble) 
                        may be unreliable and are flagged with lower confidence.
                    </div>
                </div>
                <div class="limitations-item">
                    <span class="limitations-icon" style="color: #0D9488;">🟢</span>
                    <div>
                        <b style="color: #F8FAFC; font-size: 1.15rem;">Visual Specialist Constraints:</b><br>
                        The visual specialist relies on CLIP zero-shot classification 
                        (<b style="color: #2DD4BF;">88.4% mean cell accuracy</b>, <b style="color: #2DD4BF;">66.7% grid exact match</b>). It assumes standard <b>3x3 composite image grids</b> 
                        with approximately 1:1 aspect ratios. Objects spanning multiple tile boundaries or non-square panoramic 
                        crops are rejected at input validation.
                    </div>
                </div>
                <div class="limitations-item">
                    <span class="limitations-icon" style="color: #F59E0B;">🟠</span>
                    <div>
                        <b style="color: #F8FAFC; font-size: 1.15rem;">Strict Leakage Prevention:</b><br>
                        The <code>heldout_split</code> (10 files) was confirmed train-adjacent from earlier 
                        experiments and is <b style="color: #FCA5A5;">strictly excluded</b> from all official generalization reports to preserve rigorous scientific integrity.
                    </div>
                </div>
            </div>
            """
        )


# =============================================================================
# TAB 2: BENCHMARKS & METHODOLOGY (High-Contrast Custom HTML Table)
# =============================================================================
with tab_benchmarks:
    st.subheader("Official Verified Accuracy Benchmarks")
    st.markdown(
        "<p style='font-size: 1.15rem; color: #94a3b8; margin-bottom: 24px;'>"
        "All metrics below are generated directly from the canonical evaluation harness (<code>main.py --test</code>) "
        "on held-out test splits with <b>zero data leakage</b>."
        "</p>",
        unsafe_allow_html=True
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            """
            <div class="metric-container">
                <div class="metric-label" style="color: #10B981;">Binary Router Accuracy</div>
                <div class="metric-value" style="color: #10B981;">100.0%</div>
                <div class="metric-sub">46/46 Tested (36 Real-world)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with m2:
        st.markdown(
            """
            <div class="metric-container">
                <div class="metric-label" style="color: #0D9488;">Visual Specialist (CLIP)</div>
                <div class="metric-value" style="color: #2DD4BF;">88.4%</div>
                <div class="metric-sub">Cell Acc (66.7% Grid Match)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with m3:
        st.markdown(
            """
            <div class="metric-container">
                <div class="metric-label" style="color: #A855F7;">Audio Specialist (Whisper)</div>
                <div class="metric-value" style="color: #E879F9;">80.0%</div>
                <div class="metric-sub">8/10 Real Exact Match (5.0% CER)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<h3 style='margin-top: 36px; margin-bottom: 12px;'>Benchmark Summary Table</h3>", unsafe_allow_html=True)
    
    # Custom HTML Table with High Contrast & Styled Pill Badges
    custom_table_html = """
    <table class="benchmark-table">
        <thead>
            <tr>
                <th style="width: 22%;">Component / Modality</th>
                <th style="width: 24%;">Model Architecture</th>
                <th style="width: 16%;">Test Subset</th>
                <th style="width: 12%;">Samples</th>
                <th style="width: 14%;">Primary Metric</th>
                <th style="width: 12%;">Secondary Metric</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>Binary Router Classifier</b></td>
                <td>Binary Header & Audio Extension Validator</td>
                <td>All Datasets (Audio & Visual)</td>
                <td>46 files (36 real)</td>
                <td><span class="pill-green">100.0% Accuracy</span></td>
                <td>0.0% False Routing Rate</td>
            </tr>
            <tr>
                <td><b>Visual Specialist</b></td>
                <td>CLIP Zero-Shot (clip-vit-base-patch32)</td>
                <td>Composite 3x3 Challenge Grids</td>
                <td>21 grids (16 real)</td>
                <td><span class="pill-teal">88.4% Mean Cell Acc</span></td>
                <td>0.8431 F1 / 66.7% Grid Match</td>
            </tr>
            <tr>
                <td><b>Visual Specialist (Real Subset)</b></td>
                <td>CLIP Zero-Shot (clip-vit-base-patch32)</td>
                <td>Real reCAPTCHA v2 (Google)</td>
                <td>16 real grids</td>
                <td><span class="pill-teal">84.7% Cell Acc</span></td>
                <td>0.7941 F1 Score</td>
            </tr>
            <tr>
                <td><b>Audio Specialist (Canonical Clean)</b></td>
                <td>Fine-Tuned Whisper-base + 5x Aug + Gating</td>
                <td>Official Clean Test Set</td>
                <td>15 files (10 real, 5 synth)</td>
                <td><span class="pill-purple">86.7% Exact Match</span></td>
                <td>3.3% CER / 96.7% Char Acc</td>
            </tr>
            <tr>
                <td><b>Audio Specialist (Real Held-Out)</b></td>
                <td>Fine-Tuned Whisper-base + 5x Aug + Gating</td>
                <td>Real SecurImage test_split</td>
                <td>10 real files</td>
                <td><span class="pill-purple">80.0% Exact Match</span></td>
                <td>5.0% CER / 95.0% Char Acc</td>
            </tr>
            <tr>
                <td><b>Audio Specialist (Train-Adjacent)</b></td>
                <td>Fine-Tuned Whisper-base</td>
                <td>heldout_split (EXCLUDED)</td>
                <td>10 files</td>
                <td><span class="pill-excluded">EXCLUDED</span></td>
                <td>Train-adjacent; omitted for data hygiene</td>
            </tr>
        </tbody>
    </table>
    """
    st.html(custom_table_html)


# =============================================================================
# TAB 3: PIPELINE ARCHITECTURE (Visual Color-Coded Flow Diagram)
# =============================================================================
with tab_arch:
    st.subheader("System Architecture")
    st.markdown(
        "<p style='font-size: 1.15rem; color: #94a3b8; margin-bottom: 24px;'>"
        "Interactive schematic depicting deterministic routing, specialist neural backbones, "
        "and normalized schema aggregation per <code>ARCHITECTURE.md</code>."
        "</p>",
        unsafe_allow_html=True
    )

    # Polished Visual Diagram using Color Tokens from DESIGN-SYSTEM.md
    diagram_html = """
    <div style="background: #111827; border: 1.5px solid #1f2937; border-radius: 16px; padding: 32px; max-width: 1040px; margin: 0 auto;">
        
        <!-- Top: Incoming Challenge -->
        <div style="background: #1e293b; border: 2px solid #475569; border-radius: 12px; padding: 18px; text-align: center; max-width: 480px; margin: 0 auto;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">Input Ingestion</div>
            <div style="font-size: 1.35rem; font-weight: 800; color: #f8fafc; margin-top: 4px;">Incoming Challenge (Image Grid or Audio Stream)</div>
        </div>

        <div class="flow-arrow-down">↓</div>

        <!-- Router Node -->
        <div class="flow-card-router" style="max-width: 580px; margin: 0 auto;">
            <span class="badge-router" style="margin-bottom: 8px;">Deterministic Binary Router</span>
            <div style="font-size: 1.3rem; font-weight: 800; color: #f8fafc; margin-top: 6px;">Modality Classifier (100.0% Accuracy)</div>
            <div style="font-size: 1.02rem; color: #cbd5e1; margin-top: 6px;">
                Inspects binary magic bytes (<code>RIFF/WAVE</code>, <code>ID3</code>, <code>OggS</code>, <code>fLaC</code>) & verifies Pillow headers
            </div>
        </div>

        <!-- Branching Arrows -->
        <div style="display: flex; justify-content: space-around; font-size: 2.2rem; font-weight: 800; color: #64748b; margin: 12px 0;">
            <span style="color: #A855F7; transform: rotate(-30deg);">↙</span>
            <span style="color: #0D9488; transform: rotate(30deg);">↘</span>
        </div>

        <!-- Two Specialist Columns -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 28px;">
            
            <!-- Audio Path (Purple) -->
            <div>
                <div style="text-align: center; margin-bottom: 12px;">
                    <span class="badge-audio">Audio Modality Specialist</span>
                </div>

                <div class="flow-card-audio">
                    <b style="color: #F0ABFC; font-size: 1.15rem;">1. Adaptive Noise Gating</b>
                    <p style="font-size: 0.98rem; color: #cbd5e1; margin: 6px 0 0 0;">
                        Energy-based 20th-percentile spectral thresholding eliminates SecurImage background chatter & buzzers.
                    </p>
                </div>

                <div class="flow-arrow-down" style="color: #A855F7;">↓</div>

                <div class="flow-card-audio">
                    <b style="color: #F0ABFC; font-size: 1.15rem;">2. Fine-Tuned Whisper ASR</b>
                    <p style="font-size: 0.98rem; color: #cbd5e1; margin: 6px 0 0 0;">
                        5x Data Augmentation (pitch-shift, noise injection, time-stretch) trained on 40 pairs; avoids CTC collapse.
                    </p>
                </div>

                <div class="flow-arrow-down" style="color: #A855F7;">↓</div>

                <div class="flow-card-audio">
                    <b style="color: #F0ABFC; font-size: 1.15rem;">3. Constrained Decoder</b>
                    <p style="font-size: 0.98rem; color: #cbd5e1; margin: 6px 0 0 0;">
                        Enforces ~4-char alphanumeric pattern, phonetic digit mapping & acoustic repetition deduplication.
                    </p>
                    <div style="margin-top: 10px;"><span class="pill-purple">80.0% Exact Match (5.0% CER)</span></div>
                </div>
            </div>

            <!-- Visual Path (Teal) -->
            <div>
                <div style="text-align: center; margin-bottom: 12px;">
                    <span class="badge-visual">Visual Modality Specialist</span>
                </div>

                <div class="flow-card-visual">
                    <b style="color: #2DD4BF; font-size: 1.15rem;">1. 3x3 Tile Slicing</b>
                    <p style="font-size: 0.98rem; color: #cbd5e1; margin: 6px 0 0 0;">
                        Validates 1:1 aspect ratio (0.75 &le; AR &le; 1.33) & crops composite challenge into 9 individual tiles.
                    </p>
                </div>

                <div class="flow-arrow-down" style="color: #0D9488;">↓</div>

                <div class="flow-card-visual">
                    <b style="color: #2DD4BF; font-size: 1.15rem;">2. CLIP Vision-Language Model</b>
                    <p style="font-size: 0.98rem; color: #cbd5e1; margin: 6px 0 0 0;">
                        <code>openai/clip-vit-base-patch32</code> computes zero-shot cosine similarity between tiles and target text prompt.
                    </p>
                </div>

                <div class="flow-arrow-down" style="color: #0D9488;">↓</div>

                <div class="flow-card-visual">
                    <b style="color: #2DD4BF; font-size: 1.15rem;">3. Adaptive Score Clustering</b>
                    <p style="font-size: 0.98rem; color: #cbd5e1; margin: 6px 0 0 0;">
                        Separates matching cells from background based on maximum score gaps or mean thresholding.
                    </p>
                    <div style="margin-top: 10px;"><span class="pill-teal">88.4% Cell Acc (66.7% Grid Match)</span></div>
                </div>
            </div>

        </div>

        <!-- Convergence Arrows -->
        <div style="display: flex; justify-content: space-around; font-size: 2.2rem; font-weight: 800; color: #64748b; margin: 12px 0;">
            <span style="color: #A855F7; transform: rotate(30deg);">↘</span>
            <span style="color: #0D9488; transform: rotate(-30deg);">↙</span>
        </div>

        <!-- Bottom: Unified Output Schema -->
        <div style="background: #1e293b; border: 2px solid #475569; border-radius: 12px; padding: 22px; text-align: center; max-width: 680px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);">
            <div style="font-size: 0.95rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em;">Result Aggregation</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #f8fafc; margin-top: 4px;">Standardized Unified Result Schema</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: #cbd5e1; margin-top: 10px; background: #0f172a; padding: 12px; border-radius: 8px; text-align: left;">
                { <span style="color: #38bdf8;">"predicted_type"</span>, <span style="color: #34d399;">"router_confidence"</span>, <span style="color: #c084fc;">"specialist_used"</span>, <span style="color: #f472b6;">"answer"</span>, <span style="color: #fbbf24;">"specialist_confidence"</span>, <span style="color: #94a3b8;">"details"</span> }
            </div>
        </div>

    </div>
    """
    st.html(diagram_html)
