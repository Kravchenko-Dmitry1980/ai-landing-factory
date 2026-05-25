import logging

from uuid import UUID



logger = logging.getLogger("pii.audit")





def log_pii_audit(

    *,

    event: str,

    project_id: UUID,

    privacy_mode: str,

    redaction_count: int = 0,

    entity_types: list[str] | None = None,

    has_pii: bool = False,

    risk_level: str = "low",

    cloud_sent: bool = False,

    cloud_provider: str | None = None,

    fallback: bool = False,

    payload_chars: int = 0,

    detectors_used: str = "",

    safe_for_cloud: bool = False,

) -> None:

    """

    Production-safe audit: never log original PII values.

    """

    logger.info(

        "pii_audit event=%s project_id=%s mode=%s has_pii=%s redactions=%d "

        "types=%s risk=%s cloud_sent=%s provider=%s fallback=%s payload_chars=%d "

        "detectors=%s safe_for_cloud=%s",

        event,

        project_id,

        privacy_mode,

        has_pii,

        redaction_count,

        ",".join(entity_types or []),

        risk_level,

        cloud_sent,

        cloud_provider or "-",

        fallback,

        payload_chars,

        detectors_used or "-",

        safe_for_cloud,

    )

