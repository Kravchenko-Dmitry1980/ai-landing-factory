"""Algofusion export HTML must contain key facts from the DOCX."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.generation import GeneratedLanding, LandingBlockContent
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.export.wow.wow_exporter import WowExportOptions, WowHtmlExporter

FIXTURE = Path(__file__).parent / "fixtures" / "algofusion_landing.txt"

REQUIRED_SNIPPETS = [
    "ООО «АлгоФьюжн»",
    "YOLO v11 nano",
    "ByteTrack",
    "Random Forest",
    "Compliance Engine",
    "CASHIER WATCH",
    "mAP50 = 0.956",
    "95.12%",
    "97%",
    "Кус",
    "Кривонос Вадим",
    "Гречко Алёна",
    "Семин Алексей",
    "цифровой паспорт",
]


def _build_contract_and_landing():
    text = FIXTURE.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="Лендинг_АлгоФьюжн_CV.docx",
                file_type="docx",
                extracted_text=text,
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )
    builder = ContractBuilderService(ContractRepository(settings))
    contract = builder.build(extraction)
    landing = GeneratedLanding(
        project_id=contract.project_id,
        style=contract.style,
        blocks=[
            LandingBlockContent(
                key=b.key,
                title=b.title,
                body=b.content or (b.bullets[0] if b.bullets else ""),
                bullets=list(b.bullets),
            )
            for b in contract.blocks
        ],
        generated_at=datetime.now(timezone.utc),
        prompt_version="test-algofusion",
    )
    return contract, landing


class _Repo:
    def __init__(self, contract, landing) -> None:
        self._contract = contract
        self._landing = landing

    async def get_contract(self, _pid):
        return self._contract

    async def get_landing(self, _pid):
        return self._landing


def test_algofusion_standard_html_contains_key_facts() -> None:
    contract, landing = _build_contract_and_landing()
    html = asyncio.run(
        StyledHtmlExporter(_Repo(contract, landing)).to_html(
            contract.project_id,
            theme=ExportTheme.UNIVERSITY_PLATFORM,
        )
    )
    missing = [s for s in REQUIRED_SNIPPETS if s not in html]
    assert missing == [], f"Missing in Standard HTML: {missing}"


def test_algofusion_wow_html_contains_key_facts() -> None:
    contract, landing = _build_contract_and_landing()
    html = asyncio.run(
        WowHtmlExporter(_Repo(contract, landing)).to_html(
            contract.project_id,
            options=WowExportOptions(),
        )
    )
    for snippet in (
        "АлгоФьюжн",
        "YOLO",
        "ByteTrack",
        "CASHIER WATCH",
        "Кривонос",
        "цифровой паспорт",
    ):
        assert snippet in html
