"""A6 - Coordinator Agent. Applies a documented, ordered policy to all agent outputs.
Final predicted label = Diagnosis Agent's top class (every image gets a prediction AND a decision)."""
from config import CLASS_NAMES, HIGH_RISK_CLASSES, load_policy

POLICY_TEXT = [
    "1. A1 grade POOR (or safety veto)          -> RE_IMAGE",
    "2. A5 raised SAFETY_FLAG                    -> REFER",
    "3. A2 predicts mel / bcc / akiec            -> REFER",
    "4. A2 P(mel) >= mel_watch                   -> REFER",
    "5. A2 confidence < min_confidence           -> REFER",
    "6. A3 not LOW_CUE_BURDEN and confidence < watch_confidence -> REFER",
    "7. otherwise                                -> AUTO_TRIAGE",
]


def _agreement(diagnosis, lesion, context):
    hi = diagnosis["predicted_class"] in HIGH_RISK_CLASSES
    a3 = ("INCONCLUSIVE" if lesion["suspicion"] == "UNAVAILABLE" else
          "AGREE" if hi == (lesion["suspicion"] != "LOW_CUE_BURDEN") else "DISAGREE")
    a4 = ("NO_CONTEXT" if context["fieldsProvided"] == 0 else
          "AGREE" if hi == (context["riskLevel"] == "CONTEXT_FLAG") else "DISAGREE")
    return {"A2_vs_A3": a3, "A2_vs_A4": a4}


def coordinate(quality, diagnosis, lesion, context, safety, policy: dict = None) -> dict:
    p = load_policy(policy)
    cls, conf = diagnosis["predicted_class"], diagnosis["confidence"]
    name = CLASS_NAMES.get(cls, cls)
    reasons = []

    if quality["status"] == "POOR" or safety["veto"]:
        decision = "RE_IMAGE"
        reasons.append("Image Quality Agent flagged the photo as inadequate.")
        reasons.extend(quality["reasons"][:3])
        rule = 1
    elif safety["flag"] == "SAFETY_FLAG":
        decision, rule = "REFER", 2
        reasons.extend(safety["conflicts"])
    elif cls in HIGH_RISK_CLASSES:
        decision, rule = "REFER", 3
        reasons.append(f"{name} is a high-risk predicted class ({conf:.0%}).")
    elif diagnosis["probabilities"].get("mel", 0) >= p["mel_watch"]:
        decision, rule = "REFER", 4
        reasons.append(f"Melanoma probability is {diagnosis['probabilities']['mel']:.0%}, above the watch threshold.")
    elif conf < p["min_confidence"]:
        decision, rule = "REFER", 5
        reasons.append(f"Diagnosis confidence ({conf:.0%}) is below the threshold.")
    elif lesion["suspicion"] != "LOW_CUE_BURDEN" and conf < p["watch_confidence"]:
        decision, rule = "REFER", 6
        reasons.append(f"Lesion Analysis reports {lesion['suspicion']} (score {lesion['suspicionScore']}/100) and confidence {conf:.0%} is not high enough to override it.")
    else:
        decision, rule = "AUTO_TRIAGE", 7
        reasons.append(f"Clear photo and confident, low-risk prediction: {name} ({conf:.0%}); visual cues, context and safety review raise no concern.")

    headline = {"AUTO_TRIAGE": "Routine follow-up", "RE_IMAGE": "Take a new photo"}.get(decision, "Refer to a dermatologist")
    summary = {"AUTO_TRIAGE": "The available evidence passed the documented screening policy. This is not a clean bill of health.",
               "RE_IMAGE": "Image quality is inadequate; another photo is needed.",
               "REFER": "Suspicion, uncertainty, or conflicting evidence warrants expert review."}[decision]
    return {
        "agent": "coordinator", "predictedLabel": cls, "decision": decision, "rule": rule,
        "headline": headline, "summary": summary, "reasons": reasons,
        "agreement": _agreement(diagnosis, lesion, context),
        "agentVotes": {"A1": quality["grade"], "A2": f"{cls} {conf:.0%}", "A3": lesion["suspicion"],
                       "A4": context["riskLevel"], "A5": safety["flag"]},
        "rationale": (f"A6 reviewed A1 quality ({quality['grade']}, {quality['score']}/100), A2 diagnosis ({cls}, {conf:.0%}), "
                      f"A3 visual suspicion ({lesion['suspicion']}, {lesion['suspicionScore']}/100), A4 context ({context['riskLevel']}) "
                      f"and A5 safety ({safety['flag']}). Decision by policy rule {rule}."),
        "policy": POLICY_TEXT,
    }
