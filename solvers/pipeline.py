"""Pipeline and Result Aggregator wiring Router to all 3 specialist models.

Defined in ARCHITECTURE.md:
  1. Input CAPTCHA
  2. Router Model (modality classifier)
  3. Dispatches to matching specialist (Visual, Audio, or Puzzle)
  4. Aggregates and returns standardized result dictionary
"""

import os
from typing import Any, Dict, Optional

from solvers.base import CaptchaSolver, InvalidInputError
from solvers.router import RouterModel, router
from solvers.audio import AudioSolver
from solvers.visual import VisualSolver
from solvers.puzzle import PuzzleSolver


# Registry of specialist solvers (initialized with lazy loading)
SOLVERS: Dict[str, CaptchaSolver] = {
    "visual": VisualSolver(lazy_load=True),
    "audio": AudioSolver(lazy_load=True),
    "puzzle": PuzzleSolver(),
}


def route_and_solve(
    input_path: str,
    prompt: Optional[str] = None,
    router_instance: Optional[RouterModel] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Classify incoming CAPTCHA challenge and solve it using the matching specialist.
    
    Args:
        input_path: Path to CAPTCHA challenge file (audio, image grid, or slider image).
        prompt: Optional query object prompt for visual solver (defaults to 'traffic light').
        router_instance: Optional custom RouterModel instance.
        **kwargs: Modality-specific keyword arguments passed to specialist solvers.
        
    Returns:
        Standardized aggregated response:
          - predicted_type: 'audio' | 'visual' | 'puzzle'
          - router_confidence: float (0.0 to 1.0)
          - specialist_used: name of the solver invoked
          - answer: specialist solution (cell indices, transcribed string, or pixel offset)
          - specialist_confidence: float (0.0 to 1.0)
          - details: specialist debug/visualization metadata
    """
    if not os.path.exists(input_path):
        raise InvalidInputError(f"Input CAPTCHA not found: {input_path}")

    clf_router = router_instance or router
    routing_result = clf_router.classify(input_path)
    predicted_type = routing_result["type"]
    router_conf = routing_result["confidence"]

    if predicted_type not in SOLVERS:
        raise InvalidInputError(f"Router classified unknown or unsupported type: {predicted_type}")

    specialist = SOLVERS[predicted_type]
    
    # Forward kwargs and prompt
    if predicted_type == "visual" and prompt is not None:
        kwargs["prompt"] = prompt

    solve_result = specialist.solve(input_path, **kwargs)

    return {
        "predicted_type": predicted_type,
        "router_confidence": router_conf,
        "specialist_used": predicted_type,
        "answer": solve_result["answer"],
        "specialist_confidence": solve_result["confidence"],
        "details": solve_result.get("details", {}),
        "router_meta": routing_result.get("details", {})
    }
