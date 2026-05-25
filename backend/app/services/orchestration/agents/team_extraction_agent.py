"""Team extraction orchestration agent."""

from __future__ import annotations

from app.schemas.extraction import ExtractionResult
from app.schemas.orchestration import AgentFinding, AgentResult, AgentRunStatus
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.contract_fidelity.team_candidate_validator import filter_team_members
from app.services.evidence.group_team_parser import group_expansion_trace, parse_team_section_group_aware
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.contract_fidelity.pptx_team_markers import text_has_team_markers


class TeamExtractionAgent:
    """Extract and trace team from all doc-like sources."""

    name = "team_extraction_agent"

    def run(self, extraction: ExtractionResult) -> AgentResult:
        findings: list[AgentFinding] = []
        warnings: list[str] = []
        expansions: list[dict[str, str]] = []
        parser = StructuredLandingParser()
        total_people = 0

        for file in extraction.files:
            text = (file.extracted_text or "").strip()
            if not text:
                continue

            members = []
            if file.file_type in ("docx", "txt", "pdf"):
                parsed = parser.parse(text)
                if parsed.team:
                    members = filter_team_members(parsed.team)
                else:
                    team_section = _extract_team_section(text)
                    if team_section:
                        members = parse_team_section_group_aware(team_section)
                        expansions.extend(group_expansion_trace(team_section))
            elif file.file_type == "pptx":
                if text_has_team_markers(text):
                    candidates = extract_people_from_text(
                        text,
                        source_ref=file.filename,
                        in_team_section=True,
                    )
                    from app.schemas.fidelity import TeamMember

                    members = [
                        TeamMember(
                            name=c.name,
                            role=c.role,
                            project_area=c.project_area,
                            contributions=list(c.contributions),
                        )
                        for c in candidates
                    ]
                    members = filter_team_members(members)

            if members:
                total_people += len(members)
                findings.append(
                    AgentFinding(
                        agent_name=self.name,
                        field_name="team",
                        filename=file.filename,
                        source_id=file.filename,
                        status=AgentRunStatus.OK,
                        value_preview=f"{len(members)} members",
                        confidence=0.9,
                        reason="team_extracted",
                    )
                )
            elif file.file_type == "pptx" and text_has_team_markers(text):
                warnings.append(f"team markers in {file.filename} but no people parsed")

        status = AgentRunStatus.OK if total_people else AgentRunStatus.WARNING
        return AgentResult(
            agent_name=self.name,
            status=status,
            findings=findings,
            warnings=warnings,
            metrics={"team_count": total_people, "group_expansions": len(expansions)},
        )


def _extract_team_section(text: str) -> str:
    lower = text.lower()
    start = lower.find("команда проекта")
    if start < 0:
        return ""
    end = lower.find("фраза проекта", start)
    if end < 0:
        end = len(text)
    return text[start:end]
