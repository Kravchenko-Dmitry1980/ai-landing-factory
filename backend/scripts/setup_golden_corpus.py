#!/usr/bin/env python3
"""One-off helper: copy golden corpus binaries and write *.txt snapshots."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
GOLDEN = REPO / "test_corpus" / "golden"
DOWNLOADS = Path(r"C:\Users\Paladin 965\Downloads")

sys.path.insert(0, str(BACKEND))

from app.services.extraction.dispatcher import ExtractionDispatcher  # noqa: E402

PROJECTS: dict[str, list[tuple[str, Path]]] = {
    "indlab_telegram_news": [
        ("01_presentation.pptx", DOWNLOADS / "Proekt-Intellektualnyj-agregator.pptx"),
        ("02_landing.docx", DOWNLOADS / "Ленд Индлаб (1).docx"),
    ],
    "ksk_it_barrier": [
        ("01_presentation.pptx", DOWNLOADS / "КСК_ИТ.pptx"),
    ],
    "endocrinology": [
        ("01_landing.docx", DOWNLOADS / "Ленд проекта Эндокринология.docx"),
        ("02_glaucologic_presentation.pptx", DOWNLOADS / "GlaucoLogic_ОКТ_аналитика.pptx"),
        ("03_ai_copilot_presentation.pptx", DOWNLOADS / "AI Copilot_final3.pptx"),
    ],
}


def write_snapshot(dispatcher: ExtractionDispatcher, dest: Path, logical_name: str) -> None:
    record = dispatcher.extract_file(dest, logical_name)
    snapshot = dest.with_suffix(dest.suffix + ".txt")
    snapshot.write_text(record.extracted_text, encoding="utf-8")
    print(f"  snapshot: {snapshot.name} ({len(record.extracted_text)} chars)")


def main() -> int:
    dispatcher = ExtractionDispatcher()
    for slug, files in PROJECTS.items():
        sources = GOLDEN / slug / "sources"
        sources.mkdir(parents=True, exist_ok=True)
        print(f"\n{slug}:")
        for logical_name, src in files:
            if not src.is_file():
                print(f"  MISSING source: {src}")
                return 1
            dest = sources / logical_name
            shutil.copy2(src, dest)
            print(f"  copied: {logical_name} <- {src.name}")
            write_snapshot(dispatcher, dest, logical_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
