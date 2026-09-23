# Architecture — Multi-Modal reCAPTCHA Solver

## 1. High-Level Diagram

```
                         ┌───────────────────────┐
                         │      Input CAPTCHA     │
                         │ (image / audio / pair) │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      Router Model      │
                         │  (modality classifier) │
                         └───────────┬────────────┘
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐
          │ Visual Model │  │ Audio Model  │  │  Reasoning/Puzzle  │
          │ (CLIP zero-  │  │ (Wav2Vec2 /  │  │  Model (YOLOv8     │
          │  shot grid)  │  │  CRNN)       │  │  slider offset)    │
          └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘
                  │                 │                     │
                  └────────────┬────┴─────────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │   Result Aggregator    │
                    │ (answer + type + conf) │
                    └───────────┬────────────┘
                                ▼
                    ┌───────────────────────┐
                    │   Output / Demo UI     │
                    └───────────────────────┘
```

## 2. Components

### 2.1 Router Model
- **Purpose:** classify input CAPTCHA into {audio, visual, puzzle}.
- **Input signals:** file extension/MIME type as a fast-path check; if ambiguous, a lightweight CNN on a downsized thumbnail (visual vs puzzle disambiguation, since both are images).
- **Output:** `{type: "audio"|"visual"|"puzzle", confidence: float}`
- **Implementation:** simple `sklearn`/small `torch` classifier, or even rule-based (file type + aspect ratio heuristics) as a v1, upgraded to a trained classifier later if time allows.

### 2.2 Visual Specialist
- **Base:** `LudwigStumpp/zero-shot-captcha-solver`
- **Pipeline:** split 3x3 grid image → 9 cells → CLIP image embeddings → CLIP text embedding of target object → cosine similarity → cluster into match/no-match.
- **Output:** list of selected cell indices.

### 2.3 Audio Specialist
- **Base:** `sampritipanda/audio_captcha_solver` (baseline algorithm) and/or `pritam123junior/audio-captcha-solver` (Wav2Vec2 + CRNN).
- **Pipeline:** noise reduction/normalization → Wav2Vec2 transcription (or CRNN for digit/letter classification) → decoded text.
- **Output:** transcribed string.
- **Fallback/upgrade path:** if baseline accuracy is too low on your data, fine-tune with synthetic data generated via the repo's `gen_data.sh` scripts.

### 2.4 Reasoning/Puzzle Specialist
- **Base:** `prashant-italiya/Slider-Captcha-Automation`
- **Pipeline:** YOLOv8 object detection on the puzzle-piece + background image → bounding box of the gap → compute x-offset.
- **Output:** numeric offset (pixels) representing the solution.

### 2.5 Result Aggregator
- Combines router's predicted type, chosen specialist's raw output, and a normalized "answer" format.
- Logs router accuracy vs specialist accuracy separately for evaluation.

## 3. Data Flow & Storage
- Raw samples organized as: `data/audio/`, `data/visual/`, `data/puzzle/` (mirrors the structure of the base repos for easy reuse of their scripts).
- Model weights: `models/visual/`, `models/audio/`, `models/puzzle/`, `models/router/`.
- Each specialist is wrapped in a small adapter module exposing a common interface: `solve(input) -> answer`.

## 4. Common Interface (for pluggability)
```python
class CaptchaSolver(Protocol):
    def solve(self, input_path: str) -> dict:
        """Returns {"answer": ..., "confidence": float}"""
```
Each of the three specialists implements this interface, so the router can call them uniformly:
```python
SOLVERS = {
    "visual": VisualSolver(),
    "audio": AudioSolver(),
    "puzzle": PuzzleSolver(),
}

def route_and_solve(input_path):
    captcha_type = router.classify(input_path)
    return SOLVERS[captcha_type].solve(input_path)
```

## 5. Evaluation Harness
- Batch runner that iterates over a labeled test set (type + ground-truth answer), computes:
  - Router classification accuracy (confusion matrix)
  - Per-specialist accuracy (exact match / Levenshtein distance for audio, IoU/offset-tolerance for puzzle, hit/no-hit accuracy for visual)
  - End-to-end pipeline accuracy

## 6. Tech Stack
- Python 3.9+
- PyTorch / Transformers (Wav2Vec2), CLIP (OpenAI/HuggingFace), Ultralytics YOLOv8
- OpenCV for image preprocessing
- scikit-learn for router classifier / metrics
- Optional: Streamlit or a simple Flask/React UI for the demo (reusing the zero-shot repo's Streamlit pattern as a base)

## 7. Deployment/Demo
- Local demo: CLI script or Streamlit app, no need for cloud deployment for a semester project.
- Reproducibility: `requirements.txt`, model weight download instructions, and a `demo.ipynb` notebook showing the full pipeline on sample CAPTCHAs.
