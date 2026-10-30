"""Run BOTH agents + decision engine on all validation images, compute metrics, optionally submit.

Usage (from backend/):
  python scripts/run_validation.py --val-dir /path/val_images --labels-csv /path/val_labels.csv \
         --id-col image_id --label-col dx --out results            # evaluate only
  ... --submit            # also POST to organizers' API (needs SUBMIT_URL/SUBMIT_TOKEN)
  ... --submit --dry-run  # write submission_payload.json instead of sending
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import diagnosis_agent as dx                      # noqa: E402
from agents.quality_agent import check_image_quality           # noqa: E402
from config import CLASSES, HIGH_RISK_CLASSES, MODEL_PATH      # noqa: E402
from services.decision_engine import make_decision             # noqa: E402
from services.submission import submit_results                 # noqa: E402

EXTS = (".jpg", ".jpeg", ".png")


def find_image(root: Path, image_id: str):
    for ext in EXTS:
        p = root / f"{image_id}{ext}"
        if p.exists():
            return p
    hits = list(root.rglob(f"{image_id}.*"))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val-dir", required=True)
    ap.add_argument("--labels-csv", required=True)
    ap.add_argument("--id-col", default="image_id")
    ap.add_argument("--label-col", default="dx")
    ap.add_argument("--out", default="results")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    df = pd.read_csv(a.labels_csv)
    df[a.label_col] = df[a.label_col].astype(str).str.strip().str.lower()
    unknown = set(df[a.label_col]) - set(CLASSES)
    if unknown:
        sys.exit(f"Labels not in CLASSES: {unknown}. Fix config.CLASSES or --label-col.")

    root, items = Path(a.val_dir), []
    for _, row in df.iterrows():
        p = find_image(root, str(row[a.id_col]))
        if p is None:
            print(f"[warn] missing image for {row[a.id_col]}")
            continue
        items.append((str(row[a.id_col]), p, row[a.label_col]))
    print(f"Evaluating {len(items)} images")

    # --- Agent 1 on every image
    qualities = []
    for i, (_, p, _) in enumerate(items, 1):
        qualities.append(check_image_quality(p))
        if i % 200 == 0:
            print(f"  quality {i}/{len(items)}")

    # --- Agent 2 on every image (metrics need predictions for all 2000)
    diagnoses = []
    use_batch = MODEL_PATH.exists()
    if use_batch:
        for s in range(0, len(items), a.batch_size):
            chunk = [p for _, p, _ in items[s:s + a.batch_size]]
            for pr in dx.predict_probs_batch(chunk):
                diagnoses.append(dx.result_from_probs(pr))
            if (s // a.batch_size) % 10 == 0:
                print(f"  diagnosis {min(s + a.batch_size, len(items))}/{len(items)}")
    else:
        print("[warn] no trained model found - using MOCK predictions (numbers are meaningless)")
        diagnoses = [dx.predict_lesion(p) for _, p, _ in items]

    # --- Decision layer
    records = []
    for (iid, _, true), q, d in zip(items, qualities, diagnoses):
        dec = make_decision(q, d)
        records.append({
            "image_id": iid, "true_class": true,
            "quality_status": q["status"], "quality_score": q["score"], "quality_reasons": q["reasons"], "quality_checks": q["checks"],
            "predicted_class": d["predicted_class"], "confidence": d["confidence"],
            "malignant_probability": d["malignant_probability"],
            "final_decision": dec["decision"], "rule": dec["rule"],
        })

    y_true = [r["true_class"] for r in records]
    y_pred = [r["predicted_class"] for r in records]
    rep = classification_report(y_true, y_pred, labels=CLASSES, output_dict=True, zero_division=0)
    hi = [r for r in records if r["true_class"] in HIGH_RISK_CLASSES]
    hi_missed = [r for r in hi if r["final_decision"] == "AUTO_TRIAGE"]

    summary = {
        "n_images": len(records),
        "classification": {
            "accuracy": round(accuracy_score(y_true, y_pred), 4),
            "balanced_accuracy": round(balanced_accuracy_score(y_true, y_pred), 4),
            "macro_f1": round(f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0), 4),
            "weighted_f1": round(f1_score(y_true, y_pred, labels=CLASSES, average="weighted", zero_division=0), 4),
            "per_class": {c: {k: round(v, 4) for k, v in rep[c].items()} for c in CLASSES},
            "confusion_matrix": {"labels": CLASSES,
                                 "matrix": confusion_matrix(y_true, y_pred, labels=CLASSES).tolist()},
        },
        "quality": {
            "status_counts": dict(Counter(r["quality_status"] for r in records)),
            "flagged_checks": dict(Counter(f"{k}:{v}" for r in records for k, v in r["quality_checks"].items() if v != "PASS")),
            "mean_score": round(float(np.mean([r["quality_score"] for r in records])), 4),
        },
        "decisions": {
            "counts": dict(Counter(r["final_decision"] for r in records)),
            "rule_counts": dict(Counter(r["rule"] for r in records)),
            "high_risk_total": len(hi),
            "high_risk_sent_to_AUTO_TRIAGE": len(hi_missed),
            "high_risk_referral_recall": round(1 - len(hi_missed) / max(1, len(hi)), 4),
        },
        "mock": not use_batch,
    }

    out = Path(a.out)
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    pd.DataFrame(records).to_csv(out / "records.csv", index=False)   # for your own analysis only
    (out / "records.json").write_text(json.dumps(records))
    print(json.dumps({k: summary[k] for k in ("n_images", "quality", "decisions")}, indent=2))
    c = summary["classification"]
    print(f"accuracy={c['accuracy']}  balanced_acc={c['balanced_accuracy']}  macro_f1={c['macro_f1']}")

    if a.submit:
        print(submit_results(summary, records, dry_run=a.dry_run))


if __name__ == "__main__":
    main()
