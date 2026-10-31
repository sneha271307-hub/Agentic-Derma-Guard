"""Central configuration. Every threshold used by the six agents lives here (or in the JSON override files)."""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# HAM10000 classes. ORDER MUST MATCH TRAINING (alphabetical).
CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_NAMES = {
    "akiec": "Actinic keratosis", "bcc": "Basal cell carcinoma", "bkl": "Benign keratosis",
    "df": "Dermatofibroma", "mel": "Melanoma", "nv": "Melanocytic nevus", "vasc": "Vascular lesion",
}
HIGH_RISK_CLASSES = {"mel", "bcc", "akiec"}

MODEL_PATH = Path(os.getenv("DERMAGUARD_MODEL_PATH", BASE_DIR.parent / "models" / "best_model.pth"))
MOCK_MODE = os.getenv("DERMAGUARD_MOCK", "0") == "1"
IMG_SIZE = 224
MAX_UPLOAD_MB = 15

# ---------------- A1 Image Quality thresholds (override with quality_thresholds.json) -------------------
DEFAULT_QUALITY_THRESHOLDS = {
    "blur_min": 40.0, "blur_marginal": 80.0,
    "brightness_min": 45.0, "brightness_max": 215.0, "contrast_min": 18.0,
    "glare_max": 0.04, "glare_marginal": 0.015,
    "hair_max": 0.12, "occlusion_max": 0.35, "min_side_px": 100,
    "min_score": 60,
}
QUALITY_THRESHOLD_FILE = BASE_DIR / "quality_thresholds.json"


def load_quality_thresholds() -> dict:
    t = dict(DEFAULT_QUALITY_THRESHOLDS)
    if QUALITY_THRESHOLD_FILE.exists():
        t.update(json.loads(QUALITY_THRESHOLD_FILE.read_text()))
    return t


# ---------------- A3 Lesion Analysis -------------------------------------------------------------------
LESION_CFG = {
    "asym_concern": 0.20, "border_concern": 0.45, "color_concern": 0.50,
    "suspicious_score": 45, "watch_score": 25,
    "min_area": 0.02, "max_area": 0.75, "border_touch_max": 0.30,
}

# ---------------- A4 Context ---------------------------------------------------------------------------
CONTEXT_CFG = {
    "age_high": 60,
    "sun_exposed": r"face|ear|scalp|neck|hand|arm|upper extremity|shoulder",
    "special_site": r"acral|palm|sole|foot|nail|genital",
}

# ---------------- A5 Safety + A6 Coordinator policy (override with policy.json via tune_policy.py) ------
POLICY_DEFAULTS = {
    "min_confidence": 0.75,            # below => REFER
    "min_confidence_marginal": 0.90,   # stricter when A1 only MARGINAL
    "mel_watch": 0.25,                 # P(mel) at/above => REFER
    "malignant_mass": 0.35,            # P(mel)+P(bcc)+P(akiec) at/above with benign top class => conflict
    "watch_confidence": 0.85,          # A3 WATCH/SUSPICIOUS/UNAVAILABLE needs at least this confidence to AUTO_TRIAGE
    "context_confidence": 0.90,        # context risk flag + benign top class needs at least this confidence
}
POLICY_FILE = BASE_DIR / "policy.json"


def load_policy(override: dict = None) -> dict:
    p = dict(POLICY_DEFAULTS)
    if POLICY_FILE.exists():
        p.update(json.loads(POLICY_FILE.read_text()))
    if override:
        p.update(override)
    return p


DISCLAIMER = ("Screening prototype only - not a medical diagnosis. AUTO_TRIAGE does not mean the lesion "
              "is harmless; consult a qualified clinician for any concern.")
