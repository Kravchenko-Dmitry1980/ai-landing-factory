"""Deterministic document extraction orchestrator."""

from __future__ import annotations

import logging

from app.schemas.extraction import ExtractionResult
from app.schemas.orchestration import AgentRunStatus, OrchestrationTrace
from app.services.evidence.group_team_parser import group_expansion_trace
from app.services.orchestration.agents.pptx_ocr_need_detector_agent import (
    PptxOcrNeedDetectorAgent,
)
from app.services.orchestration.agents.team_extraction_agent import TeamExtractionAgent

logger = logging.getLogger(__name__)


class DocumentOrchestrator:
    """Run specialized extraction agents with full trace (no LLM)."""

    def __init__(self) -> None:
        self._pptx_agent = PptxOcrNeedDetectorAgent()
        self._team_agent = TeamExtractionAgent()

    def run(self, extraction: ExtractionResult) -> OrchestrationTrace:
        source_count = len(extraction.files)
        results = [
            self._pptx_agent.run(extraction),
            self._team_agent.run(extraction),
        ]

        global_warnings: list[str] = []
        missing_capabilities: list[str] = []
        team_group_expansions: list[dict[str, str]] = []

        for file in extraction.files:
            text = (file.extracted_text or "").strip()
            if file.file_type in ("docx", "txt") and "команда проекта" in text.lower():
                team_group_expansions.extend(
                    group_expansion_trace(_team_section_slice(text))
                )

        for result in results:
            global_warnings.extend(result.warnings)
            if result.status == AgentRunStatus.WARNING and "ocr" in result.agent_name:
                missing_capabilities.append("ocr")

        global_warnings = list(dict.fromkeys(global_warnings))

        trace = OrchestrationTrace(
            source_count=source_count,
            agents_run=[r.agent_name for r in results],
            results=results,
            global_warnings=global_warnings,
            missing_capabilities=list(dict.fromkeys(missing_capabilities)),
            team_group_expansions=team_group_expansions,
        )
        logger.info(
            "Orchestrator ran %d agents for %d sources, warnings=%d",
            len(results),
            source_count,
            len(global_warnings),
        )
        return trace


def _team_section_slice(text: str) -> str:
    low = text.lower()
    start = low.find("команда проекта")
    if start < 0:
        return ""
    end = low.find("фраза проекта", start)
    return text[start:end if end > 0 else len(text)]
