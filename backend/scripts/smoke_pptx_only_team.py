#!/usr/bin/env python3
"""Live smoke: PPTX-only upload → team in contract and export."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_CORPUS = REPO_ROOT / "test_corpus" / "golden"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"

sys.path.insert(0, str(BACKEND))

from app.schemas.landing_contract import LandingContract
from scripts.smoke_corpus import _load_simple_yaml
from scripts.smoke_live_multifile_project import _build_pptx_from_text

FORBIDDEN_TEAM_NAMES = (
    "Посты Telegram",
    "Из Telegram",
    "Qdrant Cloud",
    "Google Colab",
)


def _load_pptx_only_config(project_slug: str) -> dict:
    expected_path = DEFAULT_CORPUS / project_slug / "expected_contract.yml"
    if not expected_path.is_file():
        return {"must_have_team": False, "min_team": 0}
    expected = _load_simple_yaml(expected_path)
    pptx_cfg = expected.get("pptx_only") or {}
    if isinstance(pptx_cfg, dict):
        return pptx_cfg
    return {"must_have_team": False, "min_team": 0}


def _prepare_pptx(project_slug: str) -> tuple[str, Path]:
    sources_dir = DEFAULT_CORPUS / project_slug / "sources"
    snapshot = sources_dir / "01_presentation.pptx.txt"
    binary = sources_dir / "01_presentation.pptx"
    if binary.is_file():
        return binary.name, binary
    if snapshot.is_file():
        tmp = Path(tempfile.mkdtemp(prefix="pptx_only_smoke_"))
        out = tmp / "01_presentation.pptx"
        _build_pptx_from_text(snapshot.read_text(encoding="utf-8"), out)
        return out.name, out
    raise FileNotFoundError(f"No PPTX source in {sources_dir}")


def run_smoke(backend_url: str, project_slug: str, project_name: str) -> int:
    cfg = _load_pptx_only_config(project_slug)
    must_have = bool(cfg.get("must_have_team"))
    min_team = int(cfg.get("min_team") or (3 if must_have else 0))
    reason = str(cfg.get("reason") or "")
    expected_names = cfg.get("expected_team_names") or []

    filename, pptx_path = _prepare_pptx(project_slug)
    base = backend_url.rstrip("/")
    api = f"{base}/api/v1"
    errors: list[str] = []

    with httpx.Client(timeout=120.0, trust_env=False) as client:
        create_resp = client.post(
            f"{api}/projects",
            json={"name": project_name, "description": "pptx-only team smoke"},
        )
        if create_resp.status_code != 201:
            print(f"FAIL: create HTTP {create_resp.status_code}", file=sys.stderr)
            return 1
        project_id = create_resp.json()["id"]

        upload_resp = client.post(
            f"{api}/projects/{project_id}/upload",
            files=[("files", (filename, pptx_path.read_bytes(), "application/octet-stream"))],
        )
        if upload_resp.status_code != 200:
            print(f"FAIL: upload HTTP {upload_resp.status_code}", file=sys.stderr)
            return 1

        contract_resp = client.get(f"{api}/projects/{project_id}/contract")
        evidence_resp = client.get(f"{api}/projects/{project_id}/evidence-report")
        client.post(f"{api}/projects/{project_id}/generate", json={"mode": "stub"})
        export_resp = client.get(
            f"{api}/projects/{project_id}/export/html",
            params={"theme": "university_platform"},
        )

    contract = LandingContract.model_validate(contract_resp.json())
    team = contract.fidelity.team_structured if contract.fidelity else []
    team_count = len(team)
    html = export_resp.json().get("html") or ""

    if not must_have:
        print(f"PPTX-only smoke: team not required ({reason or 'config'})")
        print(f"  project_id={project_id} team_count={team_count}")
        if team_count > 0:
            print("  WARN: unexpected team extracted from PPTX-only")
        return 0

    if team_count < min_team:
        errors.append(f"team_count={team_count} < min_team={min_team}")
    if "id='team'" not in html and 'id="team"' not in html:
        errors.append("export missing section#team")
    if "team-card" not in html:
        errors.append("export missing team-card")
    for frag in expected_names:
        if not any(frag.lower() in m.name.lower() for m in team):
            errors.append(f"expected team name missing: {frag}")
    for forbidden in FORBIDDEN_TEAM_NAMES:
        if f"<h3>{forbidden}</h3>" in html:
            errors.append(f"forbidden team-card: {forbidden}")

    if evidence_resp.status_code == 200:
        ev = evidence_resp.json()
        team_view = (ev.get("field_sources") or {}).get("team")
        if team_view:
            print(f"  evidence team coverage={team_view.get('coverage')}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print(f"OK: pptx-only team smoke for {project_slug}")
    print(f"  project_id={project_id} team_count={team_count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PPTX-only team live smoke")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--corpus-project", default="indlab_telegram_news")
    parser.add_argument("--project-name", default="PPTX-only team smoke")
    args = parser.parse_args()
    try:
        return run_smoke(args.backend_url, args.corpus_project, args.project_name)
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
