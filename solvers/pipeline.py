"""Pipeline and Result Aggregator wiring Router to Audio and Visual specialist models.

Defined in ARCHITECTURE.md:
  1. Input CAPTCHA
  2. Router Model (binary modality classifier: audio vs visual)
  3. Dispatches to matching specialist (Visual or Audio)
  4. Aggregates and returns standardized result dictionary
"""

import os
from typing import Any, Dict, Optional

from solvers.base import CaptchaSolver, InvalidInputError
from solvers.router import RouterModel, router
from solvers.audio import AudioSolver
from solvers.visual import VisualSolver


# Registry of specialist solvers (initialized as persistent singletons)
SOLVERS: Dict[str, CaptchaSolver] = {
    "visual": VisualSolver(lazy_load=True),
    "audio": AudioSolver(lazy_load=True),
}


def preload_models() -> Dict[str, bool]:
    """Load model weights for all registered specialist solvers ONCE at application startup.
    
    Ensures zero cold-start delay during interactive evaluation and prevents reloading per-request.
    """
    statuses = {}
    for name, solver in SOLVERS.items():
        if hasattr(solver, "_ensure_model_loaded"):
            statuses[name] = solver._ensure_model_loaded()
    return statuses


def route_and_solve(
    input_path: str,
    prompt: Optional[str] = None,
    router_instance: Optional[RouterModel] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Classify incoming CAPTCHA challenge and solve it using the matching specialist.
    
    Args:
        input_path: Path to CAPTCHA challenge file (audio or visual image grid).
        prompt: Optional query object prompt for visual solver (defaults to 'traffic light').
        router_instance: Optional custom RouterModel instance.
        **kwargs: Modality-specific keyword arguments passed to specialist solvers.
        
    Returns:
        Standardized aggregated response:
          - predicted_type: 'audio' | 'visual'
          - router_confidence: float (0.0 to 1.0)
          - specialist_used: name of the solver invoked ('audio' or 'visual')
          - answer: specialist solution (cell indices or transcribed string)
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
