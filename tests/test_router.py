"""Unit tests for the Router modality classifier component."""

import os
import unittest
import numpy as np

from solvers.router import RouterModel, classify
from solvers.base import InvalidInputError


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


class TestRouter(unittest.TestCase):
    """Test suite for RouterModel."""

    def setUp(self):
        self.router = RouterModel()

    def test_audio_classification(self):
        audio_path = os.path.join(DATA_DIR, "audio", "audio_sample_01.wav")
        res = self.router.classify(audio_path)
        self.assertEqual(res["type"], "audio")
        self.assertGreaterEqual(res["confidence"], 0.90)

    def test_visual_classification(self):
        visual_path = os.path.join(DATA_DIR, "visual", "visual_grid_01.png")
        res = self.router.classify(visual_path)
        self.assertEqual(res["type"], "visual")
        self.assertGreaterEqual(res["confidence"], 0.90)

    def test_puzzle_classification(self):
        puzzle_path = os.path.join(DATA_DIR, "puzzle", "puzzle_slider_01.png")
        res = self.router.classify(puzzle_path)
        self.assertEqual(res["type"], "puzzle")
        self.assertGreaterEqual(res["confidence"], 0.90)

    def test_invalid_file_raises_error(self):
        with self.assertRaises(InvalidInputError):
            self.router.classify("non_existent_file.xyz")

    def test_convenience_function(self):
        visual_path = os.path.join(DATA_DIR, "visual", "visual_grid_02.png")
        res = classify(visual_path)
        self.assertEqual(res["type"], "visual")


if __name__ == "__main__":
    unittest.main()
