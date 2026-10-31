"""Replay stored agent outputs (detailed.jsonl from a LABELED validation run) under different coordinator/safety
thresholds. Pick the row you like, then re-run with --save N to write backend/policy.json.

  python scripts/tune_policy.py --detailed results_val/detailed.jsonl [--save 3]
Columns: AUTO = auto-triaged images, auto_acc = share of AUTO that had the right class,
         high_risk_auto = mel/bcc/akiec images wrongly auto-triaged (want 0).
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import HIGH_RISK_CLASSES, POLICY_FILE      # noqa: E402
from services.orchestrator import decide                # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detailed", required=True)
    ap.add_argument("--save", type=int, default=-1)
    a = ap.parse_args()
    data = [json.loads(l) for l in open(a.detailed)]
    data = [d for d in data if d.get("true_label")]
    grid = [dict(min_confidence=c, malignant_mass=m, watch_confidence=w, mel_watch=mw)
            for c, m, w, mw in itertools.product([0.6, 0.7, 0.8, 0.9], [0.2, 0.35, 0.5], [0.0, 0.85, 0.95], [0.15, 0.25])]
    table = []
    for pol in grid:
        res = [(d, decide(d["quality"], d["diagnosis"], d["lesionAnalysis"], d["context"], pol)[1]) for d in data]
        auto = [(d, c) for d, c in res if c["decision"] == "AUTO_TRIAGE"]
        ok = sum(d["true_label"] == c["predictedLabel"] for d, c in auto)
        hi = sum(d["true_label"] in HIGH_RISK_CLASSES for d, c in auto)
        table.append((pol, len(auto), ok / len(auto) if auto else 0.0, hi,
                      sum(c["decision"] == "REFER" for _, c in res), sum(c["decision"] == "RE_IMAGE" for _, c in res)))
    table.sort(key=lambda r: (r[3], -r[2], -r[1]))
    print(f"{len(data)} labeled images\n #  conf  mal   watch mel  | AUTO auto_acc high_risk_auto REFER RE_IMAGE")
    for i, (pol, n, acc, hi, rf, re) in enumerate(table[:15]):
        print(f"{i:2d}  {pol['min_confidence']:.2f}  {pol['malignant_mass']:.2f}  {pol['watch_confidence']:.2f}  {pol['mel_watch']:.2f} | "
              f"{n:4d}  {acc:7.3f}  {hi:6d}  {rf:6d}  {re:4d}")
    if a.save >= 0:
        POLICY_FILE.write_text(json.dumps(table[a.save][0], indent=2))
        print("Saved", POLICY_FILE, table[a.save][0])


if __name__ == "__main__":
    main()
