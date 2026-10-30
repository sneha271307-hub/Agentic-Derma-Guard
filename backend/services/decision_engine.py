"""Decision engine: BOTH agents influence the outcome.

Quality agent  -> can veto (RE_IMAGE) and can tighten the confidence bar (MARGINAL images).
Diagnosis agent -> class, confidence, margin and malignant-probability drive REFER vs AUTO_TRIAGE.

Prototype policy only; thresholds are in config.DECISION_POLICY and must be clinically reviewed.
"""
from typing import Optional

from config import DECISION_POLICY, HIGH_RISK_CLASSES


def make_decision(quality: dict, diagnosis: Optional[dict], policy: Optional[dict] = None) -> dict:
    p = {**DECISION_POLICY, **(policy or {})}

    # 1. Quality veto
    if quality["status"] == "POOR":
        return {
            "decision": "RE_IMAGE", "rule": "QUALITY_POOR",
            "reasons": ["Image quality is insufficient for a reliable analysis"] + quality["reasons"],
            "quality_influence": "Quality agent vetoed the image; diagnosis not used for the decision",
            "diagnosis_influence": "None (ignored because the image is unreliable)",
        }

    if diagnosis is None:
        return {
            "decision": "REFER", "rule": "NO_DIAGNOSIS",
            "reasons": ["Diagnosis agent produced no result; referring for safety"],
            "quality_influence": "Image accepted", "diagnosis_influence": "Unavailable",
        }

    marginal = quality["status"] == "MARGINAL"
    conf_bar = p["conf_threshold_marginal"] if marginal else p["conf_threshold"]
    q_note = ("Image only marginal: confidence bar raised to "
              f"{conf_bar:.0%}" if marginal else "Image acceptable: standard confidence bar "
              f"{conf_bar:.0%}")

    cls, conf = diagnosis["predicted_class"], diagnosis["confidence"]
    probs = sorted(diagnosis["probabilities"].values(), reverse=True)
    margin = probs[0] - probs[1] if len(probs) > 1 else 1.0
    mal = diagnosis["malignant_probability"]

    def out(decision, rule, reasons, d_note):
        return {"decision": decision, "rule": rule,
                "reasons": ["Image quality: " + quality["status"].lower()] + reasons,
                "quality_influence": q_note, "diagnosis_influence": d_note}

    if cls in HIGH_RISK_CLASSES:
        return out("REFER", "HIGH_RISK_CLASS",
                   [f"Predicted {diagnosis['predicted_name']} ({cls}) is a potentially serious category",
                    "Referral recommended for professional evaluation"],
                   f"Predicted high-risk class {cls} at {conf:.0%}")
    if mal >= p["malignant_prob_threshold"]:
        return out("REFER", "MALIGNANT_PROB",
                   [f"Combined probability of mel/bcc/akiec is {mal:.0%} (>= {p['malignant_prob_threshold']:.0%})"],
                   "Non-trivial probability of a high-risk class")
    if conf < conf_bar:
        return out("REFER", "LOW_CONFIDENCE",
                   [f"Model confidence {conf:.0%} is below required {conf_bar:.0%}"],
                   f"Low confidence in {cls}")
    if margin < p["margin_threshold"]:
        return out("REFER", "AMBIGUOUS",
                   [f"Top two classes are close (margin {margin:.0%}); prediction is ambiguous"],
                   "Ambiguous between classes")
    return out("AUTO_TRIAGE", "PASSED_RULES",
               [f"Predicted {diagnosis['predicted_name']} ({cls}) with {conf:.0%} confidence",
                "No high-risk signal under prototype rules; this is NOT a clean bill of health"],
               f"Confident low-risk class {cls}")
