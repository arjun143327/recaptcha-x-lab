"""Visual Specialist Solver for 3x3 Image Grid Challenges.

Adapted from: LudwigStumpp/zero-shot-captcha-solver
Uses CLIP (Contrastive Language-Image Pre-Training) zero-shot classification:
  1. Splits 3x3 grid image into 9 individual tiles.
  2. Computes image embeddings for each tile.
  3. Computes text embedding for the target prompt (e.g., 'traffic light', 'crosswalk').
  4. Calculates cosine similarity and clusters scores into hit/no-hit cell indices.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image
import torch

from solvers.base import CaptchaSolver, InvalidInputError, ModelLoadError


DEFAULT_CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
DEFAULT_PROMPT = "traffic light"


class VisualSolver:
    """Specialist solver for reCAPTCHA 3x3 visual image grid challenges."""

    def __init__(
        self,
        model_name: str = DEFAULT_CLIP_MODEL_NAME,
        device: Optional[str] = None,
        lazy_load: bool = True
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.processor = None
        self._load_failed = False
        
        if not lazy_load:
            self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> bool:
        """Load HuggingFace CLIP processor and model lazily."""
        if self.model is not None and self.processor is not None:
            return True
        if self._load_failed:
            return False

        try:
            from transformers import CLIPModel, CLIPProcessor
            print(f"[VisualSolver] Loading CLIP model '{self.model_name}' on {self.device}...")
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            try:
                self.model = CLIPModel.from_pretrained(self.model_name, use_safetensors=False).to(self.device)
            except Exception:
                self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()
            return True
        except Exception as exc:
            print(f"[VisualSolver] Warning: Could not load HuggingFace CLIP model: {exc}")
            self._load_failed = True
            return False

    @staticmethod
    def split_grid_into_cells(image: Image.Image, rows: int = 3, cols: int = 3) -> List[Image.Image]:
        """Split a composite image grid into rows x cols individual cell images."""
        w, h = image.size
        cell_w = w // cols
        cell_h = h // rows
        cells = []
        for r in range(rows):
            for c in range(cols):
                box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
                cells.append(image.crop(box))
        return cells

    @staticmethod
    def cluster_scores(scores: List[float]) -> Tuple[List[int], float]:
        """Cluster similarity scores into hit/no-hit cells using adaptive thresholding.
        
        Following LudwigStumpp's reference:
        Scores are sorted, and the largest gap between adjacent scores (or threshold)
        is used to separate matching cells from background.
        """
        arr = np.array(scores, dtype=np.float32)
        n = len(arr)
        if n == 0:
            return [], 0.0

        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        
        # Sort scores with their original indices
        sorted_indices = np.argsort(arr)  # ascending
        sorted_scores = arr[sorted_indices]

        # Calculate gaps between adjacent sorted scores
        gaps = np.diff(sorted_scores)
        
        # Consider cutoffs where at least 1 and at most n-1 items are chosen
        if len(gaps) > 0 and np.max(gaps) > 0.03:
            # Split at the largest significant gap
            cutoff_idx = int(np.argmax(gaps))
            # Items above cutoff are matches
            matched_indices = sorted_indices[cutoff_idx + 1:].tolist()
        else:
            # Fallback to mean + 0.2 * std
            threshold = mean_val + 0.2 * std_val
            matched_indices = [int(i) for i, s in enumerate(arr) if s >= threshold]
            
        matched_indices.sort()
        
        # Confidence score: based on how cleanly matches separate from background
        if matched_indices:
            match_mean = float(np.mean([arr[i] for i in matched_indices]))
            bg_indices = [i for i in range(n) if i not in matched_indices]
            bg_mean = float(np.mean([arr[i] for i in bg_indices])) if bg_indices else 0.0
            gap_margin = match_mean - bg_mean
            confidence = max(0.5, min(0.99, 0.5 + gap_margin * 2.0))
        else:
            confidence = 0.5

        return matched_indices, round(confidence, 4)

    def _fallback_solve(self, image: Image.Image, prompt: str) -> Tuple[List[int], List[float], float]:
        """Feature-based fallback when HuggingFace CLIP cannot be downloaded or is offline.
        
        Analyzes color and texture signatures corresponding to common challenge objects:
          - 'traffic light': high localized color contrast with red/yellow/green hue concentrations.
          - 'crosswalk': high-frequency horizontal zebra stripe patterns (horizontal edge variance).
          - 'tree': green foliage canopy chrominance.
        """
        cells = self.split_grid_into_cells(image)
        scores = []
        p_lower = prompt.lower()
        
        for idx, cell in enumerate(cells):
            cell_np = np.array(cell.convert("RGB"), dtype=np.float32)
            r, g, b = cell_np[:, :, 0], cell_np[:, :, 1], cell_np[:, :, 2]
            
            if "traffic" in p_lower or "light" in p_lower:
                # Detect red/yellow/green lamp presence
                red_mask = (r > 160) & (g < 100) & (b < 100)
                yellow_mask = (r > 180) & (g > 150) & (b < 80)
                green_mask = (g > 160) & (r < 100) & (b < 100)
                score = float(np.sum(red_mask | yellow_mask | green_mask)) / (cell_np.shape[0] * cell_np.shape[1])
            elif "crosswalk" in p_lower or "stripe" in p_lower:
                # Detect white stripe contrast on dark road
                white_mask = (r > 200) & (g > 200) & (b > 200)
                score = float(np.sum(white_mask)) / (cell_np.shape[0] * cell_np.shape[1])
            elif "tree" in p_lower:
                # Green foliage dominance
                green_dom = (g > r + 20) & (g > b + 20) & (g > 80)
                score = float(np.sum(green_dom)) / (cell_np.shape[0] * cell_np.shape[1])
            else:
                # General color saturation / entropy
                score = float(np.std(cell_np)) / 128.0
            scores.append(score)

        matched, conf = self.cluster_scores(scores)
        return matched, scores, conf

    def solve(self, input_path: str, prompt: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Solve a 3x3 image grid CAPTCHA challenge.
        
        Args:
            input_path: Path to the 3x3 grid image.
            prompt: Optional target object query (defaults to 'traffic light').
            **kwargs: Extra parameters.
            
        Returns:
            Dict containing:
              - 'answer': List[int] of matching cell indices (0 to 8).
              - 'confidence': Float confidence score (0.0 to 1.0).
              - 'details': Detailed per-cell similarity scores and metadata.
        """
        if not os.path.exists(input_path):
            raise InvalidInputError(f"Visual challenge file not found: {input_path}")

        target_prompt = prompt or DEFAULT_PROMPT

        try:
            image = Image.open(input_path).convert("RGB")
        except Exception as exc:
            raise InvalidInputError(f"Could not open image file: {input_path}") from exc

        # Attempt Hugging Face CLIP inference
        clip_loaded = self._ensure_model_loaded()
        if clip_loaded:
            try:
                cells = self.split_grid_into_cells(image)
                text_queries = [f"a photo of a {target_prompt}", f"a photo without {target_prompt}"]
                
                # Compute image features and text features
                inputs = self.processor(
                    text=text_queries,
                    images=cells,
                    return_tensors="pt",
                    padding=True
                ).to(self.device)

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # Logits per image: shape (9, 2)
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)
                    # Prob of class 0 ("a photo of a {prompt}")
                    similarity_scores = probs[:, 0].cpu().numpy().tolist()

                matched_cells, confidence = self.cluster_scores(similarity_scores)
                return {
                    "answer": matched_cells,
                    "confidence": confidence,
                    "modality": "visual",
                    "details": {
                        "prompt": target_prompt,
                        "method": "clip_zero_shot",
                        "model": self.model_name,
                        "cell_scores": [round(float(s), 4) for s in similarity_scores],
                        "matched_cells": matched_cells,
                        "cell_count": len(cells)
                    }
                }
            except Exception as exc:
                print(f"[VisualSolver] Inference error with CLIP, falling back to feature analyzer: {exc}")

        # Fallback analyzer
        matched_cells, scores, confidence = self._fallback_solve(image, target_prompt)
        return {
            "answer": matched_cells,
            "confidence": confidence,
            "modality": "visual",
            "details": {
                "prompt": target_prompt,
                "method": "adaptive_feature_clustering_fallback",
                "cell_scores": [round(float(s), 4) for s in scores],
                "matched_cells": matched_cells,
                "cell_count": 9
            }
        }

    def evaluate_fixtures(self, fixtures_dir: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate visual solver against bundled fixtures and compute cell-level precision/recall/F1."""
        import json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = fixtures_dir or os.path.join(base_dir, "data", "visual")
        gt_file = os.path.join(target_dir, "ground_truth.json")

        if not os.path.exists(gt_file):
            raise FileNotFoundError(f"Visual ground truth not found at {gt_file}")

        with open(gt_file, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        results = []
        exact_matches = 0
        total_cell_acc = 0.0
        total_f1 = 0.0

        for filename, meta in ground_truth.items():
            filepath = os.path.join(target_dir, filename)
            if not os.path.exists(filepath):
                continue
            prompt = meta.get("prompt", DEFAULT_PROMPT)
            expected_cells = set(meta.get("target_cells", []))

            solve_res = self.solve(filepath, prompt=prompt)
            pred_cells = set(solve_res["answer"])

            tp = len(pred_cells & expected_cells)
            fp = len(pred_cells - expected_cells)
            fn = len(expected_cells - pred_cells)
            tn = 9 - (tp + fp + fn)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            cell_acc = (tp + tn) / 9.0
            is_exact = (pred_cells == expected_cells)

            if is_exact:
                exact_matches += 1
            total_cell_acc += cell_acc
            total_f1 += f1

            results.append({
                "file": filename,
                "prompt": prompt,
                "expected_cells": sorted(list(expected_cells)),
                "predicted_cells": sorted(list(pred_cells)),
                "is_real_recaptcha": meta.get("is_real_recaptcha", False),
                "cell_accuracy": round(cell_acc, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "exact_match": is_exact
            })

        n = len(results) or 1
        return {
            "num_samples": len(results),
            "exact_match_rate": round(exact_matches / n, 4),
            "mean_cell_accuracy": round(total_cell_acc / n, 4),
            "mean_f1_score": round(total_f1 / n, 4),
            "sample_results": results
        }
