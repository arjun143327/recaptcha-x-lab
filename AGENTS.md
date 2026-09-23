# AGENTS.md — Multi-Modal reCAPTCHA Solver

Instructions for AI coding agents (e.g. Antigravity) working in this repository. Scope: adapt three existing open-source CAPTCHA-solver repos into a unified pipeline with a router model and a lightweight demo UI.

## Project Summary
Three specialist models (Audio, Visual, Puzzle/Reasoning) solve reCAPTCHA-style challenges. A 4th Router model classifies incoming CAPTCHA type and dispatches to the right specialist. See `PRD.md` and `ARCHITECTURE.md` for full context — read those first.

## Source Repos Being Adapted (do not treat as scratch work)
- Visual: `LudwigStumpp/zero-shot-captcha-solver` (CLIP zero-shot, Streamlit app)
- Audio: `sampritipanda/audio_captcha_solver` (baseline, sklearn/keras) and `pritam123junior/audio-captcha-solver` (Wav2Vec2 + CRNN)
- Puzzle/Reasoning: `prashant-italiya/Slider-Captcha-Automation` (YOLOv8)

When integrating these, preserve their original license/attribution headers and cite them in the final report.

## Agent Roles

### 1. `router-agent`
- **Responsibility:** build and maintain the modality classifier (`models/router/`).
- **Inputs:** raw CAPTCHA files under `data/{audio,visual,puzzle}/`.
- **Outputs:** a `classify(input_path) -> {"type": str, "confidence": float}` function.
- **Constraints:** keep it lightweight (rule-based or a small classifier) — do not over-engineer; this is the least complex model in the system.
- **Definition of done:** >90% accuracy on a held-out mixed-type test set, unit-tested.

### 2. `visual-agent`
- **Responsibility:** wrap the CLIP zero-shot solver behind the common `CaptchaSolver` interface (`solvers/visual.py`).
- **Source:** adapt logic from `zero-shot-captcha-solver` (grid split → CLIP embeddings → cosine similarity → clustering).
- **Definition of done:** `solve(input_path) -> {"answer": [...cell indices...], "confidence": float}` implemented and tested against sample grid images.

### 3. `audio-agent`
- **Responsibility:** wrap the audio transcription model behind the common interface (`solvers/audio.py`).
- **Source:** adapt `audio_captcha_solver` baseline and/or `audio-captcha-solver`'s Wav2Vec2+CRNN pipeline.
- **Constraints:** if accuracy on the team's own ~50-sample dataset is too low, use the base repo's synthetic data generation scripts (`gen_data.sh`) to scale data before retraining — do not silently ship a low-accuracy model without flagging it in the eval report.
- **Definition of done:** `solve(input_path) -> {"answer": str, "confidence": float}` implemented; accuracy reported via Levenshtein distance against ground truth.

### 4. `puzzle-agent`
- **Responsibility:** wrap the YOLOv8 slider-puzzle solver behind the common interface (`solvers/puzzle.py`).
- **Source:** adapt `Slider-Captcha-Automation`'s detection + offset-calculation logic.
- **Definition of done:** `solve(input_path) -> {"answer": float, "confidence": float}` (offset in pixels) implemented; accuracy reported via offset tolerance (e.g. within ±5px counted correct).

### 5. `eval-agent`
- **Responsibility:** build and run the evaluation harness (`eval/run_eval.py`).
- **Outputs:** per-model accuracy report, router confusion matrix, end-to-end pipeline accuracy — written to `eval/results.md`.
- **Definition of done:** single command (`python eval/run_eval.py`) reproduces all reported numbers.

### 6. `ui-agent`
- **Responsibility:** build the demo UI per `DESIGN-SYSTEM.md`.
- **Constraints:** UI must only call `route_and_solve(input_path)` from the aggregator — no model logic embedded in UI code.
- **Definition of done:** working Streamlit (or agreed alt.) app that lets a user pick/upload a sample and see router type + specialist answer + confidence.

## Shared Conventions
- **Common interface:** every specialist implements
  ```python
  class CaptchaSolver(Protocol):
      def solve(self, input_path: str) -> dict:  # {"answer": ..., "confidence": float}
  ```
- **Directory layout:**
  ```
  data/{audio,visual,puzzle}/
  models/{router,audio,visual,puzzle}/
  solvers/{router.py,audio.py,visual.py,puzzle.py}
  eval/run_eval.py
  ui/app.py
  ```
- **Do not** re-architect a base repo's core algorithm without noting why in a commit message/PR description — the goal is adaptation, not reinvention.
- **Do** keep each adapted model's dependencies isolated (separate `requirements` sections or virtual envs) if version conflicts arise (e.g. YOLOv8 vs Transformers pinning).
- **Testing:** every `solvers/*.py` needs at least a smoke test that runs `solve()` on one bundled sample file without error.

## Out of Scope for Agents
- Browser automation / live CAPTCHA bypassing on real websites.
- Support for non-reCAPTCHA-style CAPTCHA vendors (hCaptcha, Turnstile, etc.).
- Production deployment/hosting — this is a local academic demo.
