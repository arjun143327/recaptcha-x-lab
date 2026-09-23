"""Solvers package for Multi-Modal reCAPTCHA Solver.

Exports:
  - Protocol & Errors: CaptchaSolver, SolverError, InvalidInputError, ModelLoadError
  - Router: RouterModel, router, classify
  - Specialists: AudioSolver, VisualSolver, PuzzleSolver
  - Registry & Pipeline: SOLVERS, route_and_solve
"""

from solvers.base import CaptchaSolver, SolverError, InvalidInputError, ModelLoadError
from solvers.router import RouterModel, router, classify
from solvers.audio import AudioSolver, levenshtein_distance, compute_string_accuracy
from solvers.visual import VisualSolver
from solvers.puzzle import PuzzleSolver
from solvers.pipeline import SOLVERS, route_and_solve

__all__ = [
    "CaptchaSolver",
    "SolverError",
    "InvalidInputError",
    "ModelLoadError",
    "RouterModel",
    "router",
    "classify",
    "AudioSolver",
    "VisualSolver",
    "PuzzleSolver",
    "SOLVERS",
    "route_and_solve",
    "levenshtein_distance",
    "compute_string_accuracy",
]
