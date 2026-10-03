# Architecture — Multi-Modal reCAPTCHA Solver (Audio & Visual)

## 1. High-Level Architecture Diagram

```
                         ┌───────────────────────┐
                         │      Input CAPTCHA     │
                         │ (audio waveform/image)│
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Binary Router Model  │
                         │  (audio vs. visual)   │
                         └───────────┬───────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
           ┌───────────────────┐           ┌───────────────────┐
           │   Visual Model    │           │    Audio Model    │
           │ (CLIP Zero-Shot)  │           │   (Wav2Vec2 ASR)  │
           │  openai/clip-vit  │           │ facebook/wav2vec2 │
           └─────────┬─────────┘           └─────────┬─────────┘
                     │                               │
                     └───────────────┬───────────────┘
                                     ▼
                         ┌───────────────────────┐
                         │   Result Aggregator   │
                         │(answer + type + conf) │
                         └───────────┬───────────┘
                                     ▼
                         ┌───────────────────────┐
                         │    CLI / Eval Output  │
                         └───────────────────────┘
```

## 2. Component Descriptions

### 2.1 Binary Router Model (`solvers/router.py`)
- **Purpose:** Classify incoming CAPTCHA challenge into either `audio` or `visual`.
- **Mechanism:** Fast-path binary file inspection:
  - Header inspection (RIFF/WAVE, ID3, OggS, fLaC magic bytes) + audio extension matching.
  - Image header validation via PIL (PNG, JPG, JPEG, WebP).
- **Output:** `{"type": "audio" | "visual", "confidence": float, "details": dict}`.
- **Complexity:** $O(1)$ header verification without needing heavyweight inference, achieving 100% routing accuracy.

### 2.2 Visual Specialist (`solvers/visual.py`)
- **Model Checkpoint:** `openai/clip-vit-base-patch32` (with optional drop-in evaluation of `openai/clip-vit-large-patch14`).
- **Pipeline:**
  1. Input 3x3 challenge grid is sliced into 9 sub-tiles.
  2. Sub-tiles are encoded into normalized visual feature embeddings via CLIP vision encoder.
  3. The prompt label (e.g. "traffic light", "bus", "fire hydrant") is encoded via CLIP text encoder.
  4. Prompt ensembling averages embeddings across contextual phrases (e.g. "a photo of a {target}", "a {target}").
  5. Cosine similarities between text and tile embeddings determine hit cell indices.
- **Output:** List of matched cell indices (e.g. `[1, 5, 8]`).

### 2.3 Audio Specialist (`solvers/audio.py`)
- **Model Checkpoint:** `facebook/wav2vec2-base-960h` (with acoustic preprocessing and fine-tuning adapters).
- **Pipeline:**
  1. Audio file loaded, converted to 16 kHz mono float array.
  2. Bandpass filtering and spectral noise reduction to attenuate background synthesizer whine and multi-speaker chatter.
  3. CTC decoding through Wav2Vec2 acoustic model to output characters.
  4. Phonetic post-processing maps spoken words (e.g. "seven", "nine") to digits (`"7"`, `"9"`).
- **Output:** Transcribed alphanumeric string (e.g. `"72941"`).

### 2.4 Result Aggregator & Pipeline (`solvers/pipeline.py`)
- Exposes a unified interface:
  ```python
  def route_and_solve(input_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
      ...
  ```
- Normalizes output schema containing:
  - `predicted_type`: `"audio"` or `"visual"`
  - `router_confidence`: confidence of the routing decision
  - `specialist_used`: specialist solver invoked
  - `answer`: cell indices list or transcribed string
  - `specialist_confidence`: confidence score from the specialist model
  - `details`: metadata, duration, cell scores, or transcript

## 3. Discarded Architectural Elements
- **Spatial Puzzle Solver (OpenCV Canny/YOLOv8):** Initially planned for slider CAPTCHAs, but discarded due to high domain failure (25% on independent real benchmarks) and architectural inconsistency with self-supervised deep learning foundation models.

## 4. Tech Stack
- **Language:** Python 3.9+
- **Deep Learning:** PyTorch, HuggingFace Transformers (`Wav2Vec2ForCTC`, `CLIPModel`, `CLIPProcessor`)
- **Signal & Image Processing:** SciPy, NumPy, Pillow, SoundFile
- **Metrics:** Levenshtein edit distance, Scikit-learn (F1, precision, recall)
