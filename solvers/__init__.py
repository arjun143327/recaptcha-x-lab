"""Solvers package for Multi-Modal reCAPTCHA Solver (Audio & Visual).

Exports:
  - Protocol & Errors: CaptchaSolver, SolverError, InvalidInputError, ModelLoadError
  - Router: RouterModel, router, classify
  - Specialists: AudioSolver, VisualSolver
  - Registry & Pipeline: SOLVERS, route_and_solve
"""

import os
import warnings

# Disable TensorFlow probing & background DLL conflicts on Windows
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"

warnings.filterwarnings("ignore", category=FutureWarning)

from solvers.base import CaptchaSolver, SolverError, InvalidInputError, ModelLoadError
from solvers.router import RouterModel, router, classify
from solvers.audio import AudioSolver, levenshtein_distance, compute_string_accuracy
from solvers.visual import VisualSolver
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
    "SOLVERS",
    "route_and_solve",
    "levenshtein_distance",
    "compute_string_accuracy",
]
