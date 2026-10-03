"""Binary Router Component — Modality Classifier for reCAPTCHA challenges.

Classifies incoming CAPTCHA challenge files into:
  - 'audio'  (spoken letters/digits waveform)
  - 'visual' (3x3 image grid challenge)

Uses fast-path audio header detection (RIFF/WAVE, ID3, OggS, fLaC magic bytes)
and image header validation via Pillow.
"""

import os
import mimetypes
from typing import Any, Dict
from PIL import Image

from solvers.base import InvalidInputError


AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


class RouterModel:
    """Binary modality classifier for Audio vs. Visual CAPTCHA challenges."""

    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """Check if file is an audio challenge via extension, MIME, or header magic bytes."""
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
                    if header.startswith(b"RIFF") and b"WAVE" in header:
                        return True
                    if header.startswith(b"ID3") or header.startswith(b"OggS") or header.startswith(b"fLaC"):
                        return True
            except OSError:
                pass
        return False

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Validate if file is a valid readable image format."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            return True
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def classify(self, input_path: str) -> Dict[str, Any]:
        """Classify input challenge file strictly into 'audio' or 'visual'.
        
        Args:
            input_path: Path to the CAPTCHA file.
            
        Returns:
            Dict containing:
              - 'type': 'audio' | 'visual'
              - 'confidence': float (0.0 to 1.0)
              - 'method': string explaining classification rule
              - 'details': dict with diagnostic values
        """
        if not os.path.exists(input_path):
            raise InvalidInputError(f"Input file not found: {input_path}")

        # 1. Fast-path audio check
        if self.is_audio_file(input_path):
            return {
                "type": "audio",
                "confidence": 0.99,
                "method": "fast_path_audio_extension_header",
                "details": {"path": input_path, "modality": "audio"}
            }

        # 2. Image verification -> Visual grid modality
        if self.is_image_file(input_path):
            try:
                with Image.open(input_path) as img:
                    w, h = img.size
                return {
                    "type": "visual",
                    "confidence": 0.99,
                    "method": "image_grid_visual_modality",
                    "details": {"path": input_path, "width": w, "height": h, "modality": "visual"}
                }
            except Exception as exc:
                raise InvalidInputError(f"Unreadable image challenge: {input_path}") from exc

        raise InvalidInputError(f"Unsupported or unrecognized CAPTCHA modality: {input_path}")


# Global singleton instance for easy import
router = RouterModel()


def classify(input_path: str) -> Dict[str, Any]:
    """Convenience function wrapping the RouterModel classify method."""
    return router.classify(input_path)
