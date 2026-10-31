"""Run ALL SIX agents on a folder of images (validation set or the hidden test set).

Validation (labels known):
  python scripts/run_pipeline.py --images-dir VAL_IMGS --labels-csv VAL.csv --label-col dx \
         --meta-csv VAL_META.csv --out results_val
Hidden test (NO labels; metadata only if the organizers provide it):
  python scripts/run_pipeline.py --images-dir HIDDEN_IMGS --out results_hidden [--meta-csv META.csv]

Outputs in --out:
  submission.csv    image_id,prediction,decision      <- the file to upload
  records.json      rows for the portal's Batch page ("Load results (JSON)")
  detailed.jsonl    full output of all six agents per image (for the demo and tune_policy.py)
  summary.json      (only with labels) accuracy, macro-F1, confusion matrix, correct/incorrect AUTO_TRIAGE, counts
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import diagnosis_agent as dx                    # noqa: E402
from agents.context_agent import assess_context              # noqa: E402
from agents.lesion_agent import analyze_lesion               # noqa: E402
from agents.quality_agent import check_image_quality         # noqa: E402
from config import CLASSES, HIGH_RISK_CLASSES, MODEL_PATH    # noqa: E402
from services.orchestrator import assemble, decide           # noqa: E402
from services.submission import validate_csv, write_csv      # noqa: E402
from utils.image_processing import to_bgr                    # noqa: E402

EXTS = {".jpg", ".jpeg", ".png"}


def metrics(rows):
    from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix,
                                 f1_score, roc_auc_score)
    y, p = [r["true_label"] for r in rows], [r["predicted_class"] for r in rows]
    rep = classification_report(y, p, labels=CLASSES, output_dict=True, zero_division=0)
    auto = [r for r in rows if r["decision"] == "AUTO_TRIAGE"]
    cm = confusion_matrix(y, p, labels=CLASSES)
    hi = [r for r in rows if r["true_label"] in HIGH_RISK_CLASSES]
    out = {
        "n_images": len(rows),
        "accuracy": round(accuracy_score(y, p), 4),
        "balanced_accuracy": round(balanced_accuracy_score(y, p), 4),
        "macro_f1": round(f1_score(y, p, labels=CLASSES, average="macro", zero_division=0), 4),
        "per_class": {c: {k: round(v, 4) for k, v in rep[c].items()} for c in CLASSES},
        "confusion_matrix": {"labels": CLASSES, "matrix": cm.tolist()},
        "class_wise_errors": {c: int(cm[i].sum() - cm[i, i]) for i, c in enumerate(CLASSES)},
        "decisions": dict(Counter(r["decision"] for r in rows)),
        "auto_triage": {"total": len(auto),
                        "correct": sum(r["true_label"] == r["predicted_class"] for r in auto),
                        "incorrect": sum(r["true_label"] != r["predicted_class"] for r in auto)},
        "refer": sum(r["decision"] == "REFER" for r in rows),
        "re_image": sum(r["decision"] == "RE_IMAGE" for r in rows),
        "high_risk_sent_to_auto_triage": sum(r["decision"] == "AUTO_TRIAGE" for r in hi),
    }
    ys = [r["true_label"] in HIGH_RISK_CLASSES for r in rows]
    if 0 < sum(ys) < len(ys):
        out["a3_cue_auc_for_high_risk"] = round(float(roc_auc_score(ys, [r["suspicion_score"] for r in rows])), 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-dir", required=True)
    ap.add_argument("--out", default="results")
    ap.add_argument("--labels-csv"); ap.add_argument("--id-col", default="image_id"); ap.add_argument("--label-col", default="dx")
    ap.add_argument("--meta-csv"); ap.add_argument("--meta-id-col", default="image_id")
    ap.add_argument("--age-col", default="age"); ap.add_argument("--sex-col", default="sex"); ap.add_argument("--loc-col", default="localization")
    ap.add_argument("--batch-size", type=int, default=32); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    files = sorted(p for p in Path(a.images_dir).rglob("*") if p.suffix.lower() in EXTS)
    if a.limit:
        files = files[:a.limit]
    ids = [p.stem for p in files]
    if len(set(ids)) != len(ids):
        sys.exit("Duplicate image IDs (same filename in two folders). Fix before continuing.")
    print(f"{len(files)} images")

    labels = {}
    if a.labels_csv:
        df = pd.read_csv(a.labels_csv)
        labels = {str(r[a.id_col]): str(r[a.label_col]).strip().lower() for _, r in df.iterrows()}
        bad = set(labels.values()) - set(CLASSES)
        if bad:
            sys.exit(f"Labels not in CLASSES: {bad}. Check --label-col.")
    meta = {}
    if a.meta_csv:
        df = pd.read_csv(a.meta_csv)
        for _, r in df.iterrows():
            meta[str(r[a.meta_id_col])] = {"age": r.get(a.age_col), "gender": r.get(a.sex_col), "location": r.get(a.loc_col)}

    use_model = MODEL_PATH.exists()
    if not use_model:
        print("[warn] NO TRAINED MODEL FOUND - predictions are MOCK; do not submit these results")

    rows, detailed = [], []
    for s in range(0, len(files), a.batch_size):
        chunk = files[s:s + a.batch_size]
        imgs = [to_bgr(p) for p in chunk]
        a1s = [check_image_quality(i) for i in imgs]
        a2s = ([dx.result_from_probs(pr) for pr in dx.predict_probs_batch(imgs)] if use_model
               else [dx.predict_lesion(i) for i in imgs])
        for p, img, a1, a2 in zip(chunk, imgs, a1s, a2s):
            iid = p.stem
            a3 = analyze_lesion(img, a1)
            a4 = assess_context(meta.get(iid))
            a5, a6 = decide(a1, a2, a3, a4)
            full = assemble(iid, a1, a2, a3, a4, a5, a6)
            full["true_label"] = labels.get(iid)
            detailed.append(full)
            rows.append({"id": iid, "image_id": iid, "true_label": labels.get(iid),
                         "predicted_class": a6["predictedLabel"], "confidence": round(float(a2["confidence"]), 4),
                         "quality_score": a1["score"], "quality_status": a1["status"],
                         "quality_reason": "; ".join(a1["reasons"][:2]), "decision": a6["decision"],
                         "suspicion_score": a3["suspicionScore"], "safety_flag": a5["flag"]})
        print(f"  {min(s + a.batch_size, len(files))}/{len(files)}")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv(({"image_id": r["image_id"], "prediction": r["predicted_class"], "decision": r["decision"]} for r in rows),
                         str(out / "submission.csv"))
    problems = validate_csv(csv_path, expected_ids=ids)
    (out / "records.json").write_text(json.dumps(rows, indent=1))
    with open(out / "detailed.jsonl", "w") as f:
        for d in detailed:
            f.write(json.dumps(d) + "\n")
    print("submission.csv:", "OK (valid)" if not problems else problems[:5])

    summary = {"mock": not use_model, "decisions": dict(Counter(r["decision"] for r in rows))}
    if labels:
        summary.update(metrics([r for r in rows if r["true_label"]]))
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_class", "confusion_matrix")}, indent=2))


if __name__ == "__main__":
    main()
