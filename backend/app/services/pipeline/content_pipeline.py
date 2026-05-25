import logging
from uuid import UUID

from app.repositories.contract_repository import ContractRepository
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.extraction.base import DocumentExtractor
from app.services.generation.stub_generator import StubGenerationService
from app.services.pipeline.pii_stage import PIIStageService

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    content-first orchestration:
    files → extraction → PII prescan → LandingContract → generation → landing artifact
    """

    def __init__(
        self,
        extractor: DocumentExtractor,
        contract_builder: ContractBuilderService,
        generator: StubGenerationService,
        repository: ContractRepository,
        pii_stage: PIIStageService | None = None,
    ) -> None:
        self._extractor = extractor
        self._builder = contract_builder
        self._generator = generator
        self._repo = repository
        self._pii = pii_stage

    async def run_after_upload(self, project_id: UUID) -> dict | None:
        extraction = await self._extractor.extract(project_id)
        await self._repo.save_extraction(extraction)

        pii_summary = None
        if self._pii:
            try:
                report, summary = await self._pii.prescan(extraction)
                await self._repo.save_pii_report(report)
                pii_summary = summary.model_dump()
            except Exception as exc:
                logger.warning("PII prescan after upload failed: %s", exc)

        await self._builder.build_and_save(extraction)
        await self._generator.generate(project_id)
        logger.info("Pipeline completed for project %s", project_id)
        return pii_summary
