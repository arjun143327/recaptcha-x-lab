"""CLI entry point for Multi-Modal reCAPTCHA Solver (Audio & Visual).

Usage:
  python main.py --input <path_to_file> [--prompt "traffic light"]
  python main.py --demo
  python main.py --test
"""

import argparse
import json
import os
import sys
import glob

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from solvers import route_and_solve, SOLVERS, router
from solvers.audio import AudioSolver
from solvers.visual import VisualSolver


def run_single(input_path: str, prompt: str = "traffic light"):
    print(f"\n==================================================")
    print(f"Input: {input_path}")
    print(f"Target Prompt (for visual): {prompt}")
    print(f"==================================================")
    
    result = route_and_solve(input_path, prompt=prompt)
    
    print(f"1. Router Classification : {result['predicted_type'].upper()} (Confidence: {result['router_confidence'] * 100:.1f}%)")
    print(f"2. Specialist Invoked    : {result['specialist_used'].upper()} Specialist")
    print(f"3. Specialist Confidence : {result['specialist_confidence'] * 100:.1f}%")
    print(f"4. Solved Answer         : {result['answer']}")
    print(f"5. Details               : {json.dumps(result['details'], indent=2)}")
    print(f"==================================================\n")
    return result


def run_demo():
    print("\n========================================================")
    print("      reCAPTCHA-X-LAB -- AUDIO & VISUAL PIPELINE DEMO     ")
    print("========================================================")
    
    samples = [
        # Audio: 1 clean synthetic, 1 real SecurImage
        ("data/audio/audio_sample_01.wav", None, "Audio Spoken Digits (Synthetic)"),
        ("data/audio/real_audio_017ddc45.wav", None, "Audio SecurImage Challenge (Real)"),
        # Visual: 1 synthetic grid, 2 real reCAPTCHA grids
        ("data/visual/visual_grid_01.png", "traffic light", "Visual 3x3 Grid (Synthetic)"),
        ("data/visual/real_recaptcha_chimney.jpg", "chimney", "Visual reCAPTCHA Chimneys (Real)"),
        ("data/visual/real_recaptcha_hydrant.jpg", "fire hydrant", "Visual reCAPTCHA Hydrant (Real)"),
    ]
    
    for rel_path, prompt, desc in samples:
        full_path = os.path.join(BASE_DIR, rel_path)
        if not os.path.exists(full_path):
            print(f"Skipping missing sample: {rel_path}")
            continue
            
        print(f"\n[DEMO] Processing: {desc} ({os.path.basename(full_path)})")
        run_single(full_path, prompt=prompt or "traffic light")


def run_eval_benchmarks():
    print("\n================================================================================")
    print("           reCAPTCHA-X-LAB -- ACCURACY BENCHMARK REPORT (AUDIO & VISUAL)          ")
    print("================================================================================")
    
    # 1. Router evaluation
    print("\n[1/3] Router Modality Classifier...")
    test_files = [
        *[(f, "audio") for f in glob.glob(os.path.join(BASE_DIR, "data", "audio", "*.wav"))],
        *[(f, "visual") for f in glob.glob(os.path.join(BASE_DIR, "data", "visual", "*.*")) if f.endswith(('.png', '.jpg'))],
    ]
    correct = 0
    real_correct = 0
    real_total = 0
    for path, expected in test_files:
        pred = router.classify(path)
        is_corr = (pred["type"] == expected)
        if is_corr:
            correct += 1
        if "real_" in os.path.basename(path):
            real_total += 1
            if is_corr:
                real_correct += 1

    total_acc = (correct / len(test_files)) * 100 if test_files else 0
    real_acc = (real_correct / real_total) * 100 if real_total else 0
    print(f"  Total Challenges Tested : {len(test_files)}")
    print(f"  Overall Accuracy        : {correct}/{len(test_files)} ({total_acc:.1f}%)")
    print(f"  Real-World Data Accuracy: {real_correct}/{real_total} ({real_acc:.1f}%)")

    # 2. Visual Specialist (CLIP Zero-Shot)
    print("\n[2/3] Visual Specialist (CLIP Zero-Shot Image Grid)...")
    visual_solver = VisualSolver()
    visual_summary = visual_solver.evaluate_fixtures()
    real_vis = [r for r in visual_summary["sample_results"] if r.get("is_real_recaptcha")]
    synth_vis = [r for r in visual_summary["sample_results"] if not r.get("is_real_recaptcha")]

    print(f"  Total Grids Tested      : {visual_summary['num_samples']} (Real: {len(real_vis)}, Synthetic: {len(synth_vis)})")
    print(f"  Mean Cell-Level Accuracy: {visual_summary['mean_cell_accuracy'] * 100:.1f}%")
    print(f"  Mean F1-Score           : {visual_summary['mean_f1_score']:.4f}")
    print(f"  Exact Grid Match Rate   : {visual_summary['exact_match_rate'] * 100:.1f}%")
    if real_vis:
        real_cell_acc = sum(r["cell_accuracy"] for r in real_vis) / len(real_vis) * 100
        real_f1 = sum(r["f1_score"] for r in real_vis) / len(real_vis)
        print(f"  --> Real reCAPTCHA Subset : Cell Acc: {real_cell_acc:.1f}%, F1: {real_f1:.4f}")

    # 3. Audio Specialist with Levenshtein Distance
    print("\n[3/3] Audio Specialist (Whisper ASR + Adaptive Noise Gating)...")
    audio_solver = AudioSolver()

    audio_summary = audio_solver.evaluate_fixtures()
    clean_real_aud = [r for r in audio_summary["sample_results"] if r.get("split") == "test_split"]
    heldout_aud = [r for r in audio_summary["sample_results"] if r.get("split") == "heldout_split"]
    synth_aud = [r for r in audio_summary["sample_results"] if not r.get("is_real_audio")]

    # Canonical evaluation set: 5 synthetic + 10 strictly held-out test_split (15 clean files total)
    clean_eval_samples = synth_aud + clean_real_aud
    clean_cer = sum(r["character_error_rate"] for r in clean_eval_samples) / len(clean_eval_samples) * 100 if clean_eval_samples else 0
    clean_acc = sum(r["character_accuracy"] for r in clean_eval_samples) / len(clean_eval_samples) * 100 if clean_eval_samples else 0
    clean_exact_cnt = sum(1 for r in clean_eval_samples if r["exact_match"])
    clean_exact_pct = (clean_exact_cnt / len(clean_eval_samples)) * 100 if clean_eval_samples else 0

    print(f"  Official Clean Test Files Tested: {len(clean_eval_samples)} (Real test_split: {len(clean_real_aud)}, Synthetic: {len(synth_aud)})")
    print(f"  Mean Character Accuracy         : {clean_acc:.1f}%")
    print(f"  Mean Character Error Rate (CER) : {clean_cer:.1f}%")
    print(f"  Clean Exact Match Rate          : {clean_exact_cnt}/{len(clean_eval_samples)} ({clean_exact_pct:.1f}%)")
    
    if clean_real_aud:
        real_cer = sum(r["character_error_rate"] for r in clean_real_aud) / len(clean_real_aud) * 100
        real_exact_cnt = sum(1 for r in clean_real_aud if r["exact_match"])
        real_exact_pct = (real_exact_cnt / len(clean_real_aud)) * 100
        print(f"  --> Real SecurImage Held-Out Set: {real_exact_cnt}/{len(clean_real_aud)} ({real_exact_pct:.1f}%), CER: {real_cer:.1f}%")
        print(f"      (Sole official real-world generalization metric; 0 train leakage)")
    
    if heldout_aud:
        print(f"  --> [Excluded Split] heldout_split: {len(heldout_aud)} files excluded (train-adjacent, not a valid generalization metric)")


    print("\n================================================================================")
    print("                         END OF BENCHMARK REPORT                                ")
    print("================================================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Multi-Modal reCAPTCHA Solver Pipeline (Audio & Visual)")
    parser.add_argument("--input", type=str, help="Path to CAPTCHA file to classify and solve")
    parser.add_argument("--prompt", type=str, default="traffic light", help="Prompt label for visual solver")
    parser.add_argument("--demo", action="store_true", help="Run end-to-end demo on sample files")
    parser.add_argument("--test", action="store_true", help="Run specialist accuracy benchmarks")
    
    args = parser.parse_args()
    
    if args.demo:
        run_demo()
    elif args.test:
        run_eval_benchmarks()
    elif args.input:
        run_single(args.input, prompt=args.prompt)
    else:
        run_demo()


if __name__ == "__main__":
    main()
