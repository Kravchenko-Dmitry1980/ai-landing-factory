#!/usr/bin/env python3
"""Optional Showcase Builder smoke (Stage P.6.4).

Hybrid HTTP + API flow when dev servers are running:

1. GET frontend root and /showcase (optional WARN if down).
2. POST showcase from UII template via registry API.
3. POST demo project with landing_url + demo_url.
4. POST export-zip and verify ZIP bytes/entries.
5. DELETE showcase (cleanup).

Does not require Playwright. Exit 0 with WARN when servers are unavailable
unless --require-server is passed.

Usage:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_showcase_browser.py
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_showcase_browser.py --require-server
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_PORTS = REPO_ROOT / ".runtime" / "ports.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.showcase.showcase_templates import (  # noqa: E402
    ShowcaseTemplateId,
    create_default_showcase_template,
)
from app.services.showcase.showcase_vendor import (  # noqa: E402
    VENDOR_SOURCE,
    ZIP_AFRAME_ENTRY,
    ZIP_HTML_NAME,
    ZIP_LICENSE_ENTRY,
)

SHOWCASE_HEADER = "VR/AR витрина проектов"
DEMO_PROJECT = {
    "title": "Demo AI Project",
    "description": "Тестовый проект для VR/AR витрины",
    "landing_url": "/preview/demo-project",
    "demo_url": "https://aistudio.google.com/",
    "category": "AI Demo",
}


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _warn(message: str) -> None:
    print(f"WARN: {message}")


def _read_ports() -> tuple[str, str]:
    backend = "http://127.0.0.1:8001"
    frontend = "http://localhost:3000"
    if DEFAULT_PORTS.is_file():
        data = json.loads(DEFAULT_PORTS.read_text(encoding="utf-8-sig"))
        if data.get("backend_url"):
            backend = str(data["backend_url"]).rstrip("/")
        if data.get("frontend_url"):
            frontend = str(data["frontend_url"]).rstrip("/")
    return backend, frontend


def _probe(client: httpx.Client, url: str, label: str) -> bool:
    try:
        resp = client.get(url, follow_redirects=True)
        if 200 <= resp.status_code < 400:
            print(f"OK: {label} HTTP {resp.status_code} {url}")
            return True
        _warn(f"{label} HTTP {resp.status_code} {url}")
        return False
    except httpx.HTTPError as exc:
        _warn(f"{label} unreachable {url}: {exc}")
        return False


def _verify_showcase_page(html: str) -> None:
    if SHOWCASE_HEADER not in html:
        _fail(f"/showcase page missing header {SHOWCASE_HEADER!r}")


def _verify_zip(data: bytes) -> None:
    if len(data) < 2 or data[:2] != b"PK":
        _fail("export-zip response is not a ZIP archive")
    if not VENDOR_SOURCE.is_file():
        _warn("vendored A-Frame runtime missing — skipping ZIP entry checks")
        return
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
    required = {ZIP_HTML_NAME, ZIP_AFRAME_ENTRY, ZIP_LICENSE_ENTRY}
    missing = required - names
    if missing:
        _fail(f"ZIP missing entries: {sorted(missing)}")
    print(f"OK: ZIP entries {sorted(names)}")


def run_smoke(
    *,
    backend_url: str,
    frontend_url: str,
    require_server: bool,
) -> int:
    api = f"{backend_url.rstrip('/')}/api/v1"
    showcase_id: str | None = None

    with httpx.Client(timeout=60.0, trust_env=False) as client:
        root_ok = _probe(client, frontend_url, "frontend root")
        showcase_ok = False
        if root_ok:
            try:
                resp = client.get(f"{frontend_url}/showcase", follow_redirects=True)
                if 200 <= resp.status_code < 400:
                    showcase_ok = True
                    print(f"OK: /showcase HTTP {resp.status_code}")
                    _verify_showcase_page(resp.text)
                else:
                    _warn(f"/showcase HTTP {resp.status_code}")
            except httpx.HTTPError as exc:
                _warn(f"/showcase unreachable: {exc}")

        backend_alive = False
        try:
            health = client.get(f"{api}/projects/privacy", follow_redirects=True)
            backend_alive = health.status_code < 500
        except httpx.HTTPError:
            backend_alive = False

        if not backend_alive:
            msg = "backend unavailable — start .\\run.ps1 or .\\scripts\\start_dev.ps1"
            if require_server:
                _fail(msg)
            _warn(msg)
            print("SHOWCASE BROWSER SMOKE SKIPPED (optional mode)")
            return 0

        if require_server and not showcase_ok:
            _fail("frontend /showcase not available but --require-server was set")

        template = create_default_showcase_template(
            ShowcaseTemplateId.UII_AI_PROJECTS
        ).model_dump(mode="json", exclude_none=True)

        try:
            create = client.post(f"{api}/showcases", json=template)
            if create.status_code != 201:
                _fail(f"create showcase HTTP {create.status_code}: {create.text}")
            showcase_id = create.json()["id"]
            print(f"OK: created showcase id={showcase_id}")

            add = client.post(
                f"{api}/showcases/{showcase_id}/projects",
                json=DEMO_PROJECT,
            )
            if add.status_code != 200:
                _fail(f"add project HTTP {add.status_code}: {add.text}")
            config = add.json()
            if len(config.get("projects") or []) != 1:
                _fail("expected 1 project after add")
            project = config["projects"][0]
            if not project.get("landing_url"):
                _fail("landing_url missing on saved project")
            if not project.get("demo_url"):
                _fail("demo_url missing on saved project")
            print("OK: demo project saved with landing_url and demo_url")

            export = client.post(f"{api}/showcases/{showcase_id}/export-zip")
            if export.status_code != 200:
                _fail(f"export-zip HTTP {export.status_code}: {export.text}")
            ctype = export.headers.get("content-type", "")
            if "zip" not in ctype.lower():
                _fail(f"export-zip content-type expected zip, got {ctype!r}")
            _verify_zip(export.content)
            print(f"OK: export-zip bytes={len(export.content)}")

            manual_url = f"{frontend_url}/showcase/{showcase_id}"
            print(f"MANUAL: open in browser for UI review: {manual_url}")
            if not showcase_ok:
                _warn(
                    "frontend /showcase was not verified — use manual URL above "
                    "for click-through demo checklist"
                )

        finally:
            if showcase_id:
                deleted = client.delete(f"{api}/showcases/{showcase_id}")
                if deleted.status_code != 200:
                    _warn(
                        f"cleanup delete HTTP {deleted.status_code}: {deleted.text}"
                    )
                else:
                    print(f"OK: deleted showcase id={showcase_id}")

    print("SHOWCASE BROWSER/API SMOKE PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional showcase browser/API smoke")
    parser.add_argument("--backend-url", default="")
    parser.add_argument("--frontend-url", default="")
    parser.add_argument(
        "--require-server",
        action="store_true",
        help="Fail if frontend/backend dev servers are unavailable",
    )
    args = parser.parse_args()

    default_backend, default_frontend = _read_ports()
    backend_url = args.backend_url.strip() or default_backend
    frontend_url = args.frontend_url.strip() or default_frontend

    print(f"backend={backend_url}")
    print(f"frontend={frontend_url}")

    return run_smoke(
        backend_url=backend_url,
        frontend_url=frontend_url,
        require_server=args.require_server,
    )


if __name__ == "__main__":
    raise SystemExit(main())
