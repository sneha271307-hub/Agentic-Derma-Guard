"""Submit Level-1 results to the organizers' API (details come from the WhatsApp group).

!! build_payload() is a GUESS at the schema. Replace its body with the exact format the
organizers specify, and set SUBMIT_URL / SUBMIT_TOKEN. Use dry_run=True to inspect first.
"""
import json
import time
from typing import Optional

import requests

from config import SUBMIT_TOKEN, SUBMIT_URL, TEAM_NAME


def build_payload(summary: dict, records: list) -> dict:
    return {
        "team": TEAM_NAME,
        "level": 1,
        "summary": summary,          # accuracy, macro_f1, per-class report, quality counts ...
        "predictions": [             # one entry per validation image
            {
                "image_id": r["image_id"],
                "quality_status": r["quality_status"],
                "quality_score": r["quality_score"],
                "quality_reasons": r["quality_reasons"],
                "predicted_class": r["predicted_class"],
                "confidence": r["confidence"],
                "final_decision": r["final_decision"],
            }
            for r in records
        ],
    }


def submit_results(summary: dict, records: list, url: Optional[str] = None,
                   token: Optional[str] = None, dry_run: bool = False, retries: int = 3) -> dict:
    payload = build_payload(summary, records)
    if dry_run:
        with open("submission_payload.json", "w") as f:
            json.dump(payload, f, indent=2)
        return {"dry_run": True, "saved": "submission_payload.json"}

    url, token = url or SUBMIT_URL, token or SUBMIT_TOKEN
    if not url:
        raise RuntimeError("SUBMIT_URL not set - copy it from the WhatsApp group")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"   # adjust if they use X-API-Key etc.

    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            print(f"[submit] attempt {attempt}: HTTP {r.status_code} {r.text[:300]}")
            if r.ok:
                return {"status_code": r.status_code, "body": r.text}
            last = r.text
        except requests.RequestException as e:
            last = str(e)
            print(f"[submit] attempt {attempt} failed: {e}")
        time.sleep(2 * attempt)
    raise RuntimeError(f"Submission failed after {retries} attempts: {last}")
