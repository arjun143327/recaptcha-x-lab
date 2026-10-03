# PRD — Multi-Modal reCAPTCHA Solver with Binary Model Router

## 1. Overview
A system that solves reCAPTCHA-style challenges across two key modalities — **Audio** and **Visual** — using two specialist deep learning foundation models, dispatched by a lightweight binary **Router Model** that classifies incoming CAPTCHA challenges (audio waveform vs. visual grid) and forwards each to the matching specialist.

This is an academic semester ML project analyzing the robustness of challenge-response systems across different modalities. The scope favors adapting existing open-source foundation models (Wav2Vec2 for speech, CLIP for zero-shot vision-language alignment) over training from scratch.

*Note on Project Scope Evolution:* An initial heuristic spatial reasoning/puzzle solver (OpenCV Canny contour detection) was investigated but discarded after empirical validation: while achieving 100% on clean synthetic backgrounds, it collapsed to 25% accuracy on independent real-world slider benchmarks. The project scope was formally narrowed to deep learning foundation models (Audio & Visual) to prioritize methodological rigor.

## 2. Goals
- Build a working end-to-end pipeline: input CAPTCHA → binary router classifies modality (audio vs. visual) → matching specialist solves it → standardized answer returned.
- Empirically measure robustness, accuracy, and domain gap across both specialist models and the router.
- Evaluate acoustic domain gaps under real-world noise/distortion and visual zero-shot generalization across distinct semantic categories.
- Produce a reproducible CLI pipeline (`python main.py --demo` and `python main.py --test`).

## 3. Non-Goals
- Not building a production CAPTCHA-bypass service or live web automation bot.
- Not training multi-billion parameter foundation models from scratch — base models are adapted and evaluated from published research checkpoints.
- Not supporting third-party vendor CAPTCHAs (Cloudflare Turnstile, hCaptcha) — scope is reCAPTCHA challenge modalities (audio speech transcription & 3x3 image grids).
- Spatial slider puzzles are explicitly out of scope (discarded due to classical heuristic fragility).

## 4. Users
- Evaluator/instructor reviewing the semester machine learning assignment.
- Research collaborators testing multi-modal model robustness.

## 5. Functional Requirements

### 5.1 Specialist Models
| Model | Type | Architecture / Base Checkpoint | Task |
|---|---|---|---|
| **Visual** | Zero-Shot Image-Grid Classification | `openai/clip-vit-base-patch32` (or `clip-vit-large-patch14`) | Given a 3x3 grid image + target prompt, classify each cell as hit/no-hit |
| **Audio** | Speech-to-Text Transcription | `facebook/wav2vec2-base-960h` (+ acoustic preprocessing / fine-tuning) | Transcribe spoken letters/digits from distorted audio challenges |

### 5.2 Router Model
- **Input:** A CAPTCHA challenge file (audio waveform or grid image).
- **Task:** Binary classification between `'audio'` and `'visual'`, then dispatch to the specialist.
- **Approach:** High-efficiency fast-path header inspection (RIFF/WAVE/ID3/MIME) and image validation.
- **Output:** `{type: "audio" | "visual", confidence: float, details: dict}`.

### 5.3 Pipeline Flow
1. Input CAPTCHA submitted via CLI or test suite.
2. Binary Router classifies modality (`audio` vs `visual`).
3. Router dispatches challenge to the corresponding specialist model.
4. Specialist returns standardized answer (list of grid cell indices for Visual; transcribed character string for Audio).
5. Aggregator formats prediction, confidence scores, and diagnostic metadata.

### 5.4 Evaluation Metrics
- **Router:** Binary classification accuracy and confusion matrix.
- **Visual Specialist:** Cell-level accuracy, F1 score, exact grid match rate across 10 semantic categories.
- **Audio Specialist:** Character Error Rate (CER), Levenshtein edit distance, exact string match rate across synthetic vs. real SecurImage audio.
- **End-to-End Pipeline:** Compound accuracy (correct routing AND correct solution).

## 6. Datasets
- **Audio Data:**
  - Synthetic: Clean TTS spoken digits/letters for baseline calibration.
  - Real-World: SecurImage audio challenges with synthetic multi-speaker noise, pitch shifts, and reverberation.
- **Visual Data:**
  - Synthetic: 3x3 synthetic image grids with known object placements.
  - Real-World: Real reCAPTCHA v2 image grids from benchmark sets (ETH Zurich / public collections across 10 categories: traffic light, chimney, fire hydrant, bus, etc.).

## 7. Constraints
- Hardware: Standard workstation / Colab GPU execution.
- Frameworks: PyTorch, HuggingFace Transformers, librosa/scipy, Pillow.
- Ethics: Defensive security-research framing assessing the degradation of CAPTCHAs against modern self-supervised transformers.

## 8. Deliverables
1. Python modular codebase (`solvers/router.py`, `solvers/audio.py`, `solvers/visual.py`, `solvers/pipeline.py`).
2. Test suites verifying router and end-to-end pipeline execution (`tests/test_router.py`, `tests/test_pipeline.py`).
3. Benchmark evaluation report (`main.py --test` and `eval/run_eval.py`).
4. Documentation and academic report summarizing methodology and findings.
