"""Optional Fernet encryption for full PII reports on disk."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from app.schemas.pii import PIIReportFull, StoragePolicy

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)

_ENCRYPTION_PREFIX = "FERNET:"


def build_storage_policy(settings: Settings) -> StoragePolicy:
    encrypt = settings.pii_encrypt_reports and bool(settings.pii_encryption_key)
    if settings.pii_encrypt_reports and not settings.pii_encryption_key:
        logger.warning(
            "PII_ENCRYPT_REPORTS=true but PII_ENCRYPTION_KEY missing — encryption disabled"
        )
    return StoragePolicy(
        ttl_hours=settings.pii_report_ttl_hours,
        encrypt_reports=encrypt,
        raw_pii_logging=settings.pii_audit_log_originals,
        cleanup_enabled=settings.pii_cleanup_enabled,
        storage_paths=[
            str(settings.pii_reports_dir),
            str(settings.pii_safe_payloads_dir),
        ],
    )


def _get_fernet(settings: Settings):
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.warning("cryptography not installed — PII report encryption disabled")
        return None
    key = settings.pii_encryption_key
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        logger.warning("Invalid PII_ENCRYPTION_KEY: %s", exc)
        return None


def encrypt_report_json(settings: Settings, payload: str) -> str:
    fernet = _get_fernet(settings)
    if not fernet or not settings.pii_encrypt_reports:
        return payload
    token = fernet.encrypt(payload.encode("utf-8")).decode("ascii")
    return _ENCRYPTION_PREFIX + token


def decrypt_report_json(settings: Settings, raw: str) -> str:
    if not raw.startswith(_ENCRYPTION_PREFIX):
        return raw
    fernet = _get_fernet(settings)
    if not fernet:
        raise ValueError("Encrypted PII report but encryption key unavailable")
    token = raw[len(_ENCRYPTION_PREFIX) :]
    return fernet.decrypt(token.encode("ascii")).decode("utf-8")


def serialize_full_report(settings: Settings, report: PIIReportFull) -> str:
    return encrypt_report_json(settings, report.model_dump_json(indent=2))


def parse_full_report(settings: Settings, raw: str) -> PIIReportFull:
    plain = decrypt_report_json(settings, raw)
    return PIIReportFull.model_validate_json(plain)
