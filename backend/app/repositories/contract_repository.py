import logging

from uuid import UUID



import aiofiles



from app.config import Settings

from app.schemas.extraction import ExtractionResult

from app.schemas.generation import GeneratedLanding

from app.schemas.landing_contract import LandingContract

from app.schemas.pii import PIIReportFull

from app.schemas.semantic_generation import GeneratedSemanticLanding

from app.services.pii.storage import parse_full_report, serialize_full_report



logger = logging.getLogger(__name__)





class ContractRepository:

    def __init__(self, settings: Settings) -> None:

        self._settings = settings

        self._settings.pii_reports_dir.mkdir(parents=True, exist_ok=True)

        self._settings.pii_safe_payloads_dir.mkdir(parents=True, exist_ok=True)



    def _contract_path(self, project_id: UUID) -> str:

        return str(self._settings.contracts_dir / f"{project_id}.json")



    def _extraction_path(self, project_id: UUID) -> str:

        return str(self._settings.extractions_dir / f"{project_id}.json")



    def _landing_path(self, project_id: UUID) -> str:

        return str(self._settings.contracts_dir / f"{project_id}.landing.json")



    def _semantic_path(self, project_id: UUID) -> str:

        return str(self._settings.contracts_dir / f"{project_id}.semantic.json")



    def _pii_report_path(self, project_id: UUID) -> str:

        return str(self._settings.pii_reports_dir / f"{project_id}.json")



    async def save_extraction(self, result: ExtractionResult) -> None:

        async with aiofiles.open(

            self._extraction_path(result.project_id), "w", encoding="utf-8"

        ) as f:

            await f.write(result.model_dump_json(indent=2))



    async def get_extraction(self, project_id: UUID) -> ExtractionResult | None:

        path = self._extraction_path(project_id)

        try:

            async with aiofiles.open(path, encoding="utf-8") as f:

                raw = await f.read()

        except FileNotFoundError:

            return None

        return ExtractionResult.model_validate_json(raw)



    async def save_contract(self, contract: LandingContract) -> None:

        async with aiofiles.open(

            self._contract_path(contract.project_id), "w", encoding="utf-8"

        ) as f:

            await f.write(contract.model_dump_json(indent=2))

        logger.info("Contract saved for project %s", contract.project_id)



    async def get_contract(self, project_id: UUID) -> LandingContract | None:

        path = self._contract_path(project_id)

        try:

            async with aiofiles.open(path, encoding="utf-8") as f:

                raw = await f.read()

        except FileNotFoundError:

            return None

        return LandingContract.model_validate_json(raw)



    async def save_landing(self, landing: GeneratedLanding) -> None:

        async with aiofiles.open(

            self._landing_path(landing.project_id), "w", encoding="utf-8"

        ) as f:

            await f.write(landing.model_dump_json(indent=2))



    async def get_landing(self, project_id: UUID) -> GeneratedLanding | None:

        path = self._landing_path(project_id)

        try:

            async with aiofiles.open(path, encoding="utf-8") as f:

                raw = await f.read()

        except FileNotFoundError:

            return None

        return GeneratedLanding.model_validate_json(raw)



    async def save_semantic(self, semantic: GeneratedSemanticLanding) -> None:

        async with aiofiles.open(

            self._semantic_path(semantic.project_id), "w", encoding="utf-8"

        ) as f:

            await f.write(semantic.model_dump_json(indent=2))



    async def get_semantic(self, project_id: UUID) -> GeneratedSemanticLanding | None:

        path = self._semantic_path(project_id)

        try:

            async with aiofiles.open(path, encoding="utf-8") as f:

                raw = await f.read()

        except FileNotFoundError:

            return None

        return GeneratedSemanticLanding.model_validate_json(raw)



    async def save_pii_report(self, report: PIIReportFull) -> None:

        payload = serialize_full_report(self._settings, report)

        async with aiofiles.open(

            self._pii_report_path(report.project_id), "w", encoding="utf-8"

        ) as f:

            await f.write(payload)



    async def get_pii_report(self, project_id: UUID) -> PIIReportFull | None:

        path = self._pii_report_path(project_id)

        try:

            async with aiofiles.open(path, encoding="utf-8") as f:

                raw = await f.read()

        except FileNotFoundError:

            return None

        return parse_full_report(self._settings, raw)

