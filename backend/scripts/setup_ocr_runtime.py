#!/usr/bin/env python3
"""Setup OCR runtime dependencies and .env OCR keys."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
ENV_PATH = BACKEND / ".env"
ENV_EXAMPLE = BACKEND / ".env.example"
sys.path.insert(0, str(BACKEND))

OCR_ENV_KEYS: dict[str, str] = {
    "OCR_ENABLED": "false",
    "OCR_ENGINE": "paddleocr",
    "OCR_FALLBACK_ENGINE": "tesseract",
    "OCR_DPI": "250",
    "OCR_MAX_PAGES": "30",
    "OCR_MAX_SLIDES": "40",
    "OCR_MIN_TEXT_CHARS": "40",
    "OCR_CACHE_ENABLED": "true",
    "OCR_CACHE_DIR": "backend/data/ocr_cache",
    "OCR_REQUIRE_ENGINE": "false",
    "OCR_MODEL_WARMUP_ON_START": "false",
    "OCR_TESSERACT_LANG": "rus+eng",
    "OCR_EASYOCR_LANGS": "ru,en",
    "OCR_EASYOCR_GPU": "false",
    "OCR_ENGINE_PRIORITY": "tesseract,easyocr,paddleocr",
}


def detect_socks_proxy() -> tuple[bool, dict[str, str]]:
    proxies = urllib.request.getproxies()
    socks = any("socks" in str(v).lower() for v in proxies.values() if v)
    return socks, proxies


def build_pip_env(use_no_proxy: bool) -> dict[str, str]:
    env = os.environ.copy()
    if use_no_proxy:
        env["NO_PROXY"] = "*"
        env["no_proxy"] = "*"
    return env


def pip_install(packages: list[str], use_no_proxy: bool = True) -> int:
    env = build_pip_env(use_no_proxy)
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BACKEND), env=env)
    return result.returncode


def read_env_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def write_env_keys(path: Path) -> tuple[int, list[str]]:
    lines = read_env_lines(path)
    existing_keys = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        existing_keys.add(stripped.split("=", 1)[0].strip())

    appended: list[str] = []
    new_lines: list[str] = []
    for key, value in OCR_ENV_KEYS.items():
        if key in existing_keys:
            continue
        if not new_lines:
            if lines and lines[-1].strip():
                new_lines.append("")
            if not any("OCR layer" in item for item in lines):
                new_lines.append("# OCR layer (Stage H.8.2)")
        new_lines.append(f"{key}={value}")
        appended.append(key)

    if not appended:
        return 0, []

    path.parent.mkdir(parents=True, exist_ok=True)
    combined = lines + new_lines
    path.write_text("\n".join(combined) + "\n", encoding="utf-8")
    return len(appended), appended


def print_proxy_guidance() -> None:
    socks, proxies = detect_socks_proxy()
    if socks:
        print("SOCKS proxy detected. Set NO_PROXY=* or install PySocks first.")
        if proxies:
            print(f"Detected proxies: {proxies}")
        print("Suggested:")
        print("  pip install PySocks")
        print("  set NO_PROXY=*")


def print_commands() -> None:
    print("Suggested setup commands:")
    print(f"  {sys.executable} -m pip install Pillow pymupdf pytesseract PySocks")
    print(f"  {sys.executable} -m pip install paddleocr")
    print("  Install Tesseract OCR for Windows and add to PATH.")
    print("  .\\scripts\\check_ocr_env.ps1")
    print("")
    print("If PaddleOCR init succeeds but inference fails (oneDNN/PIR error), try:")
    print('  $env:FLAGS_use_mkldnn="0"')
    print('  $env:FLAGS_enable_pir_api="0"')
    print("  Or set PADDLE_DISABLE_ONEDNN=true / PADDLE_DISABLE_PIR=true")
    print("  Then re-run: python scripts/warmup_ocr_models.py --engine paddleocr")
    print("")
    print("Alternative: install Tesseract OCR for Windows as stable fallback.")
    print("")
    print("Multi-engine benchmark (Stage H.8.4):")
    print(f"  {sys.executable} -m pip install easyocr")
    print("  python scripts/benchmark_ocr_engines.py --file deck.pptx --slides 25")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Setup OCR runtime")
    parser.add_argument("--install-basic", action="store_true")
    parser.add_argument("--install-paddle", action="store_true")
    parser.add_argument("--install-tesseract-python", action="store_true")
    parser.add_argument("--install-easyocr", action="store_true")
    parser.add_argument("--install-surya", action="store_true")
    parser.add_argument("--write-env", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    if not any(
        [
            args.install_basic,
            args.install_paddle,
            args.install_tesseract_python,
            args.install_easyocr,
            args.install_surya,
            args.write_env,
            args.all,
        ]
    ):
        print("=== OCR Runtime Setup ===\n")
        print_proxy_guidance()
        print_commands()
        print("\nUse --install-basic, --install-paddle, --write-env, or --all")
        return 0

    print_proxy_guidance()
    exit_code = 0

    if args.write_env or args.all:
        count, keys = write_env_keys(ENV_PATH)
        print(f"Updated {ENV_PATH}: appended {count} OCR keys")
        if keys:
            print("Added keys:", ", ".join(keys))
        else:
            print("All OCR keys already present.")

    advanced_req = BACKEND / "requirements-advanced.txt"
    ocr_req = BACKEND / "requirements-ocr.txt"

    if args.install_basic or args.all:
        if advanced_req.is_file():
            code = pip_install(["-r", str(advanced_req)])
        else:
            code = pip_install(["Pillow", "pymupdf", "pytesseract", "PySocks"])
        exit_code = max(exit_code, code)

    if args.install_tesseract_python or args.all:
        code = pip_install(["pytesseract"])
        exit_code = max(exit_code, code)

    if args.install_paddle or args.install_easyocr or args.all:
        if ocr_req.is_file():
            code = pip_install(["-r", str(ocr_req)])
        else:
            if args.install_paddle or args.all:
                code = pip_install(["paddleocr"])
                exit_code = max(exit_code, code)
            if args.install_easyocr or args.all:
                code = pip_install(["easyocr"])
                exit_code = max(exit_code, code)
        exit_code = max(exit_code, code)

    if args.install_surya:
        code = pip_install(["surya-ocr"])
        exit_code = max(exit_code, code)

    print("\nNext step:")
    print("  .\\scripts\\check_ocr_env.ps1")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
