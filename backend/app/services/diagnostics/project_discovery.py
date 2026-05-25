"""Resolve project_id and backend_url for live diagnostic CLI."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.services.diagnostics.last_project_tracker import (
    LAST_PROJECT_FILE,
    repo_runtime_dir,
)

DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"
BACKEND_UNAVAILABLE_HINT = "Backend unavailable. Run .\\scripts\\start_dev.ps1"
NO_USER_PROJECT_HINT = (
    "No user project with uploaded sources found. Upload files via UI first."
)
NO_CURRENT_USER_PROJECT_HINT = (
    "No current user project with uploaded sources found. Upload files via UI first."
)
LIST_PROJECTS_LIMIT = 100

TECHNICAL_NAME_PHRASES = (
    "dynamic port",
    "api test",
    "health check",
)

TECHNICAL_NAME_TOKENS = (
    "cors",
    "smoke",
    "health",
    "test",
)


@dataclass
class SkippedProject:
    name: str
    source_count: int
    reason: str = "empty"


@dataclass
class ProjectMaterialSummary:
    project_id: str
    project_name: str | None = None
    source_count: int = 0
    evidence_count: int = 0
    filenames: list[str] = field(default_factory=list)
    has_contract: bool = False
    has_extraction: bool = False
    has_uploads: bool = False


@dataclass
class ResolvedProject:
    project_id: str
    backend_url: str
    discovery_mode: str
    project_name: str | None = None
    source_count: int = 0
    filenames: list[str] = field(default_factory=list)
    skipped_projects: list[SkippedProject] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected_current: ProjectMaterialSummary | None = None

    @property
    def source(self) -> str:
        """Backward-compatible alias for discovery_mode."""
        return self.discovery_mode


class ProjectDiscoveryError(Exception):
    """User-facing project resolution failure."""


def default_runtime_root() -> Path:
    """Repo root (Lend/) from backend package layout."""
    return Path(__file__).resolve().parents[4]


def is_technical_project_name(name: str | None) -> bool:
    if not name:
        return False
    lower = name.lower()
    if any(phrase in lower for phrase in TECHNICAL_NAME_PHRASES):
        return True
    return any(re.search(rf"\b{re.escape(token)}\b", lower) for token in TECHNICAL_NAME_TOKENS)


def project_has_materials(summary: ProjectMaterialSummary) -> bool:
    return (
        summary.source_count > 0
        or bool(summary.filenames)
        or summary.evidence_count > 0
        or summary.has_extraction
        or summary.has_uploads
        or summary.has_contract
    )


def is_user_project_candidate(summary: ProjectMaterialSummary) -> bool:
    if is_technical_project_name(summary.project_name):
        return False
    return project_has_materials(summary)


def format_discovery_banner(resolved: ResolvedProject) -> str:
    lines: list[str] = []

    if resolved.rejected_current is not None:
        rejected = resolved.rejected_current
        rejected_label = rejected.project_name or rejected.project_id
        lines.append("WARNING:")
        lines.append(
            "Current project from .runtime/last_project.json is not a user project:"
        )
        lines.append(f"- name: {rejected_label}")
        lines.append(f"- id: {rejected.project_id}")
        lines.append(f"- source_count: {rejected.source_count}")
        lines.append(f"- filenames: {rejected.filenames}")
        lines.append("")
        lines.append("Fallback:")
        lines.append("Using latest user project:")
    elif resolved.warnings:
        for warning in resolved.warnings:
            lines.append(warning)
        lines.append("")

    if resolved.skipped_projects and resolved.discovery_mode in ("latest", "latest_any"):
        lines.append("Skipped technical/empty projects:")
        for skip in resolved.skipped_projects:
            lines.append(f"- {skip.name}: source_count={skip.source_count}")
        lines.append("")

    label = resolved.project_name or resolved.project_id
    if resolved.rejected_current is None and not resolved.warnings:
        lines.append("Resolved project:")
    lines.append(f"- name: {label}")
    lines.append(f"- id: {resolved.project_id}")
    lines.append(f"- source_count: {resolved.source_count}")
    lines.append(f"- filenames: {resolved.filenames}")
    return "\n".join(lines)


def get_backend_url_from_runtime(runtime_root: Path | None = None) -> str:
    root = runtime_root or default_runtime_root()
    path = repo_runtime_dir(root) / "ports.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            url = data.get("backend_url")
            if url:
                return str(url).rstrip("/")
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_BACKEND_URL


def get_last_project_from_runtime(
    runtime_root: Path | None = None,
) -> tuple[str | None, str | None]:
    root = runtime_root or default_runtime_root()
    path = repo_runtime_dir(root) / LAST_PROJECT_FILE
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pid = data.get("project_id")
        name = data.get("project_name")
        return (str(pid) if pid else None), (str(name) if name else None)
    except (json.JSONDecodeError, OSError):
        return None, None


def get_project_id_from_runtime(runtime_root: Path | None = None) -> str | None:
    project_id, _ = get_last_project_from_runtime(runtime_root)
    return project_id


def check_backend_available(backend_url: str, timeout: float = 5.0) -> bool:
    base = backend_url.rstrip("/")
    probe_urls = (
        f"{base}/api/v1/projects/privacy",
        f"{base}/docs",
        f"{base}/api/v1/projects?limit=1",
    )
    try:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            for url in probe_urls:
                try:
                    resp = client.get(url)
                    if resp.status_code < 500:
                        return True
                except httpx.HTTPError:
                    continue
    except httpx.HTTPError:
        return False
    return False


def list_projects_from_api(
    base_url: str,
    *,
    limit: int = LIST_PROJECTS_LIMIT,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    api = f"{base_url.rstrip('/')}/api/v1/projects"
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        resp = client.get(api, params={"limit": limit, "sort": "updated_desc"})
        if resp.status_code != 200:
            return []
        items = resp.json()
        return items if isinstance(items, list) else []


def _material_summary_from_filesystem(
    data_dir: Path,
    project_id: str,
    project_name: str | None,
) -> ProjectMaterialSummary:
    summary = ProjectMaterialSummary(project_id=project_id, project_name=project_name)
    uploads = data_dir / "uploads" / project_id
    if uploads.is_dir():
        names = [p.name for p in uploads.iterdir() if p.is_file()]
        summary.has_uploads = bool(names)
        if names and not summary.filenames:
            summary.filenames = sorted(names)
            summary.source_count = max(summary.source_count, len(names))
    extraction_path = data_dir / "extractions" / f"{project_id}.json"
    if extraction_path.is_file():
        summary.has_extraction = True
        try:
            raw = json.loads(extraction_path.read_text(encoding="utf-8"))
            files = raw.get("files") or []
            file_names = [f.get("filename", "") for f in files if f.get("filename")]
            if file_names:
                summary.filenames = sorted(set(summary.filenames + file_names))
                summary.source_count = max(summary.source_count, len(summary.filenames))
        except (json.JSONDecodeError, OSError):
            pass
    return summary


def fetch_project_material_summary(
    client: httpx.Client,
    base_url: str,
    project_id: str,
    project_name: str | None,
    *,
    data_dir: Path | None = None,
) -> ProjectMaterialSummary:
    summary = ProjectMaterialSummary(project_id=project_id, project_name=project_name)
    api = f"{base_url.rstrip('/')}/api/v1/projects/{project_id}"

    project_resp = client.get(api)
    if project_resp.status_code == 404:
        return summary
    if project_resp.status_code == 200:
        summary.project_name = project_resp.json().get("name") or summary.project_name

    evidence_resp = client.get(f"{api}/evidence-report")
    if evidence_resp.status_code == 200:
        evidence = evidence_resp.json()
        summary.source_count = int(evidence.get("source_count") or 0)
        summary.evidence_count = int(evidence.get("evidence_count") or 0)
        sources = evidence.get("sources") or []
        summary.filenames = [
            str(s.get("filename", "")) for s in sources if s.get("filename")
        ]

    contract_resp = client.get(f"{api}/contract")
    if contract_resp.status_code == 200:
        summary.has_contract = True
        contract = contract_resp.json()
        fidelity = contract.get("fidelity") or {}
        if not summary.source_count:
            summary.source_count = int(fidelity.get("source_count") or 0)
        if not summary.filenames and summary.source_count:
            traces = fidelity.get("field_sources") or []
            summary.filenames = sorted(
                {
                    str(t.get("source_filename"))
                    for t in traces
                    if t.get("source_filename")
                }
            )

    if data_dir is not None:
        fs_summary = _material_summary_from_filesystem(data_dir, project_id, project_name)
        summary.has_uploads = summary.has_uploads or fs_summary.has_uploads
        summary.has_extraction = summary.has_extraction or fs_summary.has_extraction
        if not summary.source_count:
            summary.source_count = fs_summary.source_count
        if not summary.filenames:
            summary.filenames = fs_summary.filenames

    return summary


def _skip_reason(summary: ProjectMaterialSummary) -> str:
    if is_technical_project_name(summary.project_name):
        return "technical_name"
    return "empty"


def get_latest_project_id(
    base_url: str,
    *,
    data_dir: Path | None = None,
    timeout: float = 30.0,
    user_projects_only: bool = True,
) -> tuple[str, str | None, list[SkippedProject], ProjectMaterialSummary | None]:
    """Return (project_id, project_name, skipped, material_summary)."""
    items = list_projects_from_api(base_url, timeout=timeout)
    skipped: list[SkippedProject] = []

    if items:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            for item in items:
                pid = str(item["id"])
                name = item.get("name")
                summary = fetch_project_material_summary(
                    client,
                    base_url,
                    pid,
                    name,
                    data_dir=data_dir,
                )
                if not user_projects_only:
                    return pid, name, skipped, summary
                if is_user_project_candidate(summary):
                    return pid, name, skipped, summary
                skipped.append(
                    SkippedProject(
                        name=name or pid,
                        source_count=summary.source_count,
                        reason=_skip_reason(summary),
                    )
                )
        if user_projects_only:
            raise ProjectDiscoveryError(NO_USER_PROJECT_HINT)
        raise ProjectDiscoveryError("No projects found. Create a project via UI upload first.")

    if data_dir is not None:
        pid = _latest_from_filesystem(data_dir)
        if pid:
            name = _project_name_from_filesystem(data_dir, pid)
            fs_summary = _material_summary_from_filesystem(data_dir, pid, name)
            if not user_projects_only or is_user_project_candidate(fs_summary):
                return pid, name, skipped, fs_summary
            if user_projects_only:
                raise ProjectDiscoveryError(NO_USER_PROJECT_HINT)

    raise ProjectDiscoveryError("No projects found. Create a project via UI upload first.")


def _project_name_from_filesystem(data_dir: Path, project_id: str) -> str | None:
    index = data_dir / "projects.json"
    if not index.is_file():
        return None
    try:
        raw = json.loads(index.read_text(encoding="utf-8"))
        item = raw.get(project_id)
        if item:
            return item.get("name")
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _latest_from_filesystem(data_dir: Path) -> str | None:
    index = data_dir / "projects.json"
    if not index.is_file():
        return None
    try:
        raw = json.loads(index.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not raw:
        return None

    def _sort_key(item: dict[str, Any]) -> datetime:
        for field_name in ("updated_at", "created_at"):
            value = item.get(field_name)
            if value:
                try:
                    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
        return datetime.min.replace(tzinfo=timezone.utc)

    best_id = max(raw.items(), key=lambda kv: _sort_key(kv[1]))[0]
    return best_id


def _build_resolved_from_summary(
    *,
    backend: str,
    discovery_mode: str,
    project_id: str,
    project_name: str | None,
    summary: ProjectMaterialSummary | None,
    skipped: list[SkippedProject] | None = None,
    warnings: list[str] | None = None,
    rejected_current: ProjectMaterialSummary | None = None,
) -> ResolvedProject:
    return ResolvedProject(
        project_id=project_id,
        backend_url=backend,
        discovery_mode=discovery_mode,
        project_name=project_name,
        source_count=summary.source_count if summary else 0,
        filenames=list(summary.filenames) if summary else [],
        skipped_projects=list(skipped or []),
        warnings=list(warnings or []),
        rejected_current=rejected_current,
    )


def _resolve_current_project(
    backend: str,
    root: Path,
    data_dir: Path | None,
    timeout: float = 30.0,
) -> ResolvedProject:
    runtime_pid, runtime_name = get_last_project_from_runtime(root)

    if not runtime_pid:
        pid, name, skipped, summary = get_latest_project_id(
            backend,
            data_dir=data_dir,
            timeout=timeout,
            user_projects_only=True,
        )
        return _build_resolved_from_summary(
            backend=backend,
            discovery_mode="latest",
            project_id=pid,
            project_name=name,
            summary=summary,
            skipped=skipped,
            warnings=[
                "WARNING:",
                "No .runtime/last_project.json found.",
                "Using latest user project:",
            ],
        )

    with httpx.Client(timeout=timeout, trust_env=False) as client:
        summary = fetch_project_material_summary(
            client,
            backend,
            runtime_pid,
            runtime_name,
            data_dir=data_dir,
        )

    if is_user_project_candidate(summary):
        return _build_resolved_from_summary(
            backend=backend,
            discovery_mode="current",
            project_id=runtime_pid,
            project_name=summary.project_name or runtime_name,
            summary=summary,
        )

    try:
        pid, name, skipped, fallback_summary = get_latest_project_id(
            backend,
            data_dir=data_dir,
            timeout=timeout,
            user_projects_only=True,
        )
    except ProjectDiscoveryError as exc:
        if str(exc) == NO_USER_PROJECT_HINT:
            raise ProjectDiscoveryError(NO_CURRENT_USER_PROJECT_HINT) from exc
        raise

    return _build_resolved_from_summary(
        backend=backend,
        discovery_mode="fallback_from_current",
        project_id=pid,
        project_name=name,
        summary=fallback_summary,
        skipped=skipped,
        rejected_current=summary,
    )


def resolve_project_id(
    *,
    project_id: str | None = None,
    latest: bool = False,
    latest_any: bool = False,
    current: bool = False,
    base_url: str | None = None,
    runtime_root: Path | None = None,
    data_dir: Path | None = None,
) -> ResolvedProject:
    root = runtime_root or default_runtime_root()
    backend = (base_url or get_backend_url_from_runtime(root)).rstrip("/")

    if not check_backend_available(backend):
        raise ProjectDiscoveryError(BACKEND_UNAVAILABLE_HINT)

    if latest and latest_any:
        raise ProjectDiscoveryError("Use only one of --latest or --latest-any.")

    if project_id:
        return ResolvedProject(
            project_id=project_id.strip(),
            backend_url=backend,
            discovery_mode="explicit",
        )

    user_only = not latest_any

    if latest or latest_any:
        pid, name, skipped, summary = get_latest_project_id(
            backend,
            data_dir=data_dir,
            user_projects_only=user_only,
        )
        mode = "latest_any" if latest_any else "latest"
        return _build_resolved_from_summary(
            backend=backend,
            discovery_mode=mode,
            project_id=pid,
            project_name=name,
            summary=summary,
            skipped=skipped,
        )

    if current:
        return _resolve_current_project(backend, root, data_dir)

    raise ProjectDiscoveryError(
        "Укажите --project-id UUID, --latest, --latest-any или --current. "
        "Пример: python scripts/check_live_project_verdict.py --latest"
    )
