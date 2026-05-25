#!/usr/bin/env python3
"""Smoke wrapper for debug_live_project_consistency with corpus defaults."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DEBUG_SCRIPT = BACKEND / "scripts" / "debug_live_project_consistency.py"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke live project consistency audit")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument(
        "--assert-team-if-docx-present",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no-assert-team-if-docx",
        action="store_true",
        help="Disable DOCX → team export requirement",
    )
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(DEBUG_SCRIPT),
        "--project-id",
        args.project_id,
        "--backend-url",
        args.backend_url,
        "--check",
    ]
    if args.assert_team_if_docx_present and not args.no_assert_team_if_docx:
        cmd.append("--assert-team-if-docx-present")

    result = subprocess.run(cmd, cwd=str(BACKEND))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
