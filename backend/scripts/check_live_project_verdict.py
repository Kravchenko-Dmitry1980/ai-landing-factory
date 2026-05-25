#!/usr/bin/env python3
"""Strict live project verdict gate from diagnostic JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.diagnostics.live_project_verdict import (  # noqa: E402
    classify_live_project_diagnostic,
    format_verdict_report,
    normalize_diagnostic_payload,
    verdict_exit_code,
)
from scripts.debug_live_project_consistency import (  # noqa: E402
    audit_project,
    diagnostics_to_payload,
)

DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"


def load_payload(
    *,
    project_id: str | None,
    backend_url: str,
    json_file: Path | None,
) -> dict[str, Any]:
    if json_file:
        raw = json.loads(json_file.read_text(encoding="utf-8"))
        return normalize_diagnostic_payload(raw)
    if not project_id:
        raise ValueError("Provide --project-id or --json-file")
    diag = audit_project(backend_url, project_id)
    return diagnostics_to_payload(diag)


def main() -> int:
    parser = argparse.ArgumentParser(description="Live project JSON verdict gate")
    parser.add_argument("--project-id", default="")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--json-file", type=Path, default=None)
    parser.add_argument(
        "--json-out",
        action="store_true",
        help="Print gate verdict as JSON after summary",
    )
    args = parser.parse_args()

    if not args.project_id and not args.json_file:
        parser.error("Provide --project-id or --json-file")

    try:
        payload = load_payload(
            project_id=args.project_id or None,
            backend_url=args.backend_url,
            json_file=args.json_file,
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    gate = classify_live_project_diagnostic(payload)
    print(format_verdict_report(gate, payload))

    if args.json_out:
        print()
        print(json.dumps(gate.to_dict(), ensure_ascii=False, indent=2))

    return verdict_exit_code(gate.status)


if __name__ == "__main__":
    raise SystemExit(main())
