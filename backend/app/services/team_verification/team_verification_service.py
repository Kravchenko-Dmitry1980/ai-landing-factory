"""Team verification gate — classify OCR candidates before public export."""

from __future__ import annotations

import logging
import re

from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.fidelity import TeamMember
from app.schemas.team_verification import (
    TeamCandidateQuality,
    TeamVerificationMetrics,
    TeamVerificationReport,
    TeamVerificationStatus,
)
from app.services.team_verification.export_policy import OCR_REVIEW_WARNING
from app.services.team_verification.name_matcher import (
    STRONG_MATCH_THRESHOLD,
    WEAK_MATCH_THRESHOLD,
    find_best_match,
    name_similarity,
)
from app.services.team_verification.name_quality import (
    normalize_cyrillic_name,
    score_name_quality,
    score_role_quality,
)
from app.services.team_verification.trusted_roster_builder import build_trusted_roster

logger = logging.getLogger(__name__)

MIN_NAME_QUALITY_REJECT = 0.3
GARBAGE_NAME_QUALITY = 0.4


class TeamVerificationService:
    """Classify team candidates into verified / review / rejected."""

    def verify(
        self,
        members: list[TeamMember],
        extraction: ExtractionResult | None = None,
        *,
        known_names: list[str] | None = None,
        expected_contract_names: list[str] | None = None,
    ) -> TeamVerificationReport:
        trusted = build_trusted_roster(
            extraction,
            known_names=known_names,
            expected_contract_names=expected_contract_names,
        )
        source_index = _build_source_index(extraction) if extraction else {}

        candidates: list[TeamCandidateQuality] = []
        for member in members:
            candidate = self._build_candidate(
                member, source_index, trusted, extraction
            )
            candidates.append(candidate)

        return self._classify_all(candidates, trusted)

    def _build_candidate(
        self,
        member: TeamMember,
        source_index: dict[str, _SourceInfo],
        trusted: list[str],
        extraction: ExtractionResult | None,
    ) -> TeamCandidateQuality:
        info = _resolve_source_info(member.name, source_index, extraction)

        name_score, name_warnings = score_name_quality(member.name)
        role_score = score_role_quality(member.role, member.contributions)

        matched, match_score = find_best_match(member.name, trusted)

        return TeamCandidateQuality(
            raw_name=member.name,
            normalized_name=normalize_cyrillic_name(member.name),
            role=member.role or None,
            contributions=list(member.contributions),
            source_filename=info.filename if info else "",
            source_type=info.source_type if info else "",
            source_location=info.location if info else None,
            source_is_ocr=info.is_ocr if info else False,
            ocr_engine=info.ocr_engine if info else None,
            ocr_confidence=info.ocr_confidence if info else None,
            name_quality_score=round(name_score, 3),
            role_quality_score=round(role_score, 3),
            matched_trusted_name=matched if match_score >= WEAK_MATCH_THRESHOLD else None,
            match_score=round(match_score, 3) if match_score > 0 else None,
            warnings=name_warnings,
        )

    def _classify_all(
        self,
        candidates: list[TeamCandidateQuality],
        trusted: list[str],
    ) -> TeamVerificationReport:
        verified: list[TeamCandidateQuality] = []
        review: list[TeamCandidateQuality] = []
        rejected: list[TeamCandidateQuality] = []
        probable: list[TeamCandidateQuality] = []
        warnings: list[str] = []

        for cand in candidates:
            classified = self._classify_one(cand, trusted)
            status = classified.verification_status
            if status == TeamVerificationStatus.verified:
                verified.append(classified)
            elif status == TeamVerificationStatus.needs_review:
                review.append(classified)
            elif status == TeamVerificationStatus.probable:
                probable.append(classified)
            else:
                rejected.append(classified)

        ocr_count = sum(1 for c in candidates if c.source_is_ocr)
        if review and ocr_count > 0:
            warnings.append(OCR_REVIEW_WARNING)

        metrics = TeamVerificationMetrics(
            ocr_candidates=ocr_count,
            verified_count=len(verified),
            needs_review_count=len(review),
            rejected_count=len(rejected),
            probable_count=len(probable),
        )

        return TeamVerificationReport(
            verified_members=verified,
            review_candidates=review,
            rejected_candidates=rejected,
            probable_candidates=probable,
            warnings=warnings,
            metrics=metrics,
        )

    def _classify_one(
        self,
        cand: TeamCandidateQuality,
        trusted: list[str],
    ) -> TeamCandidateQuality:
        """Apply verification rules to a single candidate."""
        name = cand.raw_name
        match_score = cand.match_score or 0.0
        matched = cand.matched_trusted_name

        # Garbage / low quality names
        if cand.name_quality_score < MIN_NAME_QUALITY_REJECT:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.rejected,
                    "verification_reason": "name_quality_below_threshold",
                }
            )

        if "mixed_latin_cyrillic" in cand.warnings and cand.name_quality_score < GARBAGE_NAME_QUALITY:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.rejected,
                    "verification_reason": "mixed_script_noise",
                }
            )

        # Non-OCR source with valid name and confirmed attribution → verified
        if (
            not cand.source_is_ocr
            and cand.source_type not in ("", "ocr")
            and cand.name_quality_score >= 0.5
        ):
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.verified,
                    "verification_reason": "trusted_non_ocr_source",
                    "corrected_name": matched if match_score >= STRONG_MATCH_THRESHOLD else None,
                }
            )

        # OCR with strong trusted match → verified with correction
        if match_score >= STRONG_MATCH_THRESHOLD and matched:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.verified,
                    "verification_reason": "ocr_matched_trusted_roster",
                    "corrected_name": matched,
                    "matched_trusted_name": matched,
                }
            )

        # OCR with weak fuzzy match → needs_review with suggested correction
        if WEAK_MATCH_THRESHOLD <= match_score < STRONG_MATCH_THRESHOLD and matched:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.needs_review,
                    "verification_reason": "ocr_weak_fuzzy_match",
                    "corrected_name": None,
                    "matched_trusted_name": matched,
                }
            )

        # OCR-only, no trusted match
        if cand.source_is_ocr:
            if cand.name_quality_score < 0.6:
                return cand.model_copy(
                    update={
                        "verification_status": TeamVerificationStatus.rejected,
                        "verification_reason": "ocr_low_quality_no_trusted_match",
                    }
                )
            if not cand.role and not cand.contributions:
                return cand.model_copy(
                    update={
                        "verification_status": TeamVerificationStatus.needs_review,
                        "verification_reason": "ocr_only_no_role_or_contributions",
                    }
                )
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.needs_review,
                    "verification_reason": "ocr_only_unverified",
                }
            )

        # Unknown source, no OCR flag — check trusted roster
        if match_score >= STRONG_MATCH_THRESHOLD and matched:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.verified,
                    "verification_reason": "matched_trusted_roster",
                    "corrected_name": matched,
                }
            )

        if match_score >= WEAK_MATCH_THRESHOLD:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.needs_review,
                    "verification_reason": "weak_trusted_match",
                }
            )

        if (
            cand.name_quality_score >= 0.7
            and not cand.source_is_ocr
            and cand.source_type not in ("", "ocr")
        ):
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.verified,
                    "verification_reason": "high_quality_non_ocr",
                }
            )

        # Unknown source — unverified
        if not cand.source_type and not cand.source_is_ocr:
            return cand.model_copy(
                update={
                    "verification_status": TeamVerificationStatus.needs_review,
                    "verification_reason": "unknown_source_unverified",
                }
            )

        return cand.model_copy(
            update={
                "verification_status": TeamVerificationStatus.probable,
                "verification_reason": "unverified_probable",
            }
        )


class _SourceInfo:
    __slots__ = ("filename", "source_type", "location", "is_ocr", "ocr_engine", "ocr_confidence")

    def __init__(
        self,
        filename: str,
        source_type: str,
        location: str | None,
        is_ocr: bool,
        ocr_engine: str | None = None,
        ocr_confidence: float | None = None,
    ) -> None:
        self.filename = filename
        self.source_type = source_type
        self.location = location
        self.is_ocr = is_ocr
        self.ocr_engine = ocr_engine
        self.ocr_confidence = ocr_confidence


def _build_source_index(extraction: ExtractionResult) -> dict[str, _SourceInfo]:
    """Map normalized name → best source info."""
    index: dict[str, _SourceInfo] = {}

    for source in extraction.files:
        text = source.extracted_text or ""
        is_ocr = bool(
            source.file_type == "ocr"
            or source.metadata.get("is_ocr_derivative")
        )
        ocr_engine = source.metadata.get("ocr_engine")
        ocr_confidence = source.metadata.get("ocr_confidence")

        for name in _extract_names_from_text(text):
            key = normalize_cyrillic_name(name)
            existing = index.get(key)
            info = _SourceInfo(
                filename=source.filename,
                source_type="ocr" if is_ocr else source.file_type,
                location=_location_label(source),
                is_ocr=is_ocr,
                ocr_engine=str(ocr_engine) if ocr_engine else None,
                ocr_confidence=float(ocr_confidence) if ocr_confidence is not None else None,
            )
            # Prefer non-OCR source
            if existing is None or (existing.is_ocr and not is_ocr):
                index[key] = info

    return index


def _extract_names_from_text(text: str) -> list[str]:
    """Extract potential person names from text."""
    names: list[str] = []
    pattern = re.compile(
        r"\b([А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){1,2})\b"
    )
    for match in pattern.finditer(text):
        names.append(match.group(1))
    return names


def _location_label(source: FileExtraction) -> str | None:
    slide = source.metadata.get("page_or_slide")
    if slide:
        return f"slide {slide}"
    return None


def _resolve_source_info(
    name: str,
    source_index: dict[str, _SourceInfo],
    extraction: ExtractionResult | None,
) -> _SourceInfo | None:
    """Resolve best source info for a team member name."""
    key = normalize_cyrillic_name(name)
    info = source_index.get(key)
    if info is None:
        info = _infer_source(name, source_index)
    if info is not None:
        return info
    if extraction:
        return _scan_extraction_for_name(name, extraction)
    return None


def _scan_extraction_for_name(
    name: str,
    extraction: ExtractionResult,
) -> _SourceInfo | None:
    """Find whether name appears in OCR-only or non-OCR sources."""
    ocr_info: _SourceInfo | None = None
    non_ocr_info: _SourceInfo | None = None
    name_lower = name.lower()

    for source in extraction.files:
        text = source.extracted_text or ""
        if name_lower not in text.lower():
            continue
        is_ocr = bool(
            source.file_type == "ocr"
            or source.metadata.get("is_ocr_derivative")
        )
        info = _SourceInfo(
            filename=source.filename,
            source_type="ocr" if is_ocr else source.file_type,
            location=_location_label(source),
            is_ocr=is_ocr,
            ocr_engine=str(source.metadata.get("ocr_engine") or "") or None,
            ocr_confidence=(
                float(source.metadata["ocr_confidence"])
                if source.metadata.get("ocr_confidence") is not None
                else None
            ),
        )
        if is_ocr:
            ocr_info = info
        else:
            non_ocr_info = info

    return non_ocr_info or ocr_info


def _infer_source(
    name: str,
    source_index: dict[str, _SourceInfo],
) -> _SourceInfo | None:
    """Fuzzy infer source for a name not exactly in index."""
    best: _SourceInfo | None = None
    best_score = 0.0
    for key, info in source_index.items():
        score = name_similarity(name, key)
        if score > best_score:
            best_score = score
            best = info
    if best_score >= STRONG_MATCH_THRESHOLD:
        return best
    return None


def verified_team_members(report: TeamVerificationReport) -> list[TeamMember]:
    """Extract TeamMember list from verified candidates."""
    from app.services.team_verification.export_policy import candidate_to_team_member

    return [
        candidate_to_team_member(c)
        for c in report.verified_members
        if c.verification_status == TeamVerificationStatus.verified
    ]
