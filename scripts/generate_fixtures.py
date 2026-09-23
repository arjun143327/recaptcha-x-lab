"""Stress-test Fixture Generator with deliberate difficulty controls.

Generates challenging synthetic CAPTCHA challenges with configurable degradation:
  - Audio: Additive background Gaussian noise, band-limited hum, amplitude clipping, tempo jitter.
  - Visual: Gaussian blur, contrast variation, speckle noise, partial object occlusion.
  - Puzzle: Multi-scale fractal landscape textures, lighting gradients, low-contrast notch shadows.

Usage:
  python scripts/generate_fixtures.py --difficulty hard
"""

import argparse
import json
import math
import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import win32com.client
from scipy.io import wavfile
import scipy.signal


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
VISUAL_DIR = os.path.join(DATA_DIR, "visual")
PUZZLE_DIR = os.path.join(DATA_DIR, "puzzle")


def ensure_dirs():
    for d in [AUDIO_DIR, VISUAL_DIR, PUZZLE_DIR]:
        os.makedirs(d, exist_ok=True)


# ==============================================================================
# 1. AUDIO DEGRADATION PIPELINE
# ==============================================================================

def add_audio_degradations(
    wav_path: str,
    snr_db: float = 12.0,
    speed_factor: float = 1.05,
    add_hum: bool = True
):
    """Applies realistic acoustic distortions, background noise, and tempo jitter."""
    sr, audio = wavfile.read(wav_path)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    max_amp = np.max(np.abs(audio))
    if max_amp > 0:
        audio = audio / max_amp

    # 1. Add background Gaussian white noise based on target SNR
    signal_power = np.mean(audio ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10.0))
    noise = np.random.normal(0, np.sqrt(max(noise_power, 1e-6)), len(audio)).astype(np.float32)

    # 2. Add low-frequency background hum (60 Hz + 120 Hz electrical ground loop hum typical in analog recordings)
    if add_hum:
        t = np.arange(len(audio)) / float(sr)
        hum = 0.08 * np.sin(2 * np.pi * 60 * t) + 0.04 * np.sin(2 * np.pi * 120 * t)
        noise = noise + hum.astype(np.float32)

    degraded = audio + noise

    # 3. Soft clipping / distortion
    degraded = np.tanh(degraded * 1.3)

    # 4. Resample slightly to simulate speed variation
    if speed_factor != 1.0:
        target_len = int(len(degraded) / speed_factor)
        degraded = scipy.signal.resample(degraded, target_len)

    # Normalize to 16-bit PCM
    degraded = degraded / (np.max(np.abs(degraded)) + 1e-6) * 0.9
    degraded_int16 = (degraded * 32767.0).astype(np.int16)
    wavfile.write(wav_path, sr, degraded_int16)


def generate_audio_fixtures(difficulty: str = "medium"):
    """Generates audio sample fixtures with spoken digits and applies distortion."""
    print(f"Generating audio fixtures (Difficulty: {difficulty})...")
    
    # Configure difficulty parameters
    snr_map = {"easy": 25.0, "medium": 14.0, "hard": 6.0}
    snr = snr_map.get(difficulty, 14.0)

    samples = [
        ("audio_sample_01.wav", "seven two nine four one", "72941"),
        ("audio_sample_02.wav", "three eight zero five six", "38056"),
        ("audio_sample_03.wav", "four one six nine two", "41692"),
        ("audio_sample_04.wav", "eight five two zero seven", "85207"),
        ("audio_sample_05.wav", "one nine three seven four", "19374"),
    ]

    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Rate = -1

    gt_path = os.path.join(AUDIO_DIR, "ground_truth.json")
    ground_truth = {}
    if os.path.exists(gt_path):
        try:
            with open(gt_path, "r", encoding="utf-8") as f:
                ground_truth = json.load(f)
        except Exception:
            ground_truth = {}

    for filename, text, clean_text in samples:
        filepath = os.path.join(AUDIO_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        filestream = win32com.client.Dispatch("SAPI.SpFileStream")
        filestream.Open(filepath, 3, False)
        speaker.AudioOutputStream = filestream
        speaker.Speak(text)
        filestream.Close()

        # Apply acoustic noise and distortion
        add_audio_degradations(filepath, snr_db=snr, speed_factor=1.04, add_hum=True)

        ground_truth[filename] = {
            "source": f"synthetic_degraded (SNR={snr}dB)",
            "spoken_text": text,
            "ground_truth": clean_text,
            "snr_db": snr,
            "difficulty": difficulty
        }

    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"Saved {len(samples)} degraded audio samples to {gt_path}")


# ==============================================================================
# 2. VISUAL DEGRADATION PIPELINE
# ==============================================================================

def apply_visual_degradations(img: Image.Image, blur_radius: float = 1.0, noise_amount: float = 0.08) -> Image.Image:
    """Applies camera blur, pixel noise, and contrast jitter."""
    # 1. Gaussian blur
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 2. Speckle noise
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, noise_amount * 255.0, arr.shape)
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(noisy_arr)

    # 3. Random contrast & brightness jitter
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(random.uniform(0.85, 1.2))
    b_enhancer = ImageEnhance.Brightness(img)
    img = b_enhancer.enhance(random.uniform(0.9, 1.1))

    return img


def draw_traffic_light(draw, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pole_w = int(w * 0.08)
    draw.rectangle([x0 + w // 2 - pole_w // 2, y0 + int(h * 0.6), x0 + w // 2 + pole_w // 2, y1], fill=(80, 80, 80))
    box_w, box_h = int(w * 0.36), int(h * 0.65)
    bx0 = x0 + (w - box_w) // 2
    by0 = y0 + int(h * 0.08)
    draw.rectangle([bx0, by0, bx0 + box_w, by0 + box_h], fill=(25, 25, 25), outline=(10, 10, 10), width=2)
    lamp_h = box_h // 3
    pad = int(lamp_h * 0.15)
    r = (min(box_w, lamp_h) - 2 * pad) // 2
    cx = bx0 + box_w // 2
    draw.ellipse([cx - r, by0 + lamp_h//2 - r, cx + r, by0 + lamp_h//2 + r], fill=(230, 40, 30))
    draw.ellipse([cx - r, by0 + lamp_h + lamp_h//2 - r, cx + r, by0 + lamp_h + lamp_h//2 + r], fill=(240, 200, 20))
    draw.ellipse([cx - r, by0 + 2*lamp_h + lamp_h//2 - r, cx + r, by0 + 2*lamp_h + lamp_h//2 + r], fill=(30, 200, 60))


def draw_crosswalk(draw, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle([x0, y0, x1, y1], fill=(55, 60, 65))
    num_stripes = 4
    stripe_w = int(w * 0.14)
    gap = (w - (num_stripes * stripe_w)) // (num_stripes + 1)
    for i in range(num_stripes):
        sx0 = x0 + gap + i * (stripe_w + gap)
        draw.rectangle([sx0, y0 + int(h * 0.2), sx0 + stripe_w, y0 + int(h * 0.8)], fill=(245, 245, 250))


def draw_tree(draw, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    tw = int(w * 0.12)
    draw.rectangle([x0 + w//2 - tw//2, y0 + int(h * 0.55), x0 + w//2 + tw//2, y1 - int(h * 0.05)], fill=(110, 65, 30))
    cx, cy, r = x0 + w // 2, y0 + int(h * 0.35), int(w * 0.35)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(34, 139, 34))


def draw_background_scene(draw, box, cell_idx):
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y0 + (y1 - y0) // 2], fill=(135, 206, 235))
    bw = (x1 - x0) // 3
    draw.rectangle([x0, y0 + (y1 - y0) // 4, x0 + bw, y1], fill=(140, 145, 150))
    draw.rectangle([x0 + bw, y0 + (y1 - y0) // 3, x1, y1], fill=(170, 165, 160))
    draw.rectangle([x0, y0 + 2 * (y1 - y0) // 3, x1, y1], fill=(70, 75, 80))


def generate_visual_fixtures(difficulty: str = "medium"):
    """Generates 3x3 grid fixtures with controlled noise and blur."""
    print(f"Generating visual fixtures (Difficulty: {difficulty})...")
    
    blur_map = {"easy": 0.5, "medium": 1.2, "hard": 2.5}
    noise_map = {"easy": 0.03, "medium": 0.08, "hard": 0.18}
    blur_r = blur_map.get(difficulty, 1.2)
    noise_amt = noise_map.get(difficulty, 0.08)

    grid_size = 300
    tile_size = 100

    samples = [
        {"filename": "visual_grid_01.png", "prompt": "traffic light", "target_cells": [0, 4, 8], "drawer": draw_traffic_light},
        {"filename": "visual_grid_02.png", "prompt": "traffic light", "target_cells": [1, 2, 7], "drawer": draw_traffic_light},
        {"filename": "visual_grid_03.png", "prompt": "crosswalk", "target_cells": [3, 4, 5], "drawer": draw_crosswalk},
        {"filename": "visual_grid_04.png", "prompt": "crosswalk", "target_cells": [0, 6], "drawer": draw_crosswalk},
        {"filename": "visual_grid_05.png", "prompt": "tree", "target_cells": [2, 5, 8], "drawer": draw_tree},
    ]

    gt_path = os.path.join(VISUAL_DIR, "ground_truth.json")
    ground_truth = {}
    if os.path.exists(gt_path):
        try:
            with open(gt_path, "r", encoding="utf-8") as f:
                ground_truth = json.load(f)
        except Exception:
            ground_truth = {}

    for sample in samples:
        img = Image.new("RGB", (grid_size, grid_size), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        target_cells = set(sample["target_cells"])
        drawer = sample["drawer"]

        for row in range(3):
            for col in range(3):
                idx = row * 3 + col
                x0, y0 = col * tile_size, row * tile_size
                box = [x0, y0, x0 + tile_size, y0 + tile_size]
                draw_background_scene(draw, box, idx)
                if idx in target_cells:
                    drawer(draw, box)

        # Draw grid lines
        for i in range(1, 3):
            draw.line([(i * tile_size, 0), (i * tile_size, grid_size)], fill=(210, 210, 210), width=2)
            draw.line([(0, i * tile_size), (grid_size, i * tile_size)], fill=(210, 210, 210), width=2)

        # Apply realistic degradation (blur + noise)
        img = apply_visual_degradations(img, blur_radius=blur_r, noise_amount=noise_amt)

        filepath = os.path.join(VISUAL_DIR, sample["filename"])
        img.save(filepath, "PNG")

        ground_truth[sample["filename"]] = {
            "source": f"synthetic_degraded (blur={blur_r}, noise={noise_amt})",
            "prompt": sample["prompt"],
            "target_cells": sample["target_cells"],
            "blur_radius": blur_r,
            "noise_amount": noise_amt,
            "difficulty": difficulty
        }

    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"Saved {len(samples)} visual grid samples to {gt_path}")


# ==============================================================================
# 3. PUZZLE DEGRADATION PIPELINE
# ==============================================================================

def generate_puzzle_fixtures(difficulty: str = "medium"):
    """Generates slider puzzle fixtures with complex textures and lighting gradients."""
    print(f"Generating puzzle fixtures (Difficulty: {difficulty})...")
    
    width = 400
    height = 200
    piece_size = 44

    samples = [
        {"filename": "puzzle_slider_01.png", "offset_x": 185, "y": 75},
        {"filename": "puzzle_slider_02.png", "offset_x": 240, "y": 60},
        {"filename": "puzzle_slider_03.png", "offset_x": 150, "y": 90},
        {"filename": "puzzle_slider_04.png", "offset_x": 280, "y": 70},
        {"filename": "puzzle_slider_05.png", "offset_x": 210, "y": 80},
    ]

    gt_path = os.path.join(PUZZLE_DIR, "ground_truth.json")
    ground_truth = {}
    if os.path.exists(gt_path):
        try:
            with open(gt_path, "r", encoding="utf-8") as f:
                ground_truth = json.load(f)
        except Exception:
            ground_truth = {}

    for idx, s in enumerate(samples):
        # Create non-linear textured background
        img = Image.new("RGB", (width, height))
        pixels = img.load()
        for y in range(height):
            for x in range(width):
                r = int(120 + 80 * math.sin(x * 0.02 + idx) + 30 * math.cos(y * 0.03))
                g = int(150 + 60 * math.cos(x * 0.015 - idx) + 20 * math.sin(y * 0.04))
                b = int(190 + 50 * math.sin((x + y) * 0.02))
                pixels[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 20, 140, 110], fill=(220, 210, 170), outline=(200, 190, 150))
        draw.polygon([(0, 160), (120, 90), (250, 180), (400, 100), (400, 200), (0, 200)], fill=(70, 110, 80))

        gx, gy = s["offset_x"], s["y"]
        pw, ph = piece_size, piece_size

        # In hard mode: lower contrast gap shadow + noise
        dark_factor = 0.55 if difficulty == "hard" else 0.35
        gap_box = [gx, gy, gx + pw, gy + ph]
        gap_patch = img.crop(gap_box)
        darkened = gap_patch.point(lambda p: int(p * dark_factor))
        img.paste(darkened, gap_box)

        draw.rectangle(gap_box, outline=(30, 30, 30), width=2)
        draw.line([(gx, gy), (gx + pw, gy)], fill=(200, 200, 200), width=1)
        draw.line([(gx, gy), (gx, gy + ph)], fill=(200, 200, 200), width=1)

        # Apply noise to puzzle image
        if difficulty in ["medium", "hard"]:
            img = apply_visual_degradations(img, blur_radius=0.6, noise_amount=0.04)

        filepath = os.path.join(PUZZLE_DIR, s["filename"])
        img.save(filepath, "PNG")

        ground_truth[s["filename"]] = {
            "source": f"synthetic_degraded (difficulty={difficulty})",
            "offset_x": s["offset_x"],
            "y": s["y"],
            "tolerance_px": 5.0,
            "difficulty": difficulty
        }

    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"Saved {len(samples)} puzzle slider samples to {gt_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate degraded stress-test fixtures")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium",
                        help="Level of noise, blur, and distortion to apply")
    args = parser.parse_args()

    ensure_dirs()
    generate_audio_fixtures(difficulty=args.difficulty)
    generate_visual_fixtures(difficulty=args.difficulty)
    generate_puzzle_fixtures(difficulty=args.difficulty)
    print("\nStress-test fixtures generated successfully!")


if __name__ == "__main__":
    main()
