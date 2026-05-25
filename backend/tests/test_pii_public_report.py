"""Public PII report must never expose original values."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.config import Settings
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.pipeline.pii_stage import PIIStageService
from app.services.pii.report import to_public_report


def test_public_report_has_no_originals(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        extractions_dir=tmp_path / "data" / "extractions",
        privacy_mode="hybrid_safe",
        enable_pii_detection=True,
    )
    settings.pii_reports_dir.mkdir(parents=True, exist_ok=True)
    stage = PIIStageService(settings)
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(client="ООО Ромашка"),
        files=[
            FileExtraction(
                filename="brief.docx",
                file_type="docx",
                extracted_text=(
                    "Руководитель: Александр Васильевич Древаль\n"
                    "Email: alex.dreval@example.com\n"
                ),
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )
    report, _ = asyncio.run(stage.prescan(extraction))
    public = to_public_report(report)
    dumped = public.model_dump_json()
    assert "alex.dreval@example.com" not in dumped
    assert "alex.dreval" not in dumped.lower()
    for ent in public.entities:
        assert not hasattr(ent, "original") or "original" not in ent.model_dump()
    assert public.detectors_used
    assert public.expires_at is not None
