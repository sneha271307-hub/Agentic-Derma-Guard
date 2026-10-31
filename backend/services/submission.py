"""Final CSV: exactly one row per hidden-test image with columns image_id, prediction, decision."""
import csv
import time
from typing import Iterable, Optional

import requests

from config import CLASSES

DECISIONS = {"AUTO_TRIAGE", "REFER", "RE_IMAGE"}


def write_csv(rows: Iterable[dict], path: str) -> str:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "prediction", "decision"])
        for r in rows:
            w.writerow([r["image_id"], r["prediction"], r["decision"]])
    return path


def validate_csv(path: str, expected_ids: Optional[Iterable[str]] = None) -> list:
    problems, seen = [], set()
    with open(path, newline="") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != ["image_id", "prediction", "decision"]:
            problems.append(f"Columns must be exactly image_id,prediction,decision (got {rd.fieldnames})")
        for i, row in enumerate(rd, 2):
            iid = row.get("image_id", "")
            if not iid or iid in seen:
                problems.append(f"line {i}: missing or duplicate image_id '{iid}'")
            seen.add(iid)
            if row.get("prediction") not in CLASSES:
                problems.append(f"line {i}: bad prediction '{row.get('prediction')}'")
            if row.get("decision") not in DECISIONS:
                problems.append(f"line {i}: bad decision '{row.get('decision')}'")
    if expected_ids is not None:
        exp = set(expected_ids)
        if exp - seen:
            problems.append(f"{len(exp - seen)} expected image IDs are missing")
        if seen - exp:
            problems.append(f"{len(seen - exp)} unexpected image IDs present")
    return problems


def upload_csv(path: str, url: str, token: str = "", header: str = "Authorization", scheme: str = "Bearer",
               field: str = "file", extra: Optional[dict] = None, retries: int = 3) -> dict:
    headers = {header: f"{scheme} {token}".strip()} if token else {}
    last = None
    for attempt in range(1, retries + 1):
        try:
            with open(path, "rb") as f:
                r = requests.post(url, files={field: ("submission.csv", f, "text/csv")}, data=extra or {},
                                  headers=headers, timeout=120)
            print(f"[upload] attempt {attempt}: HTTP {r.status_code} {r.text[:300]}")
            if r.ok:
                return {"status_code": r.status_code, "body": r.text}
            last = r.text
        except requests.RequestException as e:
            last = str(e)
            print(f"[upload] attempt {attempt} failed: {e}")
        time.sleep(2 * attempt)
    raise RuntimeError(f"Upload failed after {retries} attempts: {last}")
