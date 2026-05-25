#!/usr/bin/env python
"""Smoke test for semantic generation."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402
from app.core.dependencies import get_semantic_engine  # noqa: E402


async def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/smoke_semantic.py <project_id>")
        return 1
    pid = UUID(sys.argv[1])
    print(
        f"SEMANTIC_GENERATION_ENABLED={settings.semantic_generation_enabled} "
        f"SEMANTIC_USE_LLM={settings.semantic_use_llm} LLM_ENABLED={settings.llm_enabled}"
    )
    result = await get_semantic_engine().generate(pid)
    print("message:", result.message)
    print("domain:", result.semantic.domain.value)
    print("sections:", len(result.semantic.sections))
    print("layout:", result.semantic.layout_preset)
    print("warnings:", result.semantic.metadata.hallucination_warnings[:5])
    print("landing blocks:", len(result.landing.blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
