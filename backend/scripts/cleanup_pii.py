#!/usr/bin/env python3
"""CLI: remove expired PII reports and safe payload artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.services.pii.cleanup import cleanup_expired_pii_reports


def main() -> int:
    reports, artifacts = cleanup_expired_pii_reports(settings)
    print(f"Deleted {reports} expired PII reports, {artifacts} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
