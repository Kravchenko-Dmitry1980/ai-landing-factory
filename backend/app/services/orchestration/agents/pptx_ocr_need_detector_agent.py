"""PPTX team text-layer diagnostic agent."""

from __future__ import annotations

from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.orchestration import AgentFinding, AgentResult, AgentRunStatus
from app.services.contract_fidelity.pptx_team_markers import (
    iter_pptx_slides,
    matched_team_markers,
    slide_title_has_team_marker,
    text_has_team_markers,
)
from app.services.evidence.people_extractor import extract_people_from_text

PPTX_TEAM_TEXT_MISSING = (
    "PPTX не содержит извлекаемого текста команды. "
    "Возможно, команда находится на изображении. Загрузите DOCX/TXT или включите OCR."
)
POSSIBLE_IMAGE_ONLY = "possible_image_only_team_slide"


class PptxOcrNeedDetectorAgent:
    """Detect PPTX files where team is expected but not extractable from text layer."""

    name = "pptx_ocr_need_detector_agent"

    def run(self, extraction: ExtractionResult) -> AgentResult:
        findings: list[AgentFinding] = []
        warnings: list[str] = []
        metrics: dict[str, int | bool] = {}
        docx_has_team_source = _extraction_has_team_doc(extraction)

        for file in extraction.files:
            if file.file_type != "pptx":
                continue
            text = (file.extracted_text or "").strip()
            if not text:
                warnings.append(PPTX_TEAM_TEXT_MISSING)
                findings.append(
                    AgentFinding(
                        agent_name=self.name,
                        field_name="team",
                        filename=file.filename,
                        source_id=file.filename,
                        status=AgentRunStatus.WARNING,
                        reason="empty_pptx_text",
                    )
                )
                continue

            markers = matched_team_markers(text)
            people = extract_people_from_text(
                text,
                source_ref=file.filename,
                section_hint="",
                in_team_section=text_has_team_markers(text),
            )
            slides = iter_pptx_slides(text)
            team_slides = [
                s for s in slides if slide_title_has_team_marker(s[2], s[1])
            ]
            low_text_slides = [
                s for s in slides if len(s[1].strip()) < 80
            ]

            metrics[f"{file.filename}_team_markers"] = len(markers)
            metrics[f"{file.filename}_people"] = len(people)
            metrics[f"{file.filename}_team_slides"] = len(team_slides)

            if markers or team_slides:
                if not people:
                    warnings.append(PPTX_TEAM_TEXT_MISSING)
                    warnings.append(POSSIBLE_IMAGE_ONLY)
                    findings.append(
                        AgentFinding(
                            agent_name=self.name,
                            field_name="team",
                            filename=file.filename,
                            source_id=file.filename,
                            status=AgentRunStatus.WARNING,
                            reason="pptx_team_text_missing",
                            value_preview=f"markers={markers}, team_slides={len(team_slides)}",
                        )
                    )
                else:
                    findings.append(
                        AgentFinding(
                            agent_name=self.name,
                            field_name="team",
                            filename=file.filename,
                            source_id=file.filename,
                            status=AgentRunStatus.OK,
                            reason="pptx_team_text_found",
                            value_preview=f"people={len(people)}",
                            confidence=0.85,
                        )
                    )
            elif not people and not docx_has_team_source:
                warnings.append(PPTX_TEAM_TEXT_MISSING)
                findings.append(
                    AgentFinding(
                        agent_name=self.name,
                        field_name="team",
                        filename=file.filename,
                        source_id=file.filename,
                        status=AgentRunStatus.WARNING,
                        reason="pptx_team_text_missing",
                        value_preview="no extractable team in PPTX text layer",
                    )
                )
            elif not people and len(low_text_slides) >= max(1, len(slides) // 2):
                warnings.append(PPTX_TEAM_TEXT_MISSING)
                warnings.append(POSSIBLE_IMAGE_ONLY)
                findings.append(
                    AgentFinding(
                        agent_name=self.name,
                        field_name="team",
                        filename=file.filename,
                        source_id=file.filename,
                        status=AgentRunStatus.WARNING,
                        reason="possible_image_only_team_slide",
                    )
                )

        status = AgentRunStatus.WARNING if warnings else AgentRunStatus.OK
        if not findings and not any(f.file_type == "pptx" for f in extraction.files):
            status = AgentRunStatus.SKIPPED

        return AgentResult(
            agent_name=self.name,
            status=status,
            findings=findings,
            warnings=list(dict.fromkeys(warnings)),
            metrics=metrics,
        )


def _extraction_has_team_doc(extraction: ExtractionResult) -> bool:
    for file in extraction.files:
        if file.file_type not in ("docx", "txt"):
            continue
        text = (file.extracted_text or "").lower()
        if "команда проекта" in text or "участники команды" in text:
            return True
    return False
