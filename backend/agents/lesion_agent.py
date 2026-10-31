"""A3 - Lesion Analysis Agent (OpenCV). Segments the lesion, then measures the visual cues dermatologists use:
asymmetry, border irregularity and color variation. Output: feature evidence, suspicion score, reliability flags.
These are explainable heuristics, NOT a clinical detector."""
import cv2
import numpy as np

from config import LESION_CFG as C
from utils.image_processing import to_bgr


def _segment(small):
    L = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)[:, :, 0]
    L = cv2.morphologyEx(L, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))  # drop hairs
    L = cv2.GaussianBlur(L, (7, 7), 0)
    _, m = cv2.threshold(L, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)                      # lesion = darker
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(m, connectivity=8)
    h, w = m.shape
    diag, best, best_sc = float(np.hypot(h, w)), None, -1.0
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 0.005 * h * w:
            continue
        d = np.hypot(cents[i][0] - w / 2, cents[i][1] - h / 2) / diag
        sc = area / (1 + 4 * d)                      # large AND near the centre
        if sc > best_sc:
            best, best_sc = i, sc
    if best is None:
        return None
    comp = (labels == best).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(comp)
    cv2.drawContours(filled, cnts, -1, 255, thickness=cv2.FILLED)
    return filled


def _asymmetry(mask):
    m = cv2.moments(mask, binaryImage=True)
    if m["m00"] < 10:
        return None
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    theta = 0.5 * np.arctan2(2 * m["mu11"], m["mu20"] - m["mu02"])
    size = int(2 * max(mask.shape))
    R = cv2.getRotationMatrix2D((cx, cy), float(np.degrees(theta)), 1.0)
    R[0, 2] += size / 2 - cx
    R[1, 2] += size / 2 - cy
    a = cv2.warpAffine(mask, R, (size, size), flags=cv2.INTER_NEAREST) > 0
    vals = []
    for f in (a[:, ::-1], a[::-1, :]):
        union = np.logical_or(a, f).sum()
        vals.append(np.logical_xor(a, f).sum() / union if union else 0.0)
    return float(np.mean(vals))


def _border(mask):
    sm = (cv2.GaussianBlur(mask, (9, 9), 0) > 127).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(sm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    area, per = cv2.contourArea(c), cv2.arcLength(c, True)
    if area < 20:
        return None
    harea = cv2.contourArea(cv2.convexHull(c))
    compact = per * per / (4 * np.pi * area)
    solidity = area / harea if harea else 1.0
    irr = 0.6 * np.clip((compact - 1.1) / 1.2, 0, 1) + 0.4 * np.clip((1 - solidity) / 0.2, 0, 1)
    return float(irr), float(compact), float(solidity)


def _color(small, mask):
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    sel = cv2.erode(mask, np.ones((5, 5), np.uint8)) > 0
    if sel.sum() < 50:
        sel = mask > 0
    px = lab[sel].astype(np.float32)
    if len(px) < 50:
        return None
    if len(px) > 3000:
        px = px[np.random.RandomState(0).choice(len(px), 3000, replace=False)]
    cv2.setRNGSeed(0)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, lbl, cen = cv2.kmeans(px, 3, None, crit, 1, cv2.KMEANS_PP_CENTERS)
    shares = np.bincount(lbl.ravel(), minlength=3) / len(px)
    keep = [i for i in range(3) if shares[i] >= 0.08]
    dist = max([float(np.linalg.norm(cen[i] - cen[j])) for i in keep for j in keep if i < j] or [0.0])
    return float(np.clip((dist - 12) / 28, 0, 1)), dist, len(keep)


def _unavailable(flags):
    cue = lambda k, l: {"key": k, "label": l, "value": "Unavailable", "detail": "Lesion region not isolated reliably.", "concern": False}  # noqa: E731
    cues = [cue("asymmetry", "Asymmetry"), cue("border", "Border variation"), cue("color", "Color variation")]
    return {"agent": "lesion_analysis", "cues": cues,
            "featureEvidence": [{k: c[k] for k in ("label", "value", "detail")} for c in cues],
            "suspicionScore": 0, "suspicion": "UNAVAILABLE", "reliable": False,
            "reliabilityFlags": flags, "method": "OpenCV segmentation + cue heuristics"}


def analyze_lesion(image, quality: dict = None) -> dict:
    bgr = to_bgr(image)
    h, w = bgr.shape[:2]
    s = 256.0 / max(h, w)
    small = cv2.resize(bgr, (max(8, int(w * s)), max(8, int(h * s))), interpolation=cv2.INTER_AREA)
    flags = []
    if quality and quality.get("grade") == "POOR":
        flags.append("Image quality is poor; visual cues may be unreliable.")
    if quality and quality.get("metrics", {}).get("glare_ratio", 0) > 0.015:
        flags.append("Bright regions may hide lesion boundaries or color.")

    mask = _segment(small)
    if mask is None:
        return _unavailable(flags + ["The lesion region could not be separated from surrounding skin."])
    area = float((mask > 0).mean())
    if area < C["min_area"] or area > C["max_area"]:
        return _unavailable(flags + ["The lesion region could not be separated confidently from surrounding skin."])
    edge = np.concatenate([mask[0], mask[-1], mask[:, 0], mask[:, -1]])
    if (edge > 0).mean() > C["border_touch_max"]:
        flags.append("The lesion is cut off by the frame; border cues are less reliable.")

    asym, border, color = _asymmetry(mask), _border(mask), _color(small, mask)
    if asym is None or border is None or color is None:
        return _unavailable(flags + ["Not enough lesion pixels to measure cues."])
    irr, compact, solidity = border
    cscore, cdist, ncol = color

    cues = [
        {"key": "asymmetry", "label": "Asymmetry", "value": "Elevated" if asym > C["asym_concern"] else "Low",
         "detail": f"Mirror mismatch about the lesion axes: {asym * 100:.0f}%.", "concern": asym > C["asym_concern"]},
        {"key": "border", "label": "Border variation", "value": "Elevated" if irr > C["border_concern"] else "Low",
         "detail": f"Border irregularity {irr * 100:.0f}% (compactness {compact:.2f}, solidity {solidity:.2f}).",
         "concern": irr > C["border_concern"]},
        {"key": "color", "label": "Color variation", "value": "Elevated" if cscore > C["color_concern"] else "Low",
         "detail": f"{ncol} distinct color regions, spread {cdist:.0f} units.", "concern": cscore > C["color_concern"]},
    ]
    score = int(round(100 * (0.35 * min(asym / 0.45, 1.0) + 0.30 * irr + 0.35 * cscore)))
    suspicion = ("SUSPICIOUS" if score >= C["suspicious_score"] else
                 "WATCH" if score >= C["watch_score"] else "LOW_CUE_BURDEN")
    return {"agent": "lesion_analysis", "cues": cues,
            "featureEvidence": [{k: c[k] for k in ("label", "value", "detail")} for c in cues],
            "suspicionScore": score, "suspicion": suspicion, "reliable": not flags,
            "reliabilityFlags": flags,
            "features": {"asymmetry": round(asym, 4), "border_irregularity": round(irr, 4),
                         "color_score": round(cscore, 4), "lesion_area_fraction": round(area, 4)},
            "method": "OpenCV segmentation + cue heuristics"}
