# Design System — CAPTCHA Solver Demo UI

Applies to the demo application (Streamlit/Flask/React) used to showcase the router + 3 specialist models. Kept intentionally lightweight since the core deliverable is the ML pipeline, not the UI.

## 1. Purpose of the UI
- Let a user (or the instructor) upload/select a CAPTCHA sample (audio file, grid image, or puzzle image pair).
- Show the router's predicted type, the specialist invoked, and the final answer.
- Display confidence scores and, for visual/puzzle types, an annotated image (selected cells / detected offset marker).

## 2. Screens
1. **Home / Upload screen** — file upload or sample picker (dropdown of bundled demo CAPTCHAs).
2. **Processing screen** — shows router classification result first, then specialist output (can be a single screen with progressive reveal rather than a separate page).
3. **Result screen** — final answer, confidence, and annotated visualization.
4. **(Optional) Benchmark screen** — table of accuracy per model, confusion matrix for the router, pulled from the evaluation harness output.

## 3. Layout Principles
- Single-column, centered content (max-width ~720px) — this is a demo, not a full product; avoid building a complex dashboard.
- One primary action visible at a time ("Upload / Select Sample" → "Solve" → "View Result").
- Results always show: **Predicted Type → Specialist Used → Answer → Confidence**, in that order, so the router's role is visible, not hidden.

## 4. Color Palette
| Role | Color | Usage |
|---|---|---|
| Primary | `#2563EB` (blue) | Buttons, active states, links |
| Success | `#16A34A` (green) | Correct/high-confidence results |
| Warning | `#F59E0B` (amber) | Low-confidence results |
| Error | `#DC2626` (red) | Failed solve / low router confidence |
| Neutral background | `#F8FAFC` | Page background |
| Neutral text | `#0F172A` | Body text |
| Border/divider | `#E2E8F0` | Card borders |

Each specialist type gets a small accent tag color for quick visual scanning:
- Audio → purple `#7C3AED`
- Visual → teal `#0D9488`
- Puzzle/Reasoning → orange `#EA580C`

## 5. Typography
- Font: system UI stack (`Inter`, `-apple-system`, `Segoe UI`, sans-serif) — no custom font loading needed for a demo.
- Headings: 20–28px, semi-bold.
- Body: 14–16px, regular.
- Monospace (for raw model output / confidence numbers): `ui-monospace`, `SFMono-Regular`, `Menlo`.

## 6. Components
- **Type Badge** — small pill showing predicted CAPTCHA type with its accent color (Audio/Visual/Puzzle).
- **Confidence Bar** — thin horizontal bar, colored green/amber/red by threshold (e.g. >80% green, 50–80% amber, <50% red).
- **Result Card** — bordered card containing: type badge, input preview (thumbnail/waveform), answer, confidence bar.
- **Annotated Image** — for visual (highlight selected grid cells with colored border) and puzzle (draw offset line/marker on the background image).
- **Upload/Sample Picker** — drag-and-drop zone + a "try a sample" dropdown of bundled demo files so evaluators don't need their own CAPTCHA files.
- **Benchmark Table** — simple striped table with per-model accuracy and a confusion-matrix mini-grid for the router.

## 7. States
- **Loading:** simple spinner + step label ("Classifying type…", "Running visual model…").
- **Empty:** friendly prompt ("Upload a CAPTCHA or pick a sample to begin").
- **Error:** clear message with the failure reason (e.g. "Unsupported file type", "Model failed to load").

## 8. Accessibility
- Color is never the only signal — confidence and type badges include text labels, not just color.
- Audio player has visible controls (not autoplay).
- Sufficient contrast: body text `#0F172A` on `#F8FAFC` background passes WCAG AA.

## 9. Notes for Antigravity Build
- Keep the UI as a thin wrapper around the `CaptchaSolver` interface defined in ARCHITECTURE.md — UI should call `route_and_solve(input_path)` and render its return dict, not embed model logic.
- Favor a single-file Streamlit app for v1 (fastest to build/demo); only move to Flask/React if interactivity needs grow (e.g. live drag for puzzle solving).
