# PRD — Multi-Modal reCAPTCHA Solver with Model Router

## 1. Overview
A system that solves reCAPTCHA-style challenges across three modalities — **Audio**, **Visual**, and **Puzzle/Reasoning** — using three specialist models, dispatched by a 4th **Router Model** that classifies the incoming CAPTCHA type and forwards it to the correct specialist.

This is a semester ML project. Scope favors reusing and adapting existing open-source trained models over training from scratch, given time and data constraints.

## 2. Goals
- Build a working end-to-end pipeline: input CAPTCHA → router classifies type → correct specialist solves it → answer returned.
- Demonstrate measurable accuracy per specialist model and for the router's classification step.
- Produce a demo (CLI or simple web UI) showing the pipeline running on sample CAPTCHAs.

## 3. Non-Goals
- Not building a production CAPTCHA-bypass service or browser-automation bot.
- Not training large models from scratch — base models are adapted/fine-tuned from existing repos.
- Not covering every CAPTCHA vendor (Cloudflare Turnstile, hCaptcha, etc.) — scope is reCAPTCHA-style challenges only (image grid, audio, slider puzzle).

## 4. Users
- Instructor/evaluator reviewing the semester project.
- Project team members (Arjun + collaborators) building and demoing it.

## 5. Functional Requirements

### 5.1 Specialist Models
| Model | Type | Base Repo | Task |
|---|---|---|---|
| Visual | Image-grid classification | `LudwigStumpp/zero-shot-captcha-solver` (CLIP zero-shot) | Given a 3x3 grid image + object prompt, classify each cell as hit/no-hit |
| Audio | Speech-to-text | `sampritipanda/audio_captcha_solver` (baseline) and/or `pritam123junior/audio-captcha-solver` (Wav2Vec2 + CRNN) | Transcribe spoken digits/letters from audio CAPTCHA |
| Reasoning/Puzzle | Spatial offset detection | `prashant-italiya/Slider-Captcha-Automation` (YOLOv8) | Detect puzzle-piece position and compute the slider offset needed to solve it |

### 5.2 Router Model
- **Input:** a CAPTCHA file (image, audio, or puzzle image pair) of unknown type.
- **Task:** classify the input's modality/type — Audio vs Visual (grid) vs Puzzle — then forward it to the matching specialist.
- **Approach:** lightweight classifier (file type + simple feature check, or a small CNN on a thumbnail) rather than a heavy model — modality is usually a near-trivial classification.
- **Output:** the specialist's answer plus the predicted CAPTCHA type (for transparency/evaluation).

### 5.3 Pipeline Flow
1. User/test harness submits a CAPTCHA sample.
2. Router identifies modality.
3. Router invokes the matching specialist model.
4. Specialist returns the solved answer (grid selections / transcribed text / slider offset).
5. Result + confidence + predicted type displayed to user.

### 5.4 Evaluation
- Per-specialist accuracy reported separately (using each base repo's existing test data/dataset where possible).
- Router classification accuracy (confusion matrix across the 3 types).
- End-to-end accuracy: correct type routing AND correct specialist answer.

## 6. Data
- Reuse each base repo's provided sample/training data where licensing allows.
- Supplement/scale audio data using `sampritipanda`'s synthetic data generation scripts if original 50-sample set proves too small.
- Visual: CLIP is zero-shot, so no training data is strictly required, only test/demo images.
- Puzzle: use `Slider-Captcha-Automation`'s labeling workflow (CVAT/LabelImg) if fine-tuning YOLOv8 further; otherwise use their pretrained weights as-is.

## 7. Constraints
- Small dataset sizes; limited compute (likely Colab/free-tier GPU).
- Time-boxed semester timeline.
- Legal/ethical framing: this is defensive/security-research style analysis of CAPTCHA robustness for academic purposes, not a production bypass tool.

## 8. Deliverables
- Working demo pipeline (script or simple UI) that runs the router → specialist flow.
- Accuracy report/benchmarks per model and end-to-end.
- Project report/paper documenting architecture, datasets, results, and limitations.
- Source code repo with the three adapted specialist models + router.

## 9. Success Criteria
- Router correctly identifies input modality with high accuracy (target: >90%, since this is a near-trivial classification task).
- Each specialist matches or approaches the reported accuracy of its base repo on your own test samples.
- End-to-end demo runs without manual intervention on a batch of mixed CAPTCHA samples.

## 10. Risks
- Small/imbalanced dataset — mitigate with synthetic data generation and data augmentation.
- Reused pretrained models may not generalize to your specific CAPTCHA samples — mitigate by fine-tuning lightly on your own collected samples.
- Puzzle model (YOLOv8) needs labeled bounding boxes if fine-tuning is required — budget time for annotation.
