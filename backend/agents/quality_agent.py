"""Agent 1 - Image Quality Agent (pure OpenCV, no training needed).

Output matches the frontend: score 0-100, status GOOD|POOR, checks = list of {key,label,pass,value,detail}.
Extra: grade = ACCEPTABLE | MARGINAL | POOR (MARGINAL makes the Safety agent stricter).
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
        return {"agent": "image_quality", "status": "POOR", "grade": "POOR", "score": 0, "checks": [],
                "metrics": {}, "reasons": ["Image could not be read"]}

    items, reasons = [], []

    def add(key, label, level, value, detail):
        items.append({"key": key, "label": label, "level": level, "pass": level != "FAIL",
                      "value": value, "detail": detail})
        if level != "PASS":
            reasons.append(detail)

    if min(m["width"], m["height"]) < t["min_side_px"]:
        add("resolution", "Resolution", "FAIL", f"{int(m['width'])}x{int(m['height'])}px", "Resolution is too low.")

    b = m["blur_score"]
    if b < t["blur_min"]:
        add("blur", "Sharpness", "FAIL", f"{b:.0f} (needs {t['blur_min']:.0f}+)", "The photo is blurry. Hold steady and refocus.")
    elif b < t["blur_marginal"]:
        add("blur", "Sharpness", "WARN", f"{b:.0f}", "The photo is slightly soft.")
    else:
        add("blur", "Sharpness", "PASS", f"{b:.0f}", "Edges are crisp.")

    br = m["brightness"]
    if br < t["brightness_min"]:
        add("light", "Lighting", "FAIL", f"{br:.0f} of 255", "The photo is too dark.")
    elif br > t["brightness_max"]:
        add("light", "Lighting", "FAIL", f"{br:.0f} of 255", "The photo is overexposed.")
    elif m["contrast"] < t["contrast_min"]:
        add("light", "Lighting", "WARN", f"{br:.0f} of 255", "Low contrast; lighting may be flat.")
    else:
        add("light", "Lighting", "PASS", f"{br:.0f} of 255", "Even brightness.")

    g = m["glare_ratio"]
    if g > t["glare_max"]:
        add("glare", "Glare", "FAIL", f"{g * 100:.1f}% bright spots", "Reflections hide detail. Tilt the camera or use polarized light.")
    elif g > t["glare_marginal"]:
        add("glare", "Glare", "WARN", f"{g * 100:.1f}% bright spots", "Some glare on the skin.")
    else:
        add("glare", "Glare", "PASS", f"{g * 100:.1f}% bright spots", "No reflections on the skin.")

    if m["occlusion_ratio"] > t["occlusion_max"]:
        add("obstruction", "Obstruction", "FAIL", f"{m['occlusion_ratio'] * 100:.0f}% blocked", "A large part of the frame is blocked or featureless.")
    elif m["hair_ratio"] > t["hair_max"]:
        add("obstruction", "Obstruction", "WARN", f"{m['hair_ratio'] * 100:.1f}% hair-like", "Heavy hair or thin objects cross the lesion.")
    else:
        add("obstruction", "Obstruction", "PASS", f"{m['hair_ratio'] * 100:.1f}% hair-like", "The lesion is clearly visible.")

    sub = {"PASS": 1.0, "WARN": 0.6, "FAIL": 0.0}
    score = int(round(100 * float(np.mean([sub[i["level"]] for i in items]))))
    levels = {i["level"] for i in items}
    if "FAIL" in levels or score < t["min_score"]:
        grade, status = "POOR", "POOR"
        if "FAIL" not in levels:
            reasons.append("Overall image quality score is too low.")
    elif "WARN" in levels:
        grade, status = "MARGINAL", "GOOD"
    else:
        grade, status = "ACCEPTABLE", "GOOD"

    return {"agent": "image_quality", "status": status, "grade": grade, "score": score, "checks": items,
            "metrics": {k: round(float(v), 4) for k, v in m.items()}, "reasons": reasons}
