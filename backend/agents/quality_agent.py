"""Agent 1 - Image Quality Agent (pure OpenCV, no training needed).

Contract:  check_image_quality(image) -> dict (see schemas.response.QualityResult)
Status:    ACCEPTABLE -> proceed | MARGINAL -> proceed but decision engine is stricter | POOR -> RE_IMAGE
"""
import cv2
import numpy as np

from config import load_quality_thresholds
from utils.image_processing import InvalidImageError, to_bgr

_WORK_WIDTH = 512  # normalise resolution so thresholds are comparable across images


def compute_metrics(image) -> dict:
    bgr = to_bgr(image)
    h, w = bgr.shape[:2]
    scale = _WORK_WIDTH / float(w)
    small = cv2.resize(bgr, (_WORK_WIDTH, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    # Blur: variance of Laplacian (low => few sharp edges)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Illumination
    brightness = float(gray.mean())
    contrast = float(gray.std())

    # Glare: fraction of near-saturated pixels (specular highlights)
    glare = float((gray >= 245).mean())

    # Hair / thin-object obstruction: black-hat morphology highlights dark thin structures
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    hair = float((blackhat > 20).mean())

    # Large occlusion (finger, cap, ruler): featureless blocks on an 8x8 grid
    gh, gw = gray.shape[0] // 8, gray.shape[1] // 8
    flat = 0
    for i in range(8):
        for j in range(8):
            block = gray[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
            if block.std() < 3.0 and (block.mean() < 25 or block.mean() > 235):
                flat += 1
    occlusion = flat / 64.0

    return {
        "blur_score": blur, "brightness": brightness, "contrast": contrast,
        "glare_ratio": glare, "hair_ratio": hair, "occlusion_ratio": occlusion,
        "width": float(w), "height": float(h),
    }


def check_image_quality(image) -> dict:
    t = load_quality_thresholds()
    try:
        m = compute_metrics(image)
    except InvalidImageError:
        return {"agent": "image_quality", "status": "POOR", "score": 0.0,
                "checks": {"decode": "FAIL"}, "metrics": {}, "reasons": ["Image could not be read"]}

    checks, reasons, sub = {}, [], {}

    if min(m["width"], m["height"]) < t["min_side_px"]:
        checks["resolution"] = "FAIL"; sub["resolution"] = 0.0
        reasons.append(f"Resolution too low ({int(m['width'])}x{int(m['height'])}px)")
    else:
        checks["resolution"] = "PASS"; sub["resolution"] = 1.0

    # Blur
    if m["blur_score"] < t["blur_min"]:
        checks["blur"] = "FAIL"; sub["blur"] = 0.0
        reasons.append(f"Image is blurry (sharpness {m['blur_score']:.1f} < {t['blur_min']:.1f})")
    elif m["blur_score"] < t["blur_marginal"]:
        checks["blur"] = "WARN"; sub["blur"] = 0.6
        reasons.append(f"Image is slightly soft (sharpness {m['blur_score']:.1f})")
    else:
        checks["blur"] = "PASS"; sub["blur"] = 1.0

    # Illumination
    if m["brightness"] < t["brightness_min"]:
        checks["brightness"] = "FAIL"; sub["brightness"] = 0.0
        reasons.append(f"Image is too dark (mean intensity {m['brightness']:.0f})")
    elif m["brightness"] > t["brightness_max"]:
        checks["brightness"] = "FAIL"; sub["brightness"] = 0.0
        reasons.append(f"Image is overexposed (mean intensity {m['brightness']:.0f})")
    else:
        checks["brightness"] = "PASS"; sub["brightness"] = 1.0

    if m["contrast"] < t["contrast_min"]:
        checks["contrast"] = "WARN"; sub["contrast"] = 0.6
        reasons.append(f"Low contrast (std {m['contrast']:.1f}); lighting may be flat")
    else:
        checks["contrast"] = "PASS"; sub["contrast"] = 1.0

    # Glare
    if m["glare_ratio"] > t["glare_max"]:
        checks["glare"] = "FAIL"; sub["glare"] = 0.0
        reasons.append(f"Strong glare ({m['glare_ratio'] * 100:.1f}% saturated pixels)")
    elif m["glare_ratio"] > t["glare_marginal"]:
        checks["glare"] = "WARN"; sub["glare"] = 0.6
        reasons.append(f"Some glare ({m['glare_ratio'] * 100:.1f}% saturated pixels)")
    else:
        checks["glare"] = "PASS"; sub["glare"] = 1.0

    # Obstruction
    if m["occlusion_ratio"] > t["occlusion_max"]:
        checks["obstruction"] = "FAIL"; sub["obstruction"] = 0.0
        reasons.append("Large part of the frame is blocked or featureless")
    elif m["hair_ratio"] > t["hair_max"]:
        checks["obstruction"] = "WARN"; sub["obstruction"] = 0.6
        reasons.append(f"Heavy hair/thin-object coverage ({m['hair_ratio'] * 100:.1f}% of image)")
    else:
        checks["obstruction"] = "PASS"; sub["obstruction"] = 1.0

    score = float(np.mean(list(sub.values())))
    if "FAIL" in checks.values():
        status = "POOR"
    elif "WARN" in checks.values():
        status = "MARGINAL"
    else:
        status = "ACCEPTABLE"
        reasons.append("Sharpness, lighting, glare and obstruction checks passed")

    return {"agent": "image_quality", "status": status, "score": round(score, 3),
            "checks": checks, "metrics": {k: round(v, 4) for k, v in m.items()}, "reasons": reasons}
