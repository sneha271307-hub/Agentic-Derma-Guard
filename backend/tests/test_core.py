"""Run:  python tests/test_core.py   (no pytest or torch needed)"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.quality_agent import check_image_quality   # noqa: E402
from services.decision_engine import make_decision      # noqa: E402


def good_img():
    rng = np.random.RandomState(0)
    img = cv2.GaussianBlur(rng.randint(60, 200, (450, 600, 3), dtype=np.uint8), (3, 3), 0)
    cv2.circle(img, (300, 225), 120, (60, 70, 120), -1)
    return img


def test_quality():
    assert check_image_quality(good_img())["status"] in ("ACCEPTABLE", "MARGINAL")
    assert check_image_quality(cv2.GaussianBlur(good_img(), (51, 51), 0))["status"] == "POOR"   # blur
    assert check_image_quality(np.full((450, 600, 3), 10, np.uint8))["status"] == "POOR"        # dark
    glare = good_img(); glare[:150, :250] = 255
    assert check_image_quality(glare)["status"] == "POOR"                                       # glare
    assert check_image_quality(b"not an image")["status"] == "POOR"                             # corrupt


def diag(cls, conf, rest=None):
    from config import CLASSES, HIGH_RISK_CLASSES
    probs = {c: 0.0 for c in CLASSES}
    probs[cls] = conf
    other = [c for c in CLASSES if c != cls]
    for c in other:
        probs[c] = (1 - conf) / len(other)
    return {"predicted_class": cls, "predicted_name": cls, "confidence": conf, "probabilities": probs,
            "malignant_probability": sum(probs[c] for c in HIGH_RISK_CLASSES)}


def test_decisions():
    ok = {"status": "ACCEPTABLE", "reasons": []}
    marg = {"status": "MARGINAL", "reasons": []}
    poor = {"status": "POOR", "reasons": ["blurry"]}
    assert make_decision(poor, diag("nv", 0.99))["decision"] == "RE_IMAGE"
    assert make_decision(ok, diag("mel", 0.95))["decision"] == "REFER"
    assert make_decision(ok, diag("nv", 0.60))["decision"] == "REFER"
    assert make_decision(ok, diag("nv", 0.95))["decision"] == "AUTO_TRIAGE"
    assert make_decision(ok, diag("nv", 0.85))["decision"] == "AUTO_TRIAGE"
    assert make_decision(marg, diag("nv", 0.85))["decision"] == "REFER"   # quality tightens the bar
    assert make_decision(ok, None)["decision"] == "REFER"


if __name__ == "__main__":
    test_quality(); test_decisions(); print("all tests passed")
