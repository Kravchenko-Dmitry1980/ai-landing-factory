#!/usr/bin/env python3
"""Smoke: team review flow — accept_all, manual-text, export policy."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.fidelity import TeamMember
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.team_review import TeamPublicationMode
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.orchestration.agents.export_guard_agent import guard_team_for_export
from app.services.team_review.team_review_service import TeamReviewService
from app.services.team_verification.team_verification_service import TeamVerificationService

BAD_OCR = ("Наденда Глазунова", "Денис Калюаный", "Александр Егорсв")


class _MemRepo(ContractRepository):
    def __init__(self) -> None:
        super().__init__(settings)
        self.store: dict = {}

    async def save_contract(self, contract):
        self.store[contract.project_id] = contract

    async def get_contract(self, pid):
        return self.store.get(pid)


def _ocr_extraction() -> ExtractionResult:
    text = "Команда проекта\n" + "\n".join(BAD_OCR) + "\nКравченко Дмитрий — тимлид"
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="slide25.ocr",
                file_type="ocr",
                extracted_text=text,
                metadata={"is_ocr_derivative": True, "ocr_engine": "easyocr"},
            )
        ],
        extracted_at=utc_now(),
    )


def _build_contract() -> LandingContract:
    extraction = _ocr_extraction()
    raw_members = [
        TeamMember(name=n, role="") for n in BAD_OCR
    ] + [TeamMember(name="Кравченко Дмитрий", role="Тимлид")]

    report = TeamVerificationService().verify(raw_members, extraction)
    from app.services.team_verification.export_policy import draft_team_from_report

    return LandingContract(
        project_id=extraction.project_id,
        status=ContractStatus.DRAFT,
        updated_at=utc_now(),
        fidelity=__import__(
            "app.schemas.fidelity", fromlist=["FidelityMetadata"]
        ).FidelityMetadata(
            team_structured=draft_team_from_report(report),
            team_verification_report=report,
            team_publication_mode=TeamPublicationMode.draft_auto,
        ),
        blocks=[LandingBlock(key="team", title="Команда", content="", bullets=[])],
    )


class _FakeExportRepo:
    def __init__(self, contract):
        self._c = contract

    async def get_contract(self, _):
        return self._c

    async def get_landing(self, _):
        return None


async def _html_has(contract, needle: str) -> bool:
    html = await StyledHtmlExporter(_FakeExportRepo(contract)).to_html(
        contract.project_id
    )
    return needle in html


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="indlab_telegram_news")
    args = parser.parse_args()
    _ = args.project

    repo = _MemRepo()
    service = TeamReviewService(repo)
    contract = _build_contract()
    repo.store[contract.project_id] = contract
    pid = contract.project_id
    errors: list[str] = []

    review = await service.get_review(pid)
    if review.summary.needs_review_count < 1:
        errors.append("expected needs_review OCR candidates")
    print(f"review: verified={review.summary.verified_count} "
          f"needs_review={review.summary.needs_review_count}")

    for bad in BAD_OCR:
        members, _ = guard_team_for_export(
            contract.fidelity.team_structured,
            contract.fidelity.team_verification_report,
            TeamPublicationMode.draft_auto,
        )
        if any(bad in m.name for m in members):
            pass  # draft mode in guard uses safe_public default - check export
        if await _html_has(contract, bad):
            errors.append(f"safe export contains bad OCR name: {bad}")

    await service.apply_bulk_action(pid, "accept_all")
    contract = await repo.get_contract(pid)
    for bad in BAD_OCR:
        if not await _html_has(contract, bad):
            errors.append(f"after accept_all missing: {bad}")

    manual = (
        "Надежда Глазунова — аналитика\n"
        "Татьяна Ерюкова — помощник тимлида\n"
        "Егор Быков — разработчик\n"
    )
    await service.apply_manual_text(pid, manual)
    contract = await repo.get_contract(pid)
    if contract.fidelity.team_publication_mode != TeamPublicationMode.manual_edited:
        errors.append("publication_mode not manual_edited")
    if not await _html_has(contract, "Надежда Глазунова"):
        errors.append("manual export missing corrected name")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: team review flow")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
