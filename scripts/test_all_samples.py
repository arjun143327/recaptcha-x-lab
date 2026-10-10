"""Test all 20 visual and 20 audio real benchmark challenges.

Measures:
1. Router classification accuracy & confidence
2. Specialist solver performance:
   - Visual: Cell-level accuracy, exact grid match, predicted vs ground truth cells
   - Audio: Exact string match, Normalized CER, predicted vs ground truth transcript
3. Latency per sample
"""

import os
import sys
import json
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from solvers.pipeline import preload_models, route_and_solve


def run_visual_benchmark():
    gt_path = os.path.join(BASE_DIR, "data", "visual", "ground_truth.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_all = json.load(f)

    real_visual_keys = [k for k, v in gt_all.items() if v.get("is_real_recaptcha")]
    print(f"\n==================================================")
    print(f"Testing {len(real_visual_keys)} Real Visual reCAPTCHA Challenges")
    print(f"==================================================")

    results = []
    total_cells = 0
    correct_cells = 0
    exact_grid_matches = 0
    router_correct = 0

    for idx, filename in enumerate(sorted(real_visual_keys), start=1):
        info = gt_all[filename]
        filepath = os.path.join(BASE_DIR, "data", "visual", filename)
        prompt = info["prompt"]
        target_cells = sorted(info["target_cells"])

        t0 = time.time()
        res = route_and_solve(filepath, prompt=prompt)
        dt = time.time() - t0

        predicted_type = res["predicted_type"]
        is_router_ok = (predicted_type == "visual")
        if is_router_ok:
            router_correct += 1

        pred_cells = sorted(res["answer"])
        is_exact = (pred_cells == target_cells)
        if is_exact:
            exact_grid_matches += 1

        # Cell accuracy: out of 9 cells
        target_set = set(target_cells)
        pred_set = set(pred_cells)
        cell_acc_count = sum(1 for c in range(9) if (c in target_set) == (c in pred_set))
        total_cells += 9
        correct_cells += cell_acc_count

        res_item = {
            "index": idx,
            "filename": filename,
            "prompt": prompt,
            "ground_truth": target_cells,
            "predicted": pred_cells,
            "exact_match": is_exact,
            "cell_accuracy": f"{cell_acc_count}/9 ({cell_acc_count/9*100:.1f}%)",
            "router_type": predicted_type,
            "router_conf": round(res["router_confidence"], 2),
            "specialist_conf": round(res["specialist_confidence"], 2),
            "latency_sec": round(dt, 2),
        }
        results.append(res_item)
        print(f"[{idx:02d}/20] {filename:<40} | Prompt: {prompt:<14} | GT: {str(target_cells):<14} | Pred: {str(pred_cells):<14} | Match: {'PASS' if is_exact else 'PARTIAL'} ({cell_acc_count}/9) | {dt:.2f}s")

    summary = {
        "total_samples": len(real_visual_keys),
        "router_accuracy": f"{router_correct}/{len(real_visual_keys)} ({router_correct/len(real_visual_keys)*100:.1f}%)",
        "exact_grid_matches": f"{exact_grid_matches}/{len(real_visual_keys)} ({exact_grid_matches/len(real_visual_keys)*100:.1f}%)",
        "cell_accuracy": f"{correct_cells}/{total_cells} ({correct_cells/total_cells*100:.1f}%)",
    }
    print("\nVisual Summary:", summary)
    return results, summary


def run_audio_benchmark():
    gt_path = os.path.join(BASE_DIR, "data", "audio", "ground_truth.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_all = json.load(f)

    real_audio_keys = [k for k, v in gt_all.items() if v.get("is_real_audio")]
    print(f"\n==================================================")
    print(f"Testing {len(real_audio_keys)} Real Audio SecurImage Challenges")
    print(f"==================================================")

    results = []
    exact_matches = 0
    router_correct = 0
    total_chars = 0
    char_matches = 0

    for idx, filename in enumerate(sorted(real_audio_keys), start=1):
        info = gt_all[filename]
        filepath = os.path.join(BASE_DIR, "data", "audio", filename)
        gt_code = str(info["ground_truth"]).strip().lower()

        t0 = time.time()
        res = route_and_solve(filepath)
        dt = time.time() - t0

        predicted_type = res["predicted_type"]
        is_router_ok = (predicted_type == "audio")
        if is_router_ok:
            router_correct += 1

        pred_code = str(res["answer"]).strip().lower()
        is_exact = (pred_code == gt_code)
        if is_exact:
            exact_matches += 1

        # Character match calculation
        match_c = sum(1 for a, b in zip(pred_code, gt_code) if a == b)
        total_chars += len(gt_code)
        char_matches += match_c

        split = info.get("split", "unknown")

        res_item = {
            "index": idx,
            "filename": filename,
            "split": split,
            "ground_truth": gt_code,
            "predicted": pred_code,
            "exact_match": is_exact,
            "char_match": f"{match_c}/{len(gt_code)}",
            "router_type": predicted_type,
            "router_conf": round(res["router_confidence"], 2),
            "specialist_conf": round(res["specialist_confidence"], 2),
            "latency_sec": round(dt, 2),
        }
        results.append(res_item)
        print(f"[{idx:02d}/20] {filename:<26} | Split: {split:<13} | GT: {gt_code:<6} | Pred: {pred_code:<6} | Match: {'PASS' if is_exact else 'FAIL'} | {dt:.2f}s")

    summary = {
        "total_samples": len(real_audio_keys),
        "router_accuracy": f"{router_correct}/{len(real_audio_keys)} ({router_correct/len(real_audio_keys)*100:.1f}%)",
        "exact_word_matches": f"{exact_matches}/{len(real_audio_keys)} ({exact_matches/len(real_audio_keys)*100:.1f}%)",
        "character_accuracy": f"{char_matches}/{total_chars} ({char_matches/total_chars*100:.1f}%)",
    }
    print("\nAudio Summary:", summary)
    return results, summary


def main():
    print("Preloading models...")
    preload_models()
    
    vis_res, vis_sum = run_visual_benchmark()
    aud_res, aud_sum = run_audio_benchmark()

    output_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "visual_summary": vis_sum,
        "visual_results": vis_res,
        "audio_summary": aud_sum,
        "audio_results": aud_res,
    }

    report_path = os.path.join(BASE_DIR, "test_results_20_samples.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(output_report, f, indent=2)

    print(f"\nSaved full results report to {report_path}")


if __name__ == "__main__":
    main()
