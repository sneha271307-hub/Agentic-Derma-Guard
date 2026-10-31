"""Validate and upload the final CSV. The upload URL/format is announced in the WhatsApp group - adjust flags to match.

  python scripts/upload_submission.py --csv results_hidden/submission.csv --dry-run
  python scripts/upload_submission.py --csv results_hidden/submission.csv --url URL --token TOKEN [--field file] [--header Authorization --scheme Bearer]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.submission import upload_csv, validate_csv   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--csv", required=True)
ap.add_argument("--url"); ap.add_argument("--token", default="")
ap.add_argument("--field", default="file"); ap.add_argument("--header", default="Authorization")
ap.add_argument("--scheme", default="Bearer"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

problems = validate_csv(a.csv)
if problems:
    sys.exit("CSV problems:\n" + "\n".join(problems[:20]))
print("CSV is valid.")
if not a.dry_run:
    if not a.url:
        sys.exit("--url is required")
    print(upload_csv(a.csv, a.url, a.token, a.header, a.scheme, a.field))
