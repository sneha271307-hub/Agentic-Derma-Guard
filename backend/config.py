"""Central configuration. Every threshold used by the agents lives here so it can be justified."""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# HAM10000 classes. ORDER MUST MATCH TRAINING (alphabetical, same as sorted(set(labels))).
CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_NAMES = {
    "akiec": "Actinic keratoses / intraepithelial carcinoma",
    "bcc": "Basal cell carcinoma",
    "bkl": "Benign keratosis-like lesion",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic nevus",
    "vasc": "Vascular lesion",
}
# Classes treated as potentially malignant / pre-malignant -> always worth a clinician's look.
HIGH_RISK_CLASSES = {"mel", "bcc", "akiec"}

MODEL_PATH = Path(os.getenv("DERMAGUARD_MODEL_PATH", BASE_DIR.parent / "models" / "best_model.pth"))
MOCK_MODE = os.getenv("DERMAGUARD_MOCK", "0") == "1"
IMG_SIZE = 224
MAX_UPLOAD_MB = 10

# ---------------- Image-quality thresholds (defaults; overwritten by scripts/calibrate_quality.py) -----
DEFAULT_QUALITY_THRESHOLDS = {
    "blur_min": 40.0,          # Laplacian variance (on 512px-wide gray image) below this => blurry
    "blur_marginal": 80.0,     # below this => marginal
    "brightness_min": 45.0,    # mean gray intensity (0-255) below => too dark
    "brightness_max": 215.0,   # above => overexposed
    "contrast_min": 18.0,      # std of gray below => flat / washed out
    "glare_max": 0.04,         # fraction of near-white pixels above => glare
    "glare_marginal": 0.015,
    "hair_max": 0.12,          # fraction of hair-like (blackhat) pixels above => obstruction
    "occlusion_max": 0.35,     # fraction of featureless grid blocks above => obstructed
    "min_side_px": 100,        # smaller images are rejected
}
QUALITY_THRESHOLD_FILE = BASE_DIR / "quality_thresholds.json"


def load_quality_thresholds() -> dict:
    t = dict(DEFAULT_QUALITY_THRESHOLDS)
    if QUALITY_THRESHOLD_FILE.exists():
        t.update(json.loads(QUALITY_THRESHOLD_FILE.read_text()))
    return t


# ---------------- Decision policy (prototype, NOT clinically validated) --------------------------------
DECISION_POLICY = {
    "conf_threshold": 0.80,           # below => REFER
    "conf_threshold_marginal": 0.90,  # stricter when image quality is only MARGINAL
    "malignant_prob_threshold": 0.20, # P(mel)+P(bcc)+P(akiec) at/above => REFER
    "margin_threshold": 0.15,         # top1 - top2 below => ambiguous => REFER
}

DISCLAIMER = (
    "Screening prototype only - not a medical diagnosis. AUTO_TRIAGE does not mean the "
    "lesion is harmless; consult a qualified clinician for any concern."
)

SUBMIT_URL = os.getenv("SUBMIT_URL", "")
SUBMIT_TOKEN = os.getenv("SUBMIT_TOKEN", "")
TEAM_NAME = os.getenv("TEAM_NAME", "")
