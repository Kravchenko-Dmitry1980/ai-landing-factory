"""Smoke check for evidence visibility API."""

from __future__ import annotations

import argparse
import json
import sys
from uuid import UUID

import httpx

DEFAULT_BASE = "http://127.0.0.1:8001/api/v1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke evidence visibility endpoint")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/projects/{args.project_id}/evidence-report"
    try:
        with httpx.Client(timeout=30.0, trust_env=False) as client:
            resp = client.get(url)
    except httpx.HTTPError as exc:
        print(f"FAIL: request error: {exc}")
        return 1

    if resp.status_code != 200:
        print(f"FAIL: HTTP {resp.status_code}: {resp.text[:500]}")
        return 1

    data = resp.json()
    payload = json.dumps(data, ensure_ascii=False)
    if len(payload) > 500_000:
        print(f"FAIL: payload too large ({len(payload)} bytes)")
        return 1

    if data.get("source_count", 0) <= 0:
        print("WARN: source_count is 0")

    if data.get("evidence_count", 0) <= 0:
        print("WARN: evidence_count is 0")

    field_sources = data.get("field_sources") or {}
    if not field_sources:
        print("WARN: field_sources empty")

    title = field_sources.get("title")
    if title and "01_landing.docx" not in json.dumps(title, ensure_ascii=False):
        print("WARN: title source may not include 01_landing.docx")

    for src in data.get("sources") or []:
        if src.get("filename") == "02_glaucologic_presentation.pptx":
            if src.get("source_role") != "module_presentation":
                print("FAIL: GlaucoLogic should be module_presentation")
                return 1
            title_refs = json.dumps(title or {}, ensure_ascii=False)
            if "02_glaucologic" in title_refs:
                print("FAIL: module presentation should not own title")
                return 1

    print(f"OK: evidence-report for {args.project_id}")
    print(
        f"  parser_mode={data.get('parser_mode')} "
        f"sources={data.get('source_count')} "
        f"evidence={data.get('evidence_count')}"
    )
    return 0


if __name__ == "__main__":
    try:
        UUID(sys.argv[sys.argv.index("--project-id") + 1])
    except (ValueError, IndexError):
        pass
    raise SystemExit(main())
