#!/usr/bin/env python3
"""Audit venv for simple product mode — forbidden OCR/VLM packages must be absent."""

from __future__ import annotations

import argparse
import subprocess
import sys

FORBIDDEN_PACKAGES = frozenset(
    {
        "paddleocr",
        "paddlepaddle",
        "easyocr",
        "surya",
        "vllm",
        "ultralytics",
        "tensorflow",
        "paddlepaddle-gpu",
    }
)

# torch is not required for base simple product (no ML inference in default path).
FORBIDDEN_IF_UNUSED = frozenset({"torch", "torchvision", "torchaudio"})

REQUIRED_PACKAGES = frozenset(
    {
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic-settings",
        "python-docx",
        "python-pptx",
        "httpx",
        "pytest",
    }
)


def _pip_freeze(python_exe: str) -> list[str]:
    proc = subprocess.run(
        [python_exe, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "pip freeze failed")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _installed_names(freeze_lines: list[str]) -> set[str]:
    names: set[str] = set()
    for line in freeze_lines:
        # name==version or name @ file
        token = line.split("==")[0].split(" @ ")[0].strip().lower()
        if token:
            names.add(token.replace("_", "-"))
    # normalize underscores for comparison
    return {n.replace("-", "") for n in names} | {n for n in names}


def audit(
    python_exe: str,
    *,
    forbid_torch: bool = True,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    freeze = _pip_freeze(python_exe)
    installed = _installed_names(freeze)

    for pkg in sorted(FORBIDDEN_PACKAGES):
        key = pkg.replace("-", "")
        if key in installed or pkg in installed:
            errors.append(f"forbidden package installed: {pkg}")

    if forbid_torch:
        for pkg in sorted(FORBIDDEN_IF_UNUSED):
            key = pkg.replace("-", "")
            if key in installed or pkg in installed:
                errors.append(f"forbidden package installed (not needed in simple): {pkg}")

    for pkg in sorted(REQUIRED_PACKAGES):
        key = pkg.replace("-", "")
        if key not in installed and pkg not in installed:
            errors.append(f"required base package missing: {pkg}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit simple-mode Python dependencies")
    parser.add_argument(
        "--python",
        default="",
        help="Path to venv python.exe (default: repo .venv)",
    )
    parser.add_argument(
        "--allow-torch",
        action="store_true",
        help="Do not fail if torch is installed",
    )
    args = parser.parse_args()

    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    python_exe = args.python or str(repo_root / ".venv" / "Scripts" / "python.exe")
    if not Path(python_exe).is_file():
        print(f"FAIL: Python not found: {python_exe}", file=sys.stderr)
        return 1

    try:
        errors, warnings = audit(python_exe, forbid_torch=not args.allow_torch)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"WARN: {w}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print("OK: simple dependency audit passed")
    print(f"  python={python_exe}")
    print(f"  forbidden_absent={len(FORBIDDEN_PACKAGES)} checked")
    print(f"  required_present={len(REQUIRED_PACKAGES)} checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
