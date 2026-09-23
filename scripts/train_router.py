"""Train and evaluate the lightweight modality classifier.

Saves the fitted model to models/router/router_model.joblib.
Evaluates accuracy across audio, visual, and puzzle samples.
"""

import os
import glob
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib

import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from solvers.router import RouterModel, DEFAULT_ROUTER_MODEL_PATH
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "router")


def collect_dataset():
    """Extract features from data directory."""
    X = []
    y = []
    filepaths = []
    
    # 1. Visual samples
    visual_files = glob.glob(os.path.join(DATA_DIR, "visual", "*.png")) + glob.glob(os.path.join(DATA_DIR, "visual", "*.jpg"))
    for f in visual_files:
        feats, _ = RouterModel.extract_image_features(f)
        X.append(feats)
        y.append("visual")
        filepaths.append(f)
        
    # 2. Puzzle samples
    puzzle_files = glob.glob(os.path.join(DATA_DIR, "puzzle", "*.png"))
    for f in puzzle_files:
        feats, _ = RouterModel.extract_image_features(f)
        X.append(feats)
        y.append("puzzle")
        filepaths.append(f)
        
    return np.array(X), np.array(y), filepaths


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    X, y, files = collect_dataset()
    print(f"Collected {len(X)} image training samples ({sum(y == 'visual')} visual, {sum(y == 'puzzle')} puzzle).")
    
    # Fit simple regularized Logistic Regression classifier
    clf = LogisticRegression(C=1.0, random_state=42)
    clf.fit(X, y)
    
    preds = clf.predict(X)
    acc = accuracy_score(y, preds)
    print(f"Training accuracy on image modalities: {acc * 100:.1f}%")
    print("\nClassification Report:")
    print(classification_report(y, preds))
    
    # Save model
    joblib.dump(clf, DEFAULT_ROUTER_MODEL_PATH)
    print(f"Saved trained router model to {DEFAULT_ROUTER_MODEL_PATH}")
    
    # Verify overall end-to-end router accuracy on all files including audio
    print("\nTesting end-to-end RouterModel on all datasets...")
    router = RouterModel(DEFAULT_ROUTER_MODEL_PATH)
    
    all_tests = []
    # Audio
    for af in glob.glob(os.path.join(DATA_DIR, "audio", "*.wav")):
        all_tests.append((af, "audio"))
    # Visual
    for vf in glob.glob(os.path.join(DATA_DIR, "visual", "*.png")) + glob.glob(os.path.join(DATA_DIR, "visual", "*.jpg")):
        all_tests.append((vf, "visual"))
    # Puzzle
    for pf in glob.glob(os.path.join(DATA_DIR, "puzzle", "*.png")):
        all_tests.append((pf, "puzzle"))
        
    correct = 0
    for path, expected in all_tests:
        res = router.classify(path)
        is_corr = (res["type"] == expected)
        if is_corr:
            correct += 1
        print(f"[{'PASS' if is_corr else 'FAIL'}] {os.path.basename(path):<24} -> Predicted: {res['type']:<8} (Conf: {res['confidence']:.2f}, Expected: {expected})")
        
    total_acc = (correct / len(all_tests)) * 100
    print(f"\nRouter Overall Accuracy: {correct}/{len(all_tests)} ({total_acc:.1f}%)")
    assert total_acc >= 90.0, f"Router accuracy {total_acc}% is below 90% target!"
    print("Router meets definition of done (>90% accuracy).")


if __name__ == "__main__":
    main()
