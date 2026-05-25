"""TTL cleanup for expired PII reports and safe payload artifacts."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from app.services.pii.audit import log_pii_audit

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    now = datetime.now(timezone.utc)
    exp = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    return exp <= now


def _try_read_expires(path: Path) -> datetime | None:
    try:
        raw = path.read_text(encoding="utf-8")
        if raw.startswith("FERNET:"):
            return None
        data = json.loads(raw)
        exp = data.get("expires_at")
        if not exp:
            return None
        return datetime.fromisoformat(exp.replace("Z", "+00:00"))
    except Exception:
        return None


def cleanup_expired_pii_reports(settings: Settings) -> tuple[int, int]:
    """
    Remove expired full reports and stale safe payload previews.
    Returns (deleted_reports, deleted_artifacts).
    """
    if not settings.pii_cleanup_enabled:
        logger.info("PII cleanup disabled (PII_CLEANUP_ENABLED=false)")
        return 0, 0

    deleted_reports = 0
    deleted_artifacts = 0

    reports_dir = settings.pii_reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    for path in reports_dir.glob("*.json"):
        expires_at = _try_read_expires(path)
        if _is_expired(expires_at):
            path.unlink(missing_ok=True)
            deleted_reports += 1

    payloads_dir = settings.pii_safe_payloads_dir
    if payloads_dir.exists():
        for path in payloads_dir.glob("*.json"):
            expires_at = _try_read_expires(path)
            if _is_expired(expires_at):
                path.unlink(missing_ok=True)
                deleted_artifacts += 1

    if deleted_reports or deleted_artifacts:
        log_pii_audit(
            event="pii_cleanup",
            project_id=Path("00000000-0000-0000-0000-000000000000"),
            privacy_mode="-",
            has_pii=False,
            redaction_count=deleted_reports + deleted_artifacts,
        )
        logger.info(
            "PII cleanup: removed %d reports, %d artifacts",
            deleted_reports,
            deleted_artifacts,
        )

    return deleted_reports, deleted_artifacts
