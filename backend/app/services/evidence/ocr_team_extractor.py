"""Fuzzy team extraction from noisy OCR text (image-only slides)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.evidence import TeamMemberCandidate
from app.schemas.fidelity import TeamMember
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_candidates,
    is_valid_person_name,
    is_valid_team_role,
    validate_team_candidate_with_reason,
)
from app.services.contract_fidelity.team_parser import _split_name_list, _strip_urls
from app.services.evidence.group_team_parser import (
    expand_group_block,
    merge_team_members,
    parse_team_blocks,
)
from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_role,
    normalize_ocr_team_text,
)

NAME_ROLE_RE = re.compile(r"^(.+?)\s*[—–-]\s*(.+)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+(.+)$")
ROLE_LINE_RE = re.compile(
    r"^(Тимлид|Помощник\s+тимлида|Участник|Разработчик|Аналитик)\s*:\s*(.+)$",
    re.IGNORECASE,
)
RUSSIAN_NAME_RE = re.compile(
    r"\b([А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){1,2})\b"
)

FALSE_POSITIVE_MARKERS = frozenset(
    {
        "qdrant",
        "telegram",
        "neo4j",
        "bertopic",
        "google colab",
        "streamlit",
        "backend",
        "frontend",
        "docker",
        "python",
        "redis",
        "postgres",
    }
)

SKIP_HEADERS = frozenset(
    {
        "команда проекта",
        "тимлид проекта",
        "участники команды проекта",
        "участники",
        "команда",
        "тимлид",
        "роли",
        "разработчики",
    }
)


@dataclass
class OcrTeamExtractionResult:
    members: list[TeamMemberCandidate] = field(default_factory=list)
    raw_text: str = ""
    normalized_text: str = ""
    team_section_detected: bool = False
    rejected: list[tuple[str, str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_trace: str = ""


def extract_team_from_ocr_text(
    text: str,
    source_trace: str = "",
) -> OcrTeamExtractionResult:
    """Extract team members from noisy OCR text with normalization trace."""
    result = OcrTeamExtractionResult(raw_text=text, source_trace=source_trace)
    if not text.strip():
        return result

    result.team_section_detected = detect_team_ocr_section(text)
    normalized = normalize_ocr_team_text(text)
    result.normalized_text = normalized

    if not result.team_section_detected:
        result.warnings.append("No team section markers detected in OCR text.")
        return result

    candidates: list[TeamMemberCandidate] = []
    seen: set[str] = set()

    def _accept(name: str, role: str = "") -> None:
        name = _strip_urls(name.strip())
        role = normalize_ocr_role(role) if role else role
        ok, reason = validate_team_candidate_with_reason(
            name,
            role=role,
            source_text=normalized,
            in_team_section=True,
        )
        if ok:
            key = name.lower()
            if key not in seen:
                seen.add(key)
                candidates.append(
                    TeamMemberCandidate(
                        name=name,
                        role=role,
                        source_refs=[source_trace] if source_trace else [],
                    )
                )
            return
        if _looks_like_person_attempt(name):
            result.rejected.append((name, role, reason))
            if "not_person_name" in reason:
                result.warnings.append(
                    f"Possible person line rejected due to low OCR quality: {name!r}"
                )

    # Structured blocks (group lines, shared roles).
    for block in parse_team_blocks(normalized):
        for member in expand_group_block(block):
            _accept(member.name, member.role or "")

    # Line-by-line patterns for OCR layouts.
    lines = normalized.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.lower() in SKIP_HEADERS:
            continue
        if _is_false_positive_line(line):
            continue

        role_line = ROLE_LINE_RE.match(line)
        if role_line:
            _accept(role_line.group(2).strip(), role_line.group(1).strip())
            continue

        numbered = NUMBERED_RE.match(line)
        payload = numbered.group(1).strip() if numbered else line

        name_role = NAME_ROLE_RE.match(payload)
        if name_role:
            _accept(name_role.group(1).strip(), name_role.group(2).strip())
            continue

        low = line.lower()
        if low in {"тимлид проекта", "тимлид"} and i < len(lines):
            next_line = lines[i].strip()
            if is_valid_person_name(_strip_urls(next_line)):
                _accept(next_line, "Тимлид проекта")
                i += 1
            continue

        if "," in payload:
            role = ""
            trailing = ""
            if " — " in payload:
                payload, trailing = payload.split(" — ", 1)
                role = normalize_ocr_role(trailing.strip())
            for name in _split_name_list(payload):
                if is_valid_person_name(name):
                    _accept(name, role)
            continue

        if is_valid_person_name(_strip_urls(payload)):
            _accept(payload, "")
            continue

    filtered = filter_team_candidates(
        candidates,
        source_text=normalized,
        in_team_section=True,
    )
    result.members = filtered
    return result


def extract_team_members_from_ocr_text(
    text: str,
    source_trace: str = "",
) -> list[TeamMember]:
    """Convenience wrapper returning validated TeamMember list."""
    extraction = extract_team_from_ocr_text(text, source_trace=source_trace)
    members = [
        TeamMember(
            name=c.name,
            role=c.role,
            project_area=c.project_area,
            contributions=list(c.contributions),
        )
        for c in extraction.members
    ]
    return merge_team_members(members)


def _looks_like_person_attempt(text: str) -> bool:
    cleaned = _strip_urls(text.strip())
    if not cleaned or len(cleaned) < 4:
        return False
    words = cleaned.split()
    if len(words) < 2:
        return False
    if any(w[0].isupper() for w in words if w):
        return True
    return bool(RUSSIAN_NAME_RE.search(cleaned))


def _is_false_positive_line(line: str) -> bool:
    low = line.lower()
    return any(marker in low for marker in FALSE_POSITIVE_MARKERS)
