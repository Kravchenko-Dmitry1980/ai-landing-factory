#!/usr/bin/env python
"""
Smoke test for document extraction dispatcher.

Usage (from backend/):
  python scripts/smoke_extract.py path_to_file
  python scripts/smoke_extract.py path_to_folder
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as: python scripts/smoke_extract.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.extraction.dispatcher import ExtractionDispatcher  # noqa: E402


def print_record(path: Path) -> None:
    dispatcher = ExtractionDispatcher()
    record = dispatcher.extract_file(path)
    chars = len(record.extracted_text)
    print("=" * 60)
    print(f"filename:   {record.filename}")
    print(f"type:       {record.file_type}")
    print(f"chars_count:{chars}")
    print(f"metadata:   {record.metadata}")
    if record.warnings:
        print(f"warnings:   {record.warnings}")
    if record.errors:
        print(f"errors:     {record.errors}")
    if chars:
        preview = record.extracted_text[:300].replace("\n", " ")
        print(f"preview:    {preview}...")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    target = Path(sys.argv[1]).resolve()
    if not target.exists():
        print(f"Not found: {target}")
        return 1

    paths: list[Path]
    if target.is_dir():
        paths = sorted(
            p for p in target.iterdir()
            if p.is_file() and not p.name.startswith(".")
        )
        if not paths:
            print(f"No files in folder: {target}")
            return 1
    else:
        paths = [target]

    for path in paths:
        print_record(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
