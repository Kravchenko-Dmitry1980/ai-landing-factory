"""Per-field fusion strategies."""

from __future__ import annotations

from typing import Any

from app.schemas.fidelity import LandingModule, TeamMember
from app.schemas.fusion import FieldCandidate, FieldFusionDecision
from app.services.contract_fidelity.team_candidate_validator import filter_team_members
from app.services.evidence.field_candidates import is_generic_title
from app.services.fusion.field_score import rank_candidates
from app.services.fusion.fusion_config import FIELD_CAPS, FIELD_STRATEGIES
from app.services.fusion.source_value_normalizer import (
    dedupe_strings,
    is_heading_bullet,
    merge_modules,
    merge_team_members,
    merge_tech_stacks,
    normalize_text_key,
)


class FieldStrategies:
    """Apply deterministic fusion strategy per field."""

    def fuse_field(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
    ) -> tuple[Any, FieldFusionDecision]:
        strategy = FIELD_STRATEGIES.get(field_name, "union_dedupe_ranked")
        if strategy == "primary_priority_single":
            return self._primary_priority_single(field_name, candidates, strategy)
        if strategy == "primary_metadata_priority":
            return self._primary_metadata_priority(field_name, candidates, strategy)
        if strategy == "best_plus_enrichment":
            return self._best_plus_enrichment(field_name, candidates, strategy)
        if strategy == "union_grouped_tech":
            return self._union_grouped_tech(field_name, candidates, strategy)
        if strategy == "union_validated_people":
            return self._union_validated_people(field_name, candidates, strategy)
        if strategy == "union_modules_with_source_priority":
            return self._union_modules(field_name, candidates, strategy)
        return self._union_dedupe_ranked(field_name, candidates, strategy)

    def _decision(
        self,
        field_name: str,
        strategy: str,
        selected: list[FieldCandidate],
        rejected: list[FieldCandidate],
        reason: str,
        warnings: list[str] | None = None,
    ) -> FieldFusionDecision:
        avg_conf = (
            sum(c.confidence for c in selected) / len(selected) if selected else 0.0
        )
        return FieldFusionDecision(
            field_name=field_name,
            strategy=strategy,
            selected_sources=_source_labels(selected),
            rejected_sources=_source_labels(rejected),
            confidence=round(avg_conf, 3),
            reason=reason,
            warnings=warnings or [],
        )

    def _primary_priority_single(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        ranked = rank_candidates(candidates, field_name)
        warnings: list[str] = []
        for candidate in ranked:
            value = candidate.value
            if not isinstance(value, str) or not value.strip():
                continue
            if is_generic_title(value) and candidate.source_role != "primary_project_doc":
                continue
            if candidate.source_role == "module_presentation":
                continue
            rejected = [c for c in ranked if c is not candidate]
            if len({c.value for c in candidates if isinstance(c.value, str)}) > 1:
                warnings.append("title_conflict_resolved")
            return value.strip(), self._decision(
                field_name,
                strategy,
                [candidate],
                rejected,
                f"primary identity from {candidate.filename or candidate.parser_mode}",
                warnings,
            )
        if ranked:
            winner = ranked[0]
            return winner.value, self._decision(
                field_name, strategy, [winner], ranked[1:], "fallback best candidate"
            )
        return None, self._decision(field_name, strategy, [], [], "no candidates")

    def _primary_metadata_priority(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        ranked = rank_candidates(candidates, field_name)
        warnings: list[str] = []
        for candidate in ranked:
            if candidate.source_role == "module_presentation":
                continue
            value = candidate.value
            if isinstance(value, str) and value.strip():
                rejected = [c for c in ranked if c is not candidate]
                if len({str(c.value) for c in candidates}) > 1:
                    warnings.append(f"{field_name}_conflict_resolved")
                return value.strip(), self._decision(
                    field_name,
                    strategy,
                    [candidate],
                    rejected,
                    f"metadata from {candidate.filename or candidate.parser_mode}",
                    warnings,
                )
        if ranked:
            winner = ranked[0]
            return winner.value, self._decision(
                field_name, strategy, [winner], ranked[1:], "fallback metadata"
            )
        return None, self._decision(field_name, strategy, [], [], "no metadata")

    def _best_plus_enrichment(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        ranked = rank_candidates(candidates, field_name)
        texts: list[tuple[str, FieldCandidate]] = []
        for candidate in ranked:
            if isinstance(candidate.value, str) and len(candidate.value.strip()) >= 80:
                if candidate.source_role != "module_presentation":
                    texts.append((candidate.value.strip(), candidate))

        if not texts:
            for candidate in ranked:
                if isinstance(candidate.value, str) and candidate.value.strip():
                    texts.append((candidate.value.strip(), candidate))
                    break

        if not texts:
            return "", self._decision(field_name, strategy, [], ranked, "empty essence")

        best_text, best = max(texts, key=lambda pair: len(pair[0]))
        sentences = _split_sentences(best_text)
        selected = [best]
        for text, candidate in texts:
            if candidate is best:
                continue
            extra = _non_overlapping_sentences(text, sentences)
            if extra:
                sentences.extend(extra[:2])
                selected.append(candidate)

        essence = " ".join(dict.fromkeys(sentences))[:1500]
        rejected = [c for c in ranked if c not in selected]
        return essence, self._decision(
            field_name,
            strategy,
            selected,
            rejected,
            "best essence with optional enrichment",
        )

    def _union_dedupe_ranked(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        ranked = rank_candidates(candidates, field_name)
        items: list[str] = []
        selected: list[FieldCandidate] = []
        for candidate in ranked:
            if not isinstance(candidate.value, list):
                continue
            added = False
            for item in candidate.value:
                if not isinstance(item, str):
                    continue
                if is_heading_bullet(item):
                    continue
                items.append(item)
                added = True
            if added:
                selected.append(candidate)
        cap = FIELD_CAPS.get(field_name)
        merged = dedupe_strings(items, cap=cap)
        rejected = [c for c in ranked if c not in selected]
        return merged, self._decision(
            field_name,
            strategy,
            selected,
            rejected,
            f"union from {len(selected)} sources",
        )

    def _union_grouped_tech(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        stacks: list[dict[str, list[str]]] = []
        selected: list[FieldCandidate] = []
        for candidate in candidates:
            if isinstance(candidate.value, dict) and candidate.value:
                stacks.append(candidate.value)
                selected.append(candidate)
        merged = merge_tech_stacks(stacks)
        rejected = [c for c in candidates if c not in selected]
        return merged, self._decision(
            field_name,
            strategy,
            selected,
            rejected,
            f"union tech from {len(selected)} sources",
        )

    def _union_validated_people(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        members: list[TeamMember] = []
        selected: list[FieldCandidate] = []
        for candidate in candidates:
            if isinstance(candidate.value, list) and candidate.value:
                for item in candidate.value:
                    if isinstance(item, TeamMember):
                        members.append(item)
                selected.append(candidate)
        merged = merge_team_members(members)
        validated = filter_team_members(merged)
        rejected = [c for c in candidates if c not in selected]
        return validated, self._decision(
            field_name,
            strategy,
            selected,
            rejected,
            f"union validated team ({len(validated)} members)",
        )

    def _union_modules(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        strategy: str,
    ) -> tuple[Any, FieldFusionDecision]:
        ranked = rank_candidates(candidates, field_name)
        modules: list[LandingModule] = []
        selected: list[FieldCandidate] = []
        for candidate in ranked:
            if isinstance(candidate.value, list) and candidate.value:
                for item in candidate.value:
                    if isinstance(item, LandingModule):
                        modules.append(item)
                selected.append(candidate)
        merged = merge_modules(modules)
        cap = FIELD_CAPS.get("modules", 12)
        merged = merged[:cap]
        rejected = [c for c in ranked if c not in selected]
        return merged, self._decision(
            field_name,
            strategy,
            selected,
            rejected,
            f"union modules ({len(merged)} kept)",
        )


def _source_labels(candidates: list[FieldCandidate]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        label = candidate.filename or candidate.parser_mode
        if label and label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def _split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in text.replace("\n", " ").split(". ") if len(p.strip()) > 20]
    return parts or [text.strip()]


def _non_overlapping_sentences(text: str, existing: list[str]) -> list[str]:
    existing_keys = {normalize_text_key(s) for s in existing}
    extras: list[str] = []
    for sentence in _split_sentences(text):
        key = normalize_text_key(sentence)
        if key not in existing_keys:
            extras.append(sentence)
            existing_keys.add(key)
    return extras
