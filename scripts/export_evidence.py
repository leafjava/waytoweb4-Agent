"""Verify and export one run's evidence without upgrading mock data."""

from __future__ import annotations

import argparse
import json

from backend.app.evidence_report import export_report
from backend.app.verify_evidence import EvidenceError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--live", action="store_true", help="fail unless every live evidence requirement is met")
    args = parser.parse_args()
    try:
        print(json.dumps(export_report(args.run, live=args.live), indent=2))
    except EvidenceError as exc:
        parser.error(str(exc))
