"""Run:  python tests/test_core.py   (no pytest / torch / fastapi needed)"""
import os
import sys
from pathlib import Path

os.environ["DERMAGUARD_MOCK"] = "1"
os.environ["DERMAGUARD_MODEL_PATH"] = "/nonexistent/model.pth"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2           # noqa: E402
import numpy as np   # noqa: E402

from agents.context_agent import assess_context            # noqa: E402
from agents.lesion_agent import analyze_lesion              # noqa: E402
from agents.quality_agent import check_image_quality        # noqa: E402
from config import CLASSES, HIGH_RISK_CLASSES                # noqa: E402
from services.orchestrator import analyze, decide            # noqa: E402


def skin(seed=0):
    rng = np.random.RandomState(seed)
    img = np.full((450, 600, 3), (150, 170, 205), np.uint8)
    img = cv2.add(img, rng.randint(0, 25, img.shape, dtype=np.uint8))
    cv2.ellipse(img, (300, 225), (130, 100), 20, 0, 360, (40, 60, 110), -1)
    cv2.ellipse(img, (330, 240), (45, 35), 0, 0, 360, (20, 25, 50), -1)
    img = img.astype(np.int16) + rng.randint(-14, 14, img.shape)     # sharp sensor-like texture
    return np.clip(img, 0, 255).astype(np.uint8)


def probs(cls, conf):
    p = {c: (1 - conf) / 6 for c in CLASSES}
    p[cls] = conf
    return {"predicted_class": cls, "predicted_name": cls, "confidence": conf, "probabilities": p,
            "malignant_probability": sum(p[c] for c in HIGH_RISK_CLASSES)}


def test_quality():
    q = check_image_quality(skin())
    assert q["status"] == "GOOD" and isinstance(q["checks"], list) and 0 <= q["score"] <= 100
    assert check_image_quality(cv2.GaussianBlur(skin(), (51, 51), 0))["status"] == "POOR"
    assert check_image_quality(np.full((450, 600, 3), 10, np.uint8))["status"] == "POOR"
    glare = skin(); glare[:170, :250] = 255
    assert check_image_quality(glare)["status"] == "POOR"
    assert check_image_quality(b"not an image")["status"] == "POOR"


def test_lesion_context():
    a3 = analyze_lesion(skin(), check_image_quality(skin()))
    assert a3["suspicion"] in ("LOW_CUE_BURDEN", "WATCH", "SUSPICIOUS", "UNAVAILABLE") and len(a3["featureEvidence"]) == 3
    assert analyze_lesion(np.full((300, 300, 3), 170, np.uint8))["suspicion"] == "UNAVAILABLE"
    c = assess_context({"age": "", "gender": "", "location": ""})
    assert len(c["missingFields"]) == 3 and c["riskLevel"] == "NO_ADDED_FLAG"
    c = assess_context({"age": "67", "gender": "male", "location": "face"})
    assert c["riskLevel"] == "CONTEXT_FLAG" and not c["missingFields"]


def test_decisions():
    good = {"status": "GOOD", "grade": "ACCEPTABLE", "score": 90, "reasons": [], "metrics": {}}
    marg = {**good, "grade": "MARGINAL"}
    poor = {"status": "POOR", "grade": "POOR", "score": 40, "reasons": ["blurry"], "metrics": {}}
    low = {"suspicion": "LOW_CUE_BURDEN", "suspicionScore": 5, "reliabilityFlags": []}
    sus = {"suspicion": "SUSPICIOUS", "suspicionScore": 70, "reliabilityFlags": []}
    ctx0 = assess_context({}); ctx_hi = assess_context({"age": "70", "location": "scalp", "gender": "male"})
    d = lambda q, dg, l, c: decide(q, dg, l, c)[1]["decision"]  # noqa: E731
    assert d(poor, probs("nv", 0.99), low, ctx0) == "RE_IMAGE"
    assert d(good, probs("mel", 0.95), low, ctx0) == "REFER"
    assert d(good, probs("nv", 0.60), low, ctx0) == "REFER"
    assert d(good, probs("nv", 0.95), low, ctx0) == "AUTO_TRIAGE"
    assert d(good, probs("nv", 0.95), sus, ctx0) == "REFER"        # A3 conflicts with A2
    assert d(good, probs("nv", 0.80), low, ctx0) == "AUTO_TRIAGE"
    assert d(marg, probs("nv", 0.80), low, ctx0) == "REFER"        # marginal image => stricter
    assert d(good, probs("nv", 0.85), low, ctx_hi) == "REFER"      # context risk + not confident enough


def test_end_to_end():
    r = analyze(skin(), context={"age": "50", "gender": "female", "location": "back"})
    for k in ("quality", "diagnosis", "lesionAnalysis", "context", "safety", "coordinator", "triage"):
        assert k in r, k
    assert r["final"]["decision"] in ("AUTO_TRIAGE", "REFER", "RE_IMAGE") and r["final"]["prediction"] in CLASSES
    import json
    json.dumps(r)   # must be JSON serialisable
    r2 = analyze(cv2.GaussianBlur(skin(), (51, 51), 0))
    assert r2["final"]["decision"] == "RE_IMAGE" and r2["diagnosis"]["predicted_class"] in CLASSES  # still has a prediction


if __name__ == "__main__":
    test_quality(); test_lesion_context(); test_decisions(); test_end_to_end(); print("all tests passed")
