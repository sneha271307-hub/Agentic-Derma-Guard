"""Orchestrator: runs Quality -> Diagnosis -> Decision and returns one explainable result."""
import time
import uuid
from typing import Optional

from agents.diagnosis_agent import predict_lesion
from agents.quality_agent import check_image_quality
from config import DISCLAIMER
from services.decision_engine import make_decision


def analyze(image, image_id: Optional[str] = None, always_diagnose: bool = False,
            diagnosis_fn=predict_lesion) -> dict:
    """always_diagnose=True runs the diagnosis agent even on POOR images (used for validation metrics).
    The final decision is still RE_IMAGE for POOR images."""
    image_id = image_id or uuid.uuid4().hex[:12]
    lat = {}

    t0 = time.perf_counter()
    quality = check_image_quality(image)
    lat["quality"] = round((time.perf_counter() - t0) * 1000, 1)

    diagnosis = None
    if quality["status"] != "POOR" or always_diagnose:
        try:
            t1 = time.perf_counter()
            diagnosis = diagnosis_fn(image)
            lat["diagnosis"] = round((time.perf_counter() - t1) * 1000, 1)
        except Exception:
            if quality["status"] != "POOR":
                raise

    decision = make_decision(quality, diagnosis)
    lat["total"] = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "success": True, "image_id": image_id, "quality": quality, "diagnosis": diagnosis,
        "decision": decision, "final_decision": decision["decision"],
        "reasons": decision["reasons"], "latency_ms": lat, "disclaimer": DISCLAIMER,
    }
