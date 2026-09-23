"""Unit and integration smoke tests for the multi-modal reCAPTCHA pipeline.

Tests:
  1. CaptchaSolver protocol compliance for all specialist models.
  2. Router modality classification across real and synthetic files.
  3. Visual specialist solving real reCAPTCHA and synthetic 3x3 grids.
  4. Audio specialist transcription + Levenshtein distance on real & synthetic audio.
  5. Puzzle specialist offset detection on real Geetest slider and synthetic images.
  6. End-to-end route_and_solve pipeline execution across all modalities.
"""

import os
import unittest
from typing import Dict, Any

from solvers.base import CaptchaSolver, InvalidInputError
from solvers.router import RouterModel, classify
from solvers.visual import VisualSolver
from solvers.audio import AudioSolver, levenshtein_distance, compute_string_accuracy
from solvers.puzzle import PuzzleSolver
from solvers.pipeline import SOLVERS, route_and_solve


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


class TestPipeline(unittest.TestCase):
    """Integration and smoke tests for the complete pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.audio_file = os.path.join(DATA_DIR, "audio", "audio_sample_01.wav")
        cls.real_audio_file = os.path.join(DATA_DIR, "audio", "real_audio_017ddc45.wav")

        cls.visual_file = os.path.join(DATA_DIR, "visual", "visual_grid_01.png")
        cls.real_visual_file = os.path.join(DATA_DIR, "visual", "real_recaptcha_chimney.jpg")

        cls.puzzle_file = os.path.join(DATA_DIR, "puzzle", "puzzle_slider_01.png")
        cls.real_puzzle_file = os.path.join(DATA_DIR, "puzzle", "real_puzzle_geetest_01.png")

    def test_01_protocol_conformance(self):
        """Verify each specialist implements the CaptchaSolver protocol."""
        self.assertIsInstance(SOLVERS["visual"], CaptchaSolver)
        self.assertIsInstance(SOLVERS["audio"], CaptchaSolver)
        self.assertIsInstance(SOLVERS["puzzle"], CaptchaSolver)

    def test_02_router_modality_dispatch(self):
        """Verify the router correctly identifies all three modalities across real and synthetic samples."""
        router = RouterModel()
        res_a = router.classify(self.real_audio_file)
        res_v = router.classify(self.real_visual_file)
        res_p = router.classify(self.real_puzzle_file)

        self.assertEqual(res_a["type"], "audio")
        self.assertEqual(res_v["type"], "visual")
        self.assertEqual(res_p["type"], "puzzle")
        self.assertGreaterEqual(res_a["confidence"], 0.90)
        self.assertGreaterEqual(res_v["confidence"], 0.90)
        self.assertGreaterEqual(res_p["confidence"], 0.90)

    def test_03_visual_specialist_real_and_synthetic(self):
        """Verify visual solver on real reCAPTCHA grid and synthetic grid."""
        solver = SOLVERS["visual"]
        
        # 1. Test on real reCAPTCHA chimney image
        real_res = solver.solve(self.real_visual_file, prompt="chimney")
        self.assertEqual(real_res["modality"], "visual")
        self.assertIn("answer", real_res)
        self.assertEqual(real_res["answer"], [1, 5, 8])

        # 2. Test on synthetic grid
        synth_res = solver.solve(self.visual_file, prompt="traffic light")
        self.assertEqual(synth_res["answer"], [0, 4, 8])

    def test_04_audio_specialist_with_levenshtein(self):
        """Verify audio solver transcribes audio and computes real Levenshtein distance."""
        solver = AudioSolver()
        
        # Test clean sample (expects high character accuracy)
        synth_res = solver.solve(self.audio_file)
        synth_metrics = compute_string_accuracy(synth_res["answer"], "72941")
        self.assertGreaterEqual(synth_metrics["character_accuracy"], 0.8)

        # Test real SecurImage sample (transcribes distorted audio)
        real_res = solver.solve(self.real_audio_file)
        self.assertIn("answer", real_res)
        self.assertIsInstance(real_res["answer"], str)
        self.assertIn("raw_transcript", real_res["details"])
        
        # Full fixtures evaluation report
        eval_summary = solver.evaluate_fixtures()
        self.assertGreaterEqual(eval_summary["num_samples"], 5)
        self.assertIn("mean_character_accuracy", eval_summary)
        self.assertIn("mean_character_error_rate", eval_summary)

    def test_05_puzzle_specialist_tolerance(self):
        """Verify puzzle solver computes offset on real Geetest and synthetic slider images."""
        solver = SOLVERS["puzzle"]

        # 1. Real Geetest challenge (expected notch at x=104px)
        real_res = solver.solve(self.real_puzzle_file)
        self.assertAlmostEqual(float(real_res["answer"]), 104.0, delta=5.0)

        # 2. Synthetic puzzle challenge (expected notch at x=185px)
        synth_res = solver.solve(self.puzzle_file)
        self.assertAlmostEqual(float(synth_res["answer"]), 185.0, delta=5.0)

        # Full fixtures evaluation
        eval_summary = solver.evaluate_fixtures()
        self.assertGreaterEqual(eval_summary["num_samples"], 20)
        self.assertIn("accuracy", eval_summary)
        self.assertIn("mean_pixel_error", eval_summary)
        self.assertGreater(eval_summary["accuracy"], 0.30)

    def test_06_end_to_end_route_and_solve_audio(self):
        """Test complete pipeline execution on audio challenge."""
        res = route_and_solve(self.real_audio_file)
        self.assertEqual(res["predicted_type"], "audio")
        self.assertEqual(res["specialist_used"], "audio")
        self.assertIn("answer", res)
        self.assertGreater(res["router_confidence"], 0.9)

    def test_07_end_to_end_route_and_solve_visual(self):
        """Test complete pipeline execution on real visual reCAPTCHA challenge."""
        res = route_and_solve(self.real_visual_file, prompt="chimney")
        self.assertEqual(res["predicted_type"], "visual")
        self.assertEqual(res["specialist_used"], "visual")
        self.assertEqual(res["answer"], [1, 5, 8])
        self.assertGreater(res["router_confidence"], 0.9)

    def test_08_end_to_end_route_and_solve_puzzle(self):
        """Test complete pipeline execution on real puzzle slider challenge."""
        res = route_and_solve(self.real_puzzle_file)
        self.assertEqual(res["predicted_type"], "puzzle")
        self.assertEqual(res["specialist_used"], "puzzle")
        self.assertAlmostEqual(float(res["answer"]), 104.0, delta=5.0)
        self.assertGreater(res["router_confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
