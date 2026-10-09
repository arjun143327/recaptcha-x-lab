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
        """Check if file is an audio challenge via header magic bytes or valid audio content."""
        if not os.path.exists(file_path):
            return False

        # 1. Header magic bytes check
        try:
            with open(file_path, "rb") as f:
                header = f.read(12)
                if len(header) < 4:
                    return False
                if header.startswith(b"RIFF") and b"WAVE" in header:
                    return True
                if header.startswith(b"ID3") or header.startswith(b"OggS") or header.startswith(b"fLaC") or header.startswith(b"\xff\xfb"):
                    return True
        except OSError:
            pass

        # 2. Extension check with content validation
        ext = os.path.splitext(file_path)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            try:
                from scipy.io import wavfile
                wavfile.read(file_path)
                return True
            except Exception:
                # Corrupted or fake audio file with .wav extension
                return False

        mime, _ = mimetypes.guess_type(file_path)
        if mime and mime.startswith("audio/"):
            return True

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
        # Validate file existence and non-zero size
        if not os.path.exists(input_path):
            raise InvalidInputError(f"Input file not found: {input_path}")

        try:
            file_size = os.path.getsize(input_path)
        except OSError as exc:
            raise InvalidInputError(f"Cannot access challenge file '{os.path.basename(input_path)}': {exc}") from exc

        if file_size == 0:
            raise InvalidInputError(f"Corrupted or empty file (0 bytes): '{os.path.basename(input_path)}'")

        ext = os.path.splitext(input_path)[1].lower()

        # 1. Fast-path audio check
        if self.is_audio_file(input_path):
            return {
                "type": "audio",
                "confidence": 0.99,
                "method": "fast_path_audio_extension_header",
                "details": {"path": input_path, "modality": "audio"}
            }

        # If file claimed to be audio by extension but failed is_audio_file
        if ext in AUDIO_EXTENSIONS:
            raise InvalidInputError(
                f"Corrupted or unreadable audio file: '{os.path.basename(input_path)}' could not be decoded as valid audio."
            )

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
                raise InvalidInputError(
                    f"Corrupted or unreadable image file: '{os.path.basename(input_path)}' could not be opened."
                ) from exc

        # If file claimed to be image by extension but failed is_image_file
        if ext in IMAGE_EXTENSIONS:
            raise InvalidInputError(
                f"Corrupted or unreadable image file: '{os.path.basename(input_path)}' is damaged or truncated."
            )

        # 3. Explicit unsupported format failure
        display_ext = ext if ext else "no extension"
        raise InvalidInputError(
            f"Unsupported file format '{display_ext}': The solver only accepts visual 3x3 grids (.png, .jpg, .webp) or audio recordings (.wav, .mp3, .ogg)."
        )


# Global singleton instance for easy import
router = RouterModel()


def classify(input_path: str) -> Dict[str, Any]:
    """Convenience function wrapping the RouterModel classify method."""
    return router.classify(input_path)
