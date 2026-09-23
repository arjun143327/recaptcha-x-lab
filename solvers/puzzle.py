"""Puzzle / Reasoning Specialist Solver for Slider CAPTCHA Challenges.

Adapted from: prashant-italiya/Slider-Captcha-Automation
Detects the target puzzle piece notch / gap in a background slider image
and calculates the exact horizontal slider offset (in pixels).

Backends:
  1. Default: High-precision OpenCV edge & contour notch detector (zero extra dependencies).
  2. Pluggable: YOLOv8 model backend (activated when ultralytics & weights are present).
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

from solvers.base import CaptchaSolver, InvalidInputError, ModelLoadError


DEFAULT_YOLO_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "puzzle",
    "best.pt"
)


class PuzzleSolver:
    """Specialist solver for horizontal slider puzzle CAPTCHAs."""

    def __init__(
        self,
        weights_path: Optional[str] = DEFAULT_YOLO_WEIGHTS_PATH,
        piece_size: int = 44,
        tolerance_px: float = 5.0
    ):
        self.weights_path = weights_path
        self.piece_size = piece_size
        self.tolerance_px = tolerance_px
        self.yolo_model = None
        self._init_yolo_if_available()

    def _init_yolo_if_available(self) -> None:
        """Initialize YOLOv8 backend if ultralytics is installed and weights exist."""
        if self.weights_path and os.path.exists(self.weights_path):
            try:
                from ultralytics import YOLO
                print(f"[PuzzleSolver] Loading YOLOv8 puzzle model from {self.weights_path}...")
                self.yolo_model = YOLO(self.weights_path)
            except ImportError:
                # ultralytics not installed; OpenCV detector will be used
                self.yolo_model = None
            except Exception as exc:
                print(f"[PuzzleSolver] Warning: Could not load YOLO model: {exc}")
                self.yolo_model = None

    def _detect_gap_opencv(self, img_bgr: np.ndarray) -> Tuple[float, int, List[int], float]:
        """Detect the puzzle piece notch/gap using OpenCV edge and contour analysis.
        
        Algorithm:
          1. Dynamically scale target notch size based on image resolution (calibrated at 44px for 260px width).
          2. Grayscale & bilateral filter to preserve edges while smoothing texture.
          3. Canny edge detection and morphological close to consolidate outline.
          4. Search for square/rectangular contours resembling the puzzle piece size.
          5. Filter out left slider track (x < 10% of width) and select the most prominent notch.
        """
        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Bilateral filter retains sharp notch boundary while smoothing gradients
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Canny edge detector
        edges = cv2.Canny(filtered, 50, 150)
        
        # Morphological close to consolidate outline
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Scale piece size proportionally to image resolution (standard Geetest is 260x160 with ~44px piece)
        scale_factor = max(0.4, w / 260.0)
        eff_piece_size = max(24, int(self.piece_size * scale_factor))
        target_area = float(eff_piece_size * eff_piece_size)
        
        candidate_boxes = []
        for c in contours:
            bx, by, bw, bh = cv2.boundingRect(c)
            # Ignore left margin where piece starts or slider track
            if bx < int(w * 0.10):
                continue
            # Ignore too close to right edge
            if bx > int(w * 0.95):
                continue
                
            area = float(bw * bh)
            # Check aspect ratio of the bounding box (piece is approx square)
            aspect = float(bw) / float(bh) if bh > 0 else 0
            
            # Match piece size within tolerance (0.3x to 2.5x area, aspect ratio 0.55 to 1.8)
            if 0.3 * target_area <= area <= 2.5 * target_area and 0.55 <= aspect <= 1.8:
                # Dark patch check: the gap in slider CAPTCHAs is shadowed
                roi = gray[by:by + bh, bx:bx + bw]
                mean_darkness = float(np.mean(roi)) if roi.size > 0 else 255.0
                
                # Perimeter contrast score relative to effective piece size
                score = (1.0 / (abs(bw - eff_piece_size) + 1.0)) * (1.0 / (abs(bh - eff_piece_size) + 1.0))
                candidate_boxes.append((bx, by, bw, bh, score, mean_darkness))

        if candidate_boxes:
            # Pick candidate with highest matching score
            candidate_boxes.sort(key=lambda item: (item[4], -item[5]), reverse=True)
            best_x, best_y, best_w, best_h, score, _ = candidate_boxes[0]
            confidence = min(0.98, max(0.70, 0.70 + score * 0.25))
            return float(best_x), int(best_y), [best_x, best_y, best_w, best_h], round(confidence, 4)

        # Fallback: sliding window edge correlation
        best_val = -1.0
        best_pos = (int(w * 0.5), int(h * 0.3))
        pw = eff_piece_size
        ph = eff_piece_size
        step = max(5, int(5 * scale_factor))
        
        for y_scan in range(10, max(11, h - ph - 10), step):
            for x_scan in range(int(w * 0.15), max(int(w * 0.16), w - pw - 10), step):
                patch = closed[y_scan: y_scan + ph, x_scan: x_scan + pw]
                if patch.shape[0] != ph or patch.shape[1] != pw:
                    continue
                # High perimeter edge count indicates notch boundaries
                top_edge = np.sum(patch[0:3, :])
                bot_edge = np.sum(patch[-3:, :])
                left_edge = np.sum(patch[:, 0:3])
                right_edge = np.sum(patch[:, -3:])
                boundary_sum = float(top_edge + bot_edge + left_edge + right_edge)
                
                if boundary_sum > best_val:
                    best_val = boundary_sum
                    best_pos = (x_scan, y_scan)

        fx, fy = best_pos
        confidence = 0.70
        return float(fx), int(fy), [fx, fy, pw, ph], confidence

    def solve(self, input_path: str, **kwargs: Any) -> Dict[str, Any]:
        """Solve a slider puzzle challenge.
        
        Args:
            input_path: Path to the slider puzzle background image.
            **kwargs: Extra parameters.
            
        Returns:
            Dict containing:
              - 'answer': Float representing horizontal slider offset (in pixels).
              - 'confidence': Float confidence score.
              - 'details': Detected notch coordinates and bounding box.
        """
        if not os.path.exists(input_path):
            raise InvalidInputError(f"Puzzle image file not found: {input_path}")

        img_bgr = cv2.imread(input_path)
        if img_bgr is None:
            raise InvalidInputError(f"OpenCV could not decode image: {input_path}")

        # If YOLOv8 model is available, use it
        if self.yolo_model is not None:
            try:
                results = self.yolo_model(input_path, verbose=False)
                for r in results:
                    boxes = r.boxes
                    if len(boxes) > 0:
                        # Extract first detected box
                        xyxy = boxes.xyxy[0].cpu().numpy()
                        conf = float(boxes.conf[0].cpu().item())
                        bx0, by0, bx1, by1 = [float(v) for v in xyxy]
                        offset_x = bx0
                        return {
                            "answer": round(offset_x, 1),
                            "confidence": round(conf, 4),
                            "modality": "puzzle",
                            "details": {
                                "offset_x": round(offset_x, 1),
                                "y": round(by0, 1),
                                "bbox": [int(bx0), int(by0), int(bx1 - bx0), int(by1 - by0)],
                                "method": "yolov8_detection"
                            }
                        }
            except Exception as exc:
                print(f"[PuzzleSolver] YOLO inference failed: {exc}, using OpenCV backend.")

        # Default OpenCV backend
        offset_x, gap_y, bbox, confidence = self._detect_gap_opencv(img_bgr)
        return {
            "answer": round(offset_x, 1),
            "confidence": confidence,
            "modality": "puzzle",
            "details": {
                "offset_x": round(offset_x, 1),
                "y": gap_y,
                "bbox": bbox,
                "method": "opencv_canny_contour"
            }
        }

    def evaluate_fixtures(self, fixtures_dir: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate solver on bundled puzzle fixtures and compute offset accuracy within tolerance."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = fixtures_dir or os.path.join(base_dir, "data", "puzzle")
        gt_file = os.path.join(target_dir, "ground_truth.json")

        if not os.path.exists(gt_file):
            raise FileNotFoundError(f"Puzzle ground truth not found at {gt_file}")

        with open(gt_file, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        results = []
        total_error = 0.0
        correct_count = 0

        for filename, meta in ground_truth.items():
            filepath = os.path.join(target_dir, filename)
            if not os.path.exists(filepath):
                continue
            solve_res = self.solve(filepath)
            pred_offset = float(solve_res["answer"])
            expected = float(meta["offset_x"])
            tolerance = float(meta.get("tolerance_px", self.tolerance_px))
            error_px = abs(pred_offset - expected)
            is_correct = (error_px <= tolerance)

            total_error += error_px
            if is_correct:
                correct_count += 1

            results.append({
                "file": filename,
                "expected_offset": expected,
                "predicted_offset": pred_offset,
                "tolerance_px": tolerance,
                "error_px": round(error_px, 2),
                "within_tolerance": is_correct,
                "confidence": solve_res["confidence"]
            })

        n = len(results) or 1
        summary = {
            "num_samples": len(results),
            "tolerance_px": self.tolerance_px,
            "accuracy": round(correct_count / n, 4),
            "mean_pixel_error": round(total_error / n, 2),
            "sample_results": results
        }
        return summary
