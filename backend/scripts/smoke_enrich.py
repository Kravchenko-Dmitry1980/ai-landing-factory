#!/usr/bin/env python
"""
Smoke test for LLM contract enrichment.

Usage (from backend/):
  python scripts/smoke_enrich.py <project_id>
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402
from app.core.dependencies import get_llm_contract_builder  # noqa: E402


async def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    project_id = UUID(sys.argv[1])
    builder = get_llm_contract_builder()
    print(f"LLM_ENABLED={settings.llm_enabled} LLM_PROVIDER={settings.llm_provider}")

    try:
        result = await builder.enrich(project_id)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print("message:", result.message)
    print("status:", result.contract.status)
    print("title:", result.contract.title)
    print("missing_fields:", result.enrichment.missing_fields)
    print("confidence:", result.enrichment.confidence.model_dump())
    print("source_trace:", json.dumps(
        [t.model_dump() for t in result.enrichment.source_trace],
        ensure_ascii=False,
        indent=2,
    ))
    print("blocks:", len(result.contract.blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
