"""Shared interface and protocols for reCAPTCHA specialist solvers.

Defined in ARCHITECTURE.md and AGENTS.md.
Every specialist model (Audio, Visual, Puzzle) implements the CaptchaSolver protocol.
"""

from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable


class SolverError(Exception):
    """Base exception for solver errors."""
    pass


class InvalidInputError(SolverError):
    """Raised when the input path or file content is invalid for the solver."""
    pass


class ModelLoadError(SolverError):
    """Raised when model weights or dependencies fail to load."""
    pass


@runtime_checkable
class CaptchaSolver(Protocol):
    """Common protocol for all CAPTCHA specialist solvers.
    
    Each specialist solver must implement solve() taking an input file path
    and returning a dictionary containing at least 'answer' and 'confidence'.
    """

    def solve(self, input_path: str, **kwargs: Any) -> Dict[str, Any]:
        """Solve a single CAPTCHA challenge instance.
        
        Args:
            input_path: Path to the CAPTCHA file (image, audio, etc.).
            **kwargs: Modality-specific optional parameters 
                      (e.g., prompt='traffic light' for visual solver).
                      
        Returns:
            Dict containing:
                - answer: The solution (e.g. list of indices for visual, 
                          transcribed string for audio, float offset for puzzle).
                - confidence: Float confidence score between 0.0 and 1.0.
                - details: Optional dictionary with additional debug/visualization data.
        """
        ...
