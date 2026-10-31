"""A5 - Safety Agent. Reviews A1..A4 for conflicts or unsafe automatic decisions.
Output: flag (SAFETY_FLAG | CLEAR), veto, trigger, conflicts, notes, justification."""
from config import CLASS_NAMES, HIGH_RISK_CLASSES, load_policy


def review_safety(quality: dict, diagnosis: dict, lesion: dict, context: dict, policy: dict = None) -> dict:
    p = load_policy(policy)
    cls, conf = diagnosis["predicted_class"], diagnosis["confidence"]
    benign_top = cls not in HIGH_RISK_CLASSES
    marginal = quality.get("grade") == "MARGINAL"
    conf_bar = p["min_confidence_marginal"] if marginal else p["min_confidence"]
    conflicts, notes = [], []

    veto = quality["status"] == "POOR"
    if veto:
        conflicts.append("Image quality is poor, so the diagnosis and visual cues cannot be trusted.")
    if conf < conf_bar:
        conflicts.append(f"Diagnosis confidence {conf:.0%} is below the required {conf_bar:.0%}"
                         + (" (raised because the image is only marginal)." if marginal else "."))
    if benign_top and lesion["suspicion"] == "SUSPICIOUS":
        conflicts.append(f"Visual cues are suspicious (score {lesion['suspicionScore']}/100) while the model predicts the low-risk class {CLASS_NAMES.get(cls, cls)}.")
    if benign_top and diagnosis["malignant_probability"] >= p["malignant_mass"]:
        conflicts.append(f"Melanoma, BCC and AK together hold {diagnosis['malignant_probability']:.0%} of the probability despite a low-risk top class.")
    if benign_top and context["riskLevel"] == "CONTEXT_FLAG" and conf < p["context_confidence"]:
        conflicts.append("Context raises concern and the low-risk prediction is not confident enough to override it.")

    if not benign_top and lesion["suspicion"] == "LOW_CUE_BURDEN":
        notes.append("A2 predicts a high-risk class but A3 sees few visual cues (disagreement); referral still applies.")
    notes.extend(lesion.get("reliabilityFlags", []))
    notes.extend(context.get("missingFields", []))

    flag = bool(conflicts)
    return {
        "agent": "safety", "flag": "SAFETY_FLAG" if flag else "CLEAR", "veto": veto,
        "trigger": ("Poor image quality" if veto else conflicts[0] if conflicts else "No conflict trigger"),
        "conflicts": conflicts, "notes": notes,
        "justification": ("The coordinator must not auto-triage while these safety concerns remain." if flag
                          else "No evidence conflict or unsafe automatic decision detected under the current policy."),
    }
