"""Router component — Modality Classifier for reCAPTCHA challenges.

Identifies whether an incoming CAPTCHA file belongs to:
  - 'audio'  (spoken letters/digits)
  - 'visual' (3x3 image grid challenge)
  - 'puzzle' (horizontal slider puzzle)

Implements fast-path audio detection and image feature classification 
(aspect ratio + grid structure) with a trained sklearn model fallback.
"""

import os
import mimetypes
from typing import Any, Dict, Optional, Tuple
import numpy as np
from PIL import Image

try:
    import joblib
except ImportError:
    joblib = None

from solvers.base import InvalidInputError


AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

# Path to serialized model if trained
DEFAULT_ROUTER_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "router",
    "router_model.joblib"
)


class RouterModel:
    """Modality classifier for CAPTCHA challenges."""

    def __init__(self, model_path: Optional[str] = DEFAULT_ROUTER_MODEL_PATH):
        self.model_path = model_path
        self.clf = None
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load trained sklearn classifier if available."""
        if self.model_path and os.path.exists(self.model_path) and joblib is not None:
            try:
                self.clf = joblib.load(self.model_path)
            except Exception:
                self.clf = None

    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """Check if file is an audio challenge via extension and file headers."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            return True
        
        # Check MIME type
        mime, _ = mimetypes.guess_type(file_path)
        if mime and mime.startswith("audio/"):
            return True

        # Header magic bytes check
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    header = f.read(12)
                    # RIFF....WAVE or ID3 or OggS or fLaC
                    if header.startswith(b"RIFF") and b"WAVE" in header:
                        return True
                    if header.startswith(b"ID3") or header.startswith(b"OggS") or header.startswith(b"fLaC"):
                        return True
            except OSError:
                pass
        return False

    @staticmethod
    def extract_image_features(image_path: str) -> Tuple[np.ndarray, Dict[str, float]]:
        """Extract spatial and structural features for image disambiguation (visual vs puzzle).
        
        Visual (3x3 grid) challenges:
          - Square aspect ratio (width / height ~ 1.0)
          - Strong grid divider transitions at 1/3 and 2/3 coordinates
        
        Puzzle (slider) challenges:
          - Panoramic rectangular aspect ratio (width / height ~ 1.8 to 2.5)
          - Continuous landscape/scene textures with concentrated cutout notch
        """
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            w, h = img_rgb.size
            aspect_ratio = float(w) / float(h)
            
            # Downsample to normalized 90x90 for fast structural gradient check
            thumb = img_rgb.resize((90, 90), Image.BILINEAR)
            arr = np.array(thumb, dtype=np.float32).mean(axis=2)  # grayscale

            # Compute horizontal and vertical gradient lines at 1/3 (index 30) and 2/3 (index 60)
            diff_y = np.abs(np.diff(arr, axis=0))
            diff_x = np.abs(np.diff(arr, axis=1))

            # Mean edge intensity along grid division lines (indices ~29-31 and ~59-61)
            h_grid_edge = float(np.mean(diff_y[[29, 30, 59, 60], :]))
            v_grid_edge = float(np.mean(diff_x[:, [29, 30, 59, 60]]))
            bg_edge = float((np.mean(diff_y) + np.mean(diff_x)) / 2.0 + 1e-6)
            grid_ratio = float((h_grid_edge + v_grid_edge) / (2.0 * bg_edge))

            features = np.array([aspect_ratio, grid_ratio, float(w), float(h)], dtype=np.float32)
            meta = {
                "width": float(w),
                "height": float(h),
                "aspect_ratio": aspect_ratio,
                "grid_ratio": grid_ratio
            }
            return features, meta

    def classify(self, input_path: str) -> Dict[str, Any]:
        """Classify input challenge file into 'audio', 'visual', or 'puzzle'.
        
        Args:
            input_path: Path to the CAPTCHA file.
            
        Returns:
            Dict containing:
              - 'type': 'audio' | 'visual' | 'puzzle'
              - 'confidence': float (0.0 to 1.0)
              - 'method': string explaining classification rule/model
              - 'details': dict with diagnostic feature values
        """
        if not os.path.exists(input_path):
            raise InvalidInputError(f"Input file not found: {input_path}")

        # 1. Fast-path audio check
        if self.is_audio_file(input_path):
            return {
                "type": "audio",
                "confidence": 0.99,
                "method": "fast_path_audio_extension_header",
                "details": {"path": input_path}
            }

        # 2. Image modality check
        ext = os.path.splitext(input_path)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            # Check if it opens as an image despite missing extension
            try:
                with Image.open(input_path):
                    pass
            except Exception as exc:
                raise InvalidInputError(f"Unsupported file format: {input_path}") from exc

        features, meta = self.extract_image_features(input_path)
        aspect_ratio = meta["aspect_ratio"]

        # 3. Use trained model if loaded
        if self.clf is not None:
            try:
                feat_2d = features.reshape(1, -1)
                pred_label = self.clf.predict(feat_2d)[0]
                proba = float(np.max(self.clf.predict_proba(feat_2d)))
                return {
                    "type": str(pred_label),
                    "confidence": round(proba, 4),
                    "method": "trained_sklearn_classifier",
                    "details": meta
                }
            except Exception:
                pass  # Fall back to heuristic rule

        # 4. Heuristic classifier (aspect ratio + grid boundary)
        # Visual 3x3 grids are square (~1.0). Slider puzzles are rectangular (~2.0).
        # Decision boundary at aspect ratio 1.4
        if aspect_ratio < 1.4:
            # Visual grid
            # Confidence scales with closeness to 1.0
            dist = abs(aspect_ratio - 1.0)
            confidence = max(0.80, min(0.99, 1.0 - (dist * 0.5)))
            predicted_type = "visual"
        else:
            # Slider puzzle
            dist = abs(aspect_ratio - 2.0)
            confidence = max(0.80, min(0.99, 1.0 - (dist * 0.3)))
            predicted_type = "puzzle"

        return {
            "type": predicted_type,
            "confidence": round(float(confidence), 4),
            "method": "heuristic_aspect_ratio_and_geometry",
            "details": meta
        }


# Global singleton instance for easy import
router = RouterModel()


def classify(input_path: str) -> Dict[str, Any]:
    """Convenience function wrapping the RouterModel classify method."""
    return router.classify(input_path)
