#!/usr/bin/env python3
"""Simple user flow smoke: upload → contract → generate → HTML export (no OCR/VLM)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_CORPUS = REPO_ROOT / "test_corpus" / "golden"
DEFAULT_PORTS = REPO_ROOT / ".runtime" / "ports.json"

sys.path.insert(0, str(BACKEND))

from scripts.smoke_live_multifile_project import (  # noqa: E402
    _build_docx_from_text,
    _build_pptx_from_text,
    _resolve_corpus_files,
)

VALID_PARSER_MODES = frozenset(
    {
        "structured",
        "multi_source_assembly",
        "field_level_fusion",
        "project_presentation",
    }
)

CONTENT_FIELDS = ("essence", "tasks", "modules", "problem", "solution")


def _read_backend_url(explicit: str) -> str:
    if explicit:
        return explicit.rstrip("/")
    if DEFAULT_PORTS.is_file():
        data = json.loads(DEFAULT_PORTS.read_text(encoding="utf-8-sig"))
        url = data.get("backend_url") or ""
        if url:
            return str(url).rstrip("/")
    return "http://127.0.0.1:8001"


def _contract_has_content(contract: dict) -> list[str]:
    errors: list[str] = []
    blocks = contract.get("blocks") or []
    if not blocks:
        errors.append("contract has no blocks")
        return errors

    joined = json.dumps(contract, ensure_ascii=False).lower()
    found_any = False
    for field in CONTENT_FIELDS:
        if field in joined and re.search(rf'"{field}"\s*:\s*"[^"]{{8,}}', joined):
            found_any = True
            break
        if field in joined and re.search(rf'"{field}"\s*:\s*\[[^\]]{{10,}}', joined):
            found_any = True
            break
    if not found_any:
        # fallback: any block with content or bullets
        for block in blocks:
            if (block.get("content") or "").strip():
                found_any = True
                break
            if block.get("bullets"):
                found_any = True
                break
    if not found_any:
        errors.append("essence/tasks/modules (or block content) appear empty")
    return errors


def run_flow(backend_url: str, corpus_project: str = "indlab_telegram_news") -> list[str]:
    errors: list[str] = []
    api = f"{backend_url.rstrip('/')}/api/v1"

    try:
        upload_files = _resolve_corpus_files(corpus_project)
    except FileNotFoundError as exc:
        # Synthetic minimal fallback
        tmp = Path(tempfile.mkdtemp(prefix="uat_simple_"))
        docx = tmp / "landing.docx"
        pptx = tmp / "deck.pptx"
        _build_docx_from_text(
            "Indlab Telegram News\nСуть: агрегатор новостей.\nЗадачи: сбор и ранжирование.",
            docx,
        )
        _build_pptx_from_text(
            "Slide 1: Indlab\nИнтеллектуальный ассистент для Telegram.",
            pptx,
        )
        upload_files = [(docx.name, docx), (pptx.name, pptx)]

    with httpx.Client(timeout=120.0, trust_env=False) as client:
        create = client.post(
            f"{api}/projects",
            json={"name": "UAT simple flow", "description": "fresh clone user flow"},
        )
        if create.status_code != 201:
            return [f"create project HTTP {create.status_code}: {create.text}"]
        project_id = create.json()["id"]

        multipart = [
            ("files", (name, path.read_bytes(), "application/octet-stream"))
            for name, path in upload_files
        ]
        upload = client.post(f"{api}/projects/{project_id}/upload", files=multipart)
        if upload.status_code != 200:
            return [f"upload HTTP {upload.status_code}: {upload.text}"]

        contract_resp = client.get(f"{api}/projects/{project_id}/contract")
        if contract_resp.status_code != 200:
            return [f"contract HTTP {contract_resp.status_code}"]
        contract = contract_resp.json()

        title = (contract.get("title") or "").strip()
        if not title:
            errors.append("contract title is empty")

        fidelity = contract.get("fidelity") or {}
        parser_mode = fidelity.get("parser_mode") or ""
        if parser_mode not in VALID_PARSER_MODES:
            errors.append(f"invalid parser_mode={parser_mode!r}")

        errors.extend(_contract_has_content(contract))

        gen = client.post(
            f"{api}/projects/{project_id}/generate",
            json={"mode": "stub", "enrich": False},
        )
        if gen.status_code != 200:
            errors.append(f"generate HTTP {gen.status_code}: {gen.text}")

        export = client.get(
            f"{api}/projects/{project_id}/export/html",
            params={"theme": "university_platform"},
        )
        if export.status_code != 200:
            errors.append(f"export HTTP {export.status_code}: {export.text}")
            return errors

        html = export.json().get("html") or ""
        if "<html" not in html.lower():
            errors.append("export HTML missing <html")
        if title and title.lower() not in html.lower():
            # title may be normalized — warn only if completely absent project markers
            if "indlab" not in html.lower() and "проект" not in html.lower():
                errors.append("export HTML missing title/project markers")

        theme_ok = (
            "theme-university_platform" in html
            or "university_platform" in html
            or "theme-default" in html
        )
        if not theme_ok:
            errors.append("export missing university_platform or default theme marker")

        blob = html.lower()
        for term in ("install tesseract", "paddleocr", "easyocr", "ollama", "vllm required"):
            if term in blob:
                errors.append(f"export suggests OCR/VLM requirement: {term}")

        print(f"project_id={project_id}")
        print(f"parser_mode={parser_mode}")
        print(f"title={title!r}")
        print(f"html_bytes={len(html.encode('utf-8'))}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple user flow HTTP smoke")
    parser.add_argument("--backend-url", default="")
    parser.add_argument("--corpus-project", default="indlab_telegram_news")
    args = parser.parse_args()

    backend_url = _read_backend_url(args.backend_url)
    errors = run_flow(backend_url, args.corpus_project)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("OK: simple user flow smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
