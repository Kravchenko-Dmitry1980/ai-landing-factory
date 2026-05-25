"""Tests for PII TTL cleanup."""

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.config import Settings
from app.services.pii.cleanup import cleanup_expired_pii_reports


def test_cleanup_removes_expired_reports(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        pii_cleanup_enabled=True,
    )
    reports_dir = settings.pii_reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    expired = {
        "project_id": str(uuid4()),
        "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    }
    fresh = {
        "project_id": str(uuid4()),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }
    (reports_dir / "expired.json").write_text(json.dumps(expired), encoding="utf-8")
    (reports_dir / "fresh.json").write_text(json.dumps(fresh), encoding="utf-8")

    deleted, _artifacts = cleanup_expired_pii_reports(settings)
    assert deleted == 1
    assert (reports_dir / "fresh.json").exists()
    assert not (reports_dir / "expired.json").exists()


def test_cleanup_disabled(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        pii_cleanup_enabled=False,
    )
    reports_dir = settings.pii_reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "old.json").write_text("{}", encoding="utf-8")
    deleted, _ = cleanup_expired_pii_reports(settings)
    assert deleted == 0
    assert (reports_dir / "old.json").exists()
