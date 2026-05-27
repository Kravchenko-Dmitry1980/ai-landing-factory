#!/usr/bin/env python3
"""Warm up OCR models and run a tiny OCR smoke test."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine
from app.services.ocr.ocr_env import (
    PADDLE_INFERENCE_FAILURE_GUIDANCE,
    PADDLE_MODEL_GUIDANCE,
    generate_test_image_bytes,
    run_engine_inference_smoke,
    run_test_image_ocr,
)


def warmup_paddle(*, allow_init_only: bool) -> int:
    print("=== PaddleOCR warmup ===")
    engine = PaddleOcrEngine()
    if not engine._ensure_engine():
        print(f"FAIL (init): {engine._init_error}")
        print(PADDLE_MODEL_GUIDANCE)
        print("Recommended:")
        print("  1. Check internet/proxy.")
        print("  2. set NO_PROXY=*")
        print("  3. python scripts/check_ocr_env.py --require-ocr")
        return 1
    print(f"OK: PaddleOCR initialized with {engine._init_kwargs}")
    home = Path.home()
    candidates = [
        home / ".paddleocr",
        home / ".paddlex",
        home / ".paddlex" / "official_models",
    ]
    for path in candidates:
        if path.exists():
            print(f"model cache path: {path}")

    print("\n=== Inference smoke test ===")
    inference_ok, chars, err = run_engine_inference_smoke("paddleocr")
    print(f"inference_ok: {inference_ok}, chars: {chars}")
    if err:
        print(f"error: {err}")
    if not inference_ok:
        print(PADDLE_INFERENCE_FAILURE_GUIDANCE)
        if allow_init_only:
            print("WARN: inference failed but --allow-init-only set; exiting 0")
            return 0
        return 1
    if chars == 0:
        print("WARN: inference completed but extracted 0 chars from test image")
        if not allow_init_only:
            return 1
    return 0


def warmup_tesseract(*, allow_init_only: bool) -> int:
    print("=== Tesseract warmup ===")
    engine = TesseractOcrEngine()
    if not engine.is_available():
        print("FAIL: Tesseract not available (wrapper or binary missing)")
        return 1
    image = generate_test_image_bytes()
    if image is None:
        print("WARN: Pillow missing; skipping OCR extraction test")
        return 0

    print("\n=== Inference smoke test ===")
    inference_ok, chars, err = run_engine_inference_smoke("tesseract")
    print(f"inference_ok: {inference_ok}, chars: {chars}")
    if err:
        print(f"error: {err}")
    if not inference_ok and not allow_init_only:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Warm up OCR models")
    parser.add_argument("--engine", choices=["paddleocr", "tesseract"], default="paddleocr")
    parser.add_argument("--test-image", action="store_true", help="Also run router-level test image OCR")
    parser.add_argument(
        "--allow-init-only",
        action="store_true",
        help="Exit 0 even if inference smoke test fails (init-only mode)",
    )
    args = parser.parse_args()

    if args.engine == "paddleocr":
        code = warmup_paddle(allow_init_only=args.allow_init_only)
    else:
        code = warmup_tesseract(allow_init_only=args.allow_init_only)

    if args.test_image:
        print("\n=== Test image OCR (router) ===")
        ok, chars, err = run_test_image_ocr()
        print(f"ok: {ok}, chars: {chars}")
        if err:
            print(f"note: {err}")
        if not ok and not args.allow_init_only:
            code = max(code, 1)

    return code


if __name__ == "__main__":
    raise SystemExit(main())
