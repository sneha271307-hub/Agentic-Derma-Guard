"""Derive quality thresholds from the TRAINING images' own distribution (justifiable, data-driven).
Writes backend/quality_thresholds.json, which config.load_quality_thresholds() picks up.

  python scripts/calibrate_quality.py --train-dir /data/train --sample 1500
Rationale: HAM10000 images are curated, so the worst ~2-3% on each metric are treated as 'poor'.
"""
import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.quality_agent import compute_metrics   # noqa: E402
from config import QUALITY_THRESHOLD_FILE           # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-dir", required=True)
    ap.add_argument("--sample", type=int, default=1500)
    a = ap.parse_args()

    files = [p for p in Path(a.train_dir).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    random.seed(0)
    files = random.sample(files, min(a.sample, len(files)))
    M = [compute_metrics(p) for p in files]
    col = lambda k: np.array([m[k] for m in M])  # noqa: E731
    pct = lambda k, q: float(np.percentile(col(k), q))  # noqa: E731

    th = {
        "blur_min": round(pct("blur_score", 2), 2),
        "blur_marginal": round(pct("blur_score", 10), 2),
        "brightness_min": round(pct("brightness", 1), 1),
        "brightness_max": round(pct("brightness", 99.5), 1),
        "contrast_min": round(pct("contrast", 2), 1),
        "glare_marginal": round(max(pct("glare_ratio", 95), 0.005), 4),
        "glare_max": round(max(pct("glare_ratio", 99), 0.02), 4),
        "hair_max": round(pct("hair_ratio", 97), 4),
    }
    QUALITY_THRESHOLD_FILE.write_text(json.dumps(th, indent=2))
    print("Saved", QUALITY_THRESHOLD_FILE)
    print(json.dumps(th, indent=2))


if __name__ == "__main__":
    main()
