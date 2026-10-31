"""A4 - Reasoning / Context Agent. Uses age, gender and lesion location when provided.
Missing fields are recorded and NEVER guessed."""
import re

from config import CONTEXT_CFG as C


def _clean(v):
    return "" if v is None else str(v).strip()


def assess_context(context: dict = None) -> dict:
    context = context or {}
    raw_age, gender, location = _clean(context.get("age")), _clean(context.get("gender") or context.get("sex")), _clean(context.get("location") or context.get("localization"))
    if gender.lower() in ("unknown", "nan", "none"):
        gender = ""
    if location.lower() in ("unknown", "nan", "none"):
        location = ""

    age, missing = None, []
    try:
        age = float(raw_age) if raw_age and raw_age.lower() != "nan" else None
    except ValueError:
        age = None
    if age is not None and not (0 <= age <= 120):
        age = None
        missing.append("Age value is out of range and was ignored.")
    elif age is None:
        missing.append("Age not provided.")
    if not gender:
        missing.append("Gender not provided.")
    if not location:
        missing.append("Lesion location not provided.")

    risk, score = [], 0
    if age is not None and age >= C["age_high"]:
        risk.append(f"Age {int(age)} (60 or above) is a contextual risk indicator.")
        score += 2
    elif age is not None and age >= 45:
        score += 1
    if location and re.search(C["sun_exposed"], location, re.I):
        risk.append("Sun-exposed location may increase concern.")
        score += 1
    if location and re.search(C["special_site"], location, re.I):
        risk.append("This body site deserves closer review.")
        score += 1

    return {
        "agent": "context",
        "evidence": [f"Age provided: {int(age)}." if age is not None else "Age unavailable.",
                     f"Gender provided: {gender}." if gender else "Gender unavailable.",
                     f"Lesion location: {location}." if location else "Lesion location unavailable."],
        "riskIndicators": risk, "missingFields": missing, "riskScore": score,
        "riskLevel": "CONTEXT_FLAG" if risk else "NO_ADDED_FLAG",
        "fieldsProvided": 3 - sum(1 for m in missing if "not provided" in m),
    }
