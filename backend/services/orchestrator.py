"""Runs all six agents on one image and returns ONE traceable result (shape = what the frontend expects)."""
import time
import uuid
from typing import Optional

import numpy as np

from agents.context_agent import assess_context
from agents.coordinator_agent import coordinate
from agents.diagnosis_agent import predict_lesion
from agents.lesion_agent import analyze_lesion
from agents.quality_agent import check_image_quality
from agents.safety_agent import review_safety
from config import DISCLAIMER
from utils.image_processing import to_bgr


def to_py(o):
    if isinstance(o, dict):
        return {str(k): to_py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_py(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def decide(a1, a2, a3, a4, policy=None):
    """A5 + A6 only (used by tuning scripts that replay stored A1-A4 outputs)."""
    a5 = review_safety(a1, a2, a3, a4, policy)
    return a5, coordinate(a1, a2, a3, a4, a5, policy)


def assemble(image_id, a1, a2, a3, a4, a5, a6, latency=None) -> dict:
    return to_py({
        "success": True, "image_id": image_id, "source": "live",
        "quality": a1, "diagnosis": a2, "lesionAnalysis": a3, "context": a4, "safety": a5,
        "coordinator": a6, "triage": a6,
        "final": {"prediction": a6["predictedLabel"], "decision": a6["decision"]},
        "latency_ms": latency or {}, "disclaimer": DISCLAIMER,
    })


def analyze(image, image_id: Optional[str] = None, context: Optional[dict] = None,
            policy: Optional[dict] = None, diagnosis_fn=predict_lesion) -> dict:
    image_id = image_id or uuid.uuid4().hex[:12]
    bgr, lat, t = to_bgr(image), {}, time.perf_counter()

    def step(name, fn, *a):
        nonlocal t
        out = fn(*a)
        now = time.perf_counter()
        lat[name] = round((now - t) * 1000, 1)
        t = now
        return out

    a1 = step("A1_quality", check_image_quality, bgr)
    a2 = step("A2_diagnosis", diagnosis_fn, bgr)          # always run: every image needs a prediction
    a3 = step("A3_lesion", analyze_lesion, bgr, a1)
    a4 = step("A4_context", assess_context, context)
    a5 = step("A5_safety", review_safety, a1, a2, a3, a4, policy)
    a6 = step("A6_coordinator", coordinate, a1, a2, a3, a4, a5, policy)
    lat["total"] = round(sum(lat.values()), 1)
    return assemble(image_id, a1, a2, a3, a4, a5, a6, lat)
