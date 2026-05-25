#!/usr/bin/env python3
"""Verify PII / Natasha environment for AI Landing Factory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.schemas.pii import PIIEntityType
from app.services.pii.detector import (
    PIIDetector,
    natasha_available,
    natasha_load_error,
    reset_natasha_cache,
)

SMOKE_TEXT = "Кравченко Дмитрий Александрович — тимлид проекта"


def _check_imports() -> dict[str, bool]:
    modules = ("natasha", "razdel", "yargy", "pymorphy2", "slovnet", "ipymarkup")
    out: dict[str, bool] = {}
    for name in modules:
        try:
            __import__(name)
            out[name] = True
        except ImportError:
            out[name] = False
    return out


def _check_natasha_components() -> dict[str, str]:
    results: dict[str, str] = {}
    try:
        from natasha import MorphVocab, NamesExtractor, Segmenter  # noqa: F401

        results["Segmenter"] = "ok"
        results["MorphVocab"] = "ok"
        results["NamesExtractor"] = "ok"
    except Exception as exc:
        results["components"] = f"fail: {exc}"
    return results


def main() -> int:
    print("=== PII Environment Check ===\n")

    imports = _check_imports()
    for mod, ok in imports.items():
        print(f"  import {mod}: {'OK' if ok else 'MISSING'}")

    print("\n--- Natasha components ---")
    for name, status in _check_natasha_components().items():
        print(f"  {name}: {status}")

    reset_natasha_cache()
    nat_ok = natasha_available()
    err = natasha_load_error()
    print(f"\nNatasha available: {nat_ok}")
    if err:
        print(f"Natasha load error: {err}")

    settings = Settings(enable_pii_detection=True, pii_mask_names=True)
    detector = PIIDetector(settings)
    entities, warnings = detector.detect_text(SMOKE_TEXT, "smoke.txt")
    person = [e for e in entities if e.type == PIIEntityType.PERSON_NAME]
    detectors = sorted({e.detector for e in entities})

    print(f"\nSmoke text: {SMOKE_TEXT}")
    print(f"  entities: {len(entities)}")
    print(f"  person names: {len(person)}")
    print(f"  detectors: {detectors or ['none']}")
    print(f"  warnings: {warnings or ['none']}")

    fallback_ok = bool(person) or any(e.detector == "regex" for e in entities)
    print(f"\nFallback available: {fallback_ok}")

    if not fallback_ok:
        print("\nFAIL: neither Natasha nor regex detected FIO in smoke text")
        return 1

    if nat_ok:
        print("\nPII env OK (Natasha + fallback)")
    else:
        print("\nPII env OK (regex fallback only; Natasha unavailable)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
