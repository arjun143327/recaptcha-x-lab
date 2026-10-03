# AGENTS.md — Multi-Modal reCAPTCHA Solver (Audio & Visual)

Instructions for AI coding agents working in this repository.

## 1. Project Summary
The system consists of two specialist deep learning foundation models (**Audio** and **Visual**) dispatched by a binary **Router** that classifies incoming challenges (audio waveforms vs. image grids).

- **Audio:** Wav2Vec2 CTC speech transcription.
- **Visual:** CLIP zero-shot vision-language grid tile classification.
- **Router:** Binary classifier distinguishing audio challenges from visual challenge grids.

*Note on Puzzle/Spatial Reasoning:* Spatial slider puzzles have been officially discarded from the pipeline due to poor real-world generalization of heuristic approaches. Do not wire puzzle modules into the router or pipeline.

## 2. Agent Responsibilities

### 2.1 `router-agent`
- **Responsibility:** Maintain the binary modality classifier ([solvers/router.py](file:///d:/college%20projects/ML%20new%20captcha/recaptcha-x-lab/solvers/router.py)).
- **Logic:** Fast-path header and extension check (RIFF/WAVE/ID3 for audio, Pillow image check for visual).
- **Target:** 100% classification accuracy on mixed audio/visual test sets.

### 2.2 `visual-agent`
- **Responsibility:** Maintain and optimize the CLIP zero-shot vision specialist ([solvers/visual.py](file:///d:/college%20projects/ML%20new%20captcha/recaptcha-x-lab/solvers/visual.py)).
- **Techniques:** Prompt ensembling, backbone scaling (`clip-vit-base-patch32` vs `clip-vit-large-patch14`), and optional linear probing on labeled ETH Zurich tiles.
- **Metrics:** Cell-level accuracy, F1 score, exact grid match rate.

### 2.3 `audio-agent`
- **Responsibility:** Maintain and improve the speech recognition specialist ([solvers/audio.py](file:///d:/college%20projects/ML%20new%20captcha/recaptcha-x-lab/solvers/audio.py)).
- **Techniques:** Acoustic noise reduction, bandpass filtering, fine-tuning on real SecurImage samples, comparison against alternative backbones (Whisper/Wav2Vec2-large).
- **Metrics:** Character Error Rate (CER), Levenshtein edit distance, exact string match rate.

### 2.4 `eval-agent`
- **Responsibility:** Run honest benchmark evaluations ([main.py](file:///d:/college%20projects/ML%20new%20captcha/recaptcha-x-lab/main.py) and [eval/run_eval.py](file:///d:/college%20projects/ML%20new%20captcha/recaptcha-x-lab/eval/run_eval.py)).
- **Principles:** Always evaluate on strictly held-out test splits without data leakage.

## 3. Directory Layout
```
data/
  ├── audio/               # WAV audio challenge samples (synthetic & SecurImage real)
  └── visual/              # reCAPTCHA image grid samples (synthetic & real)
models/
  ├── audio/               # Fine-tuned weights / cached checkpoints
  ├── router/              # Router artifacts
  └── visual/              # Visual specialist artifacts
solvers/
  ├── base.py              # CaptchaSolver Protocol and custom Exceptions
  ├── router.py            # Binary modality classifier (Audio vs. Visual)
  ├── audio.py             # Wav2Vec2 CTC audio specialist
  ├── visual.py            # CLIP zero-shot visual specialist
  └── pipeline.py          # Unified route_and_solve aggregator
tests/
  ├── test_router.py       # Binary router unit tests
  └── test_pipeline.py     # End-to-end Audio & Visual smoke tests
main.py                    # CLI runner (--demo, --test, --input)
```
