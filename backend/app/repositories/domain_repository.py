"""Domain intelligence report persistence."""

import logging

from uuid import UUID

import aiofiles

from app.config import Settings
from app.schemas.domain_intelligence import DomainIntelligenceReport, ProjectKnowledgeGraph

logger = logging.getLogger(__name__)


class DomainRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._settings.domain_reports_dir.mkdir(parents=True, exist_ok=True)
        self._settings.knowledge_graphs_dir.mkdir(parents=True, exist_ok=True)

    def _report_path(self, project_id: UUID) -> str:
        return str(self._settings.domain_reports_dir / f"{project_id}.domain.json")

    def _graph_path(self, project_id: UUID) -> str:
        return str(self._settings.knowledge_graphs_dir / f"{project_id}.kg.json")

    async def save_report(self, report: DomainIntelligenceReport) -> None:
        async with aiofiles.open(self._report_path(report.project_id), "w", encoding="utf-8") as f:
            await f.write(report.model_dump_json(indent=2))
        logger.info("Domain report saved for project %s", report.project_id)

    async def get_report(self, project_id: UUID) -> DomainIntelligenceReport | None:
        path = self._report_path(project_id)
        try:
            async with aiofiles.open(path, encoding="utf-8") as f:
                raw = await f.read()
        except FileNotFoundError:
            return None
        return DomainIntelligenceReport.model_validate_json(raw)

    async def save_knowledge_graph(self, graph: ProjectKnowledgeGraph) -> None:
        async with aiofiles.open(self._graph_path(graph.project_id), "w", encoding="utf-8") as f:
            await f.write(graph.model_dump_json(indent=2))

    async def get_knowledge_graph(self, project_id: UUID) -> ProjectKnowledgeGraph | None:
        path = self._graph_path(project_id)
        try:
            async with aiofiles.open(path, encoding="utf-8") as f:
                raw = await f.read()
        except FileNotFoundError:
            report = await self.get_report(project_id)
            return report.graph if report else None
        return ProjectKnowledgeGraph.model_validate_json(raw)
