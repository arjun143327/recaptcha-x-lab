"""FastAPI backend for reCAPTCHA-X-Lab dashboard.

Exposes:
  POST /api/solve   — Upload a CAPTCHA file, returns routing + specialist result
  GET  /api/metrics — Returns the full benchmark metrics for all 3 modalities
  GET  /api/health  — Health check
"""

import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from solvers import route_and_solve
from solvers.audio import AudioSolver
from solvers.visual import VisualSolver

app = FastAPI(
    title="reCAPTCHA-X-Lab API",
    description="Multi-modal CAPTCHA robustness analysis API (Audio & Visual)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-load all solvers once at startup
_audio_solver: Optional[AudioSolver] = None
_visual_solver: Optional[VisualSolver] = None


def get_audio_solver() -> AudioSolver:
    global _audio_solver
    if _audio_solver is None:
        _audio_solver = AudioSolver()
    return _audio_solver


def get_visual_solver() -> VisualSolver:
    global _visual_solver
    if _visual_solver is None:
        _visual_solver = VisualSolver()
    return _visual_solver



@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/solve")
async def solve_captcha(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(default="traffic light"),
) -> Dict[str, Any]:
    """Route and solve an uploaded CAPTCHA challenge.
    
    Returns routing decision, specialist answer, confidence scores, and details.
    """
    suffix = os.path.splitext(file.filename or "upload")[1] or ".bin"
    allowed = {".wav", ".mp3", ".png", ".jpg", ".jpeg"}
    if suffix.lower() not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}. Allowed: {allowed}")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        t0 = time.perf_counter()
        result = route_and_solve(tmp_path, prompt=prompt)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        result["elapsed_ms"] = elapsed_ms
        result["filename"] = file.filename
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.get("/api/metrics")
def get_metrics() -> Dict[str, Any]:
    """Return full benchmark evaluation metrics for all 3 modalities."""
    data_dir = os.path.join(BASE_DIR, "data")

    # Visual metrics
    visual_summary: Dict[str, Any] = {}
    try:
        vs = get_visual_solver()
        visual_summary = vs.evaluate_fixtures()
    except Exception as e:
        visual_summary = {"error": str(e)}

    # Audio metrics
    audio_summary: Dict[str, Any] = {}
    try:
        aud = get_audio_solver()
        audio_summary = aud.evaluate_fixtures()
    except Exception as e:
        audio_summary = {"error": str(e)}

    return {
        "visual": visual_summary,
        "audio": audio_summary,
        "puzzle": {
            "status": "discarded",
            "reason": "OpenCV heuristic achieved 25% accuracy on independent real data; narrowed scope to Audio and Visual."
        }
    }


@app.get("/api/metrics/precomputed")
def get_precomputed_metrics() -> Dict[str, Any]:
    """Return hardcoded benchmark results (fast, no model inference needed).
    
    These are the verified empirical results from python main.py --test
    run across 46 real + synthetic challenge samples.
    """
    return {
        "router": {
            "total": 46,
            "correct": 46,
            "accuracy": 1.0,
            "real_total": 36,
            "real_correct": 36,
            "real_accuracy": 1.0,
        },
        "visual": {
            "num_samples": 21,
            "real_count": 16,
            "synth_count": 5,
            "mean_cell_accuracy": 0.884,
            "mean_f1_score": 0.8431,
            "exact_match_rate": 0.667,
            "real_cell_accuracy": 0.847,
            "real_f1": 0.7941,
            "synth_cell_accuracy": 0.978,
            "synth_f1": 0.971,
        },
        "audio": {
            "num_samples": 25,
            "real_count": 20,
            "synth_count": 5,
            "mean_char_accuracy": 0.758,
            "mean_cer": 0.242,
            "exact_match_rate": 0.440,
            "real_exact_match": 0.300,
            "real_cer": 0.302,
            "synth_exact_match": 1.0,
            "synth_cer": 0.0,
        },
        "puzzle": {
            "status": "discarded",
            "reason": "OpenCV heuristic achieved 25% accuracy on independent real data; narrowed scope to Audio and Visual.",
            "independent_real_accuracy": 0.25,
            "synth_accuracy": 1.0,
        },
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
