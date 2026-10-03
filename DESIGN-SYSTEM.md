# Design System — Multi-Modal CAPTCHA Solver Evaluation Interface

Guidelines for terminal and visualization outputs in the academic pipeline.

## 1. Scope & Focus
The final project focuses exclusively on two deep learning modalities:
- **Audio Specialist:** Spoken digit/letter transcription (Wav2Vec2 ASR).
- **Visual Specialist:** 3x3 challenge grid classification (CLIP Zero-Shot Vision-Language model).
- **Binary Router:** Deterministic dispatcher classifying inputs as either `audio` or `visual`.

*(Spatial slider puzzle heuristics have been officially removed from scope).*

## 2. Status & Metric Badges
Terminal logs and reports adhere to the following color/accent conventions:
- **Audio:** Purple/Magenta `#A855F7` / `#EC4899`
- **Visual:** Teal/Cyan `#0D9488` / `#06B6D4`
- **Router:** Emerald Green `#10B981`

## 3. Standardized Output Schema
Every execution returns a unified structured dictionary:
```python
{
    "predicted_type": "audio" | "visual",
    "router_confidence": 0.99,
    "specialist_used": "audio" | "visual",
    "answer": [...],      # list of cell ints for visual, string for audio
    "specialist_confidence": float,
    "details": dict
}
```

## 4. Evaluation Formatting
- Character Error Rate (CER) and Exact Match % are reported for Audio.
- Mean Cell Accuracy and F1 Score are reported for Visual.
- Zero-shot and fine-tuned results are benchmarked against separate real-world held-out sets.
