#!/usr/bin/env python3
"""Strict live project verdict gate from diagnostic JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.services.diagnostics.live_project_verdict import (  # noqa: E402
    classify_live_project_diagnostic,
    format_verdict_report,
    normalize_diagnostic_payload,
    verdict_exit_code,
)
from app.services.diagnostics.project_discovery import (  # noqa: E402
    ProjectDiscoveryError,
    ResolvedProject,
    format_discovery_banner,
    get_backend_url_from_runtime,
    resolve_project_id,
)
from scripts.debug_live_project_consistency import (  # noqa: E402
    audit_project,
    diagnostics_to_payload,
)

DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"

EPILOG = """
Examples:
  python scripts/check_live_project_verdict.py --latest
  python scripts/check_live_project_verdict.py --latest-any
  python scripts/check_live_project_verdict.py --current
  python scripts/check_live_project_verdict.py --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed

Do not type angle brackets literally. Copy UUID from /editor/{uuid} in the browser.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Live project JSON verdict gate",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project-id",
        default="",
        help="Explicit project UUID (copy from editor URL)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Newest user project with uploaded sources (skips CORS/smoke/empty)",
    )
    parser.add_argument(
        "--latest-any",
        action="store_true",
        help="Raw newest project from GET /api/v1/projects (includes technical)",
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Use .runtime/last_project.json, fallback to latest",
    )
    parser.add_argument(
        "--backend-url",
        default="",
        help="Backend base URL (default: .runtime/ports.json or 127.0.0.1:8001)",
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=REPO_ROOT,
        help="Repo root containing .runtime/ports.json",
    )
    parser.add_argument("--json-file", type=Path, default=None)
    parser.add_argument(
        "--json-out",
        action="store_true",
        help="Print gate verdict as JSON after summary",
    )
    return parser


def resolve_backend_url(args: argparse.Namespace) -> str:
    if args.backend_url:
        return args.backend_url.rstrip("/")
    return get_backend_url_from_runtime(args.runtime_root)


def resolve_target(args: argparse.Namespace) -> ResolvedProject | None:
    if args.json_file:
        return None
    if args.latest and args.current:
        raise ProjectDiscoveryError("Use only one of --latest, --latest-any, or --current.")
    if args.latest_any and args.current:
        raise ProjectDiscoveryError("Use only one of --latest, --latest-any, or --current.")
    if args.latest and args.latest_any:
        raise ProjectDiscoveryError("Use only one of --latest or --latest-any.")
    if args.project_id and (args.latest or args.latest_any or args.current):
        raise ProjectDiscoveryError(
            "Use --project-id alone or --latest/--latest-any/--current."
        )

    backend = resolve_backend_url(args)
    if not args.project_id and not args.latest and not args.latest_any and not args.current:
        raise ProjectDiscoveryError(
            "Укажите --project-id UUID, --latest, --latest-any или --current. "
            "Пример: python scripts/check_live_project_verdict.py --latest"
        )

    return resolve_project_id(
        project_id=args.project_id or None,
        latest=args.latest,
        latest_any=args.latest_any,
        current=args.current,
        base_url=backend,
        runtime_root=args.runtime_root,
        data_dir=settings.data_dir,
    )


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
        raise ValueError("project_id is required")
    diag = audit_project(backend_url, project_id)
    return diagnostics_to_payload(diag)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        resolved = resolve_target(args)
        backend_url = resolved.backend_url if resolved else resolve_backend_url(args)
        project_id = resolved.project_id if resolved else None

        if resolved:
            print(format_discovery_banner(resolved))

        payload = load_payload(
            project_id=project_id,
            backend_url=backend_url,
            json_file=args.json_file,
        )
    except ProjectDiscoveryError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
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
