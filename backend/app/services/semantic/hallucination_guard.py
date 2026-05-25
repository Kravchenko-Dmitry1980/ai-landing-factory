"""Hallucination guard — source-grounded validation."""

import re
from dataclasses import dataclass

from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import GeneratedSemanticLanding, SemanticSection

METRIC_PATTERN = re.compile(r"\d+(?:[.,]\d+)?%?|\d+\s*(?:ms|sec|users|clients|projects)", re.I)


@dataclass
class HallucinationReport:
    warnings: list[str]
    adjusted_sections: list[SemanticSection]


def _ground_truth_corpus(contract: LandingContract) -> str:
    parts: list[str] = []
    for field in (contract.title, contract.client, contract.timeline, contract.lead, contract.quote):
        if field:
            parts.append(field.lower())
    for b in contract.blocks:
        parts.append(b.content.lower())
        parts.extend(x.lower() for x in b.bullets)
    return " ".join(parts)


def _metric_in_corpus(metric: str, corpus: str) -> bool:
    digits = re.findall(r"\d+(?:[.,]\d+)?", metric)
    if not digits:
        return True
    return any(d.replace(",", ".") in corpus for d in digits)


def guard_hallucinations(
    semantic: GeneratedSemanticLanding,
    contract: LandingContract,
) -> HallucinationReport:
    corpus = _ground_truth_corpus(contract)
    warnings: list[str] = []
    adjusted: list[SemanticSection] = []

    for section in semantic.sections:
        sec = section.model_copy(deep=True)
        flagged_metrics: list[str] = []
        for metric in sec.metrics:
            if METRIC_PATTERN.search(metric) and not _metric_in_corpus(metric, corpus):
                flagged_metrics.append(metric)
                warnings.append(
                    f"Unverified metric in {sec.section_type}: {metric[:80]}"
                )
        if flagged_metrics:
            sec.metrics = [m for m in sec.metrics if m not in flagged_metrics]
            sec.missing_data = list(dict.fromkeys(sec.missing_data + ["metrics_unverified"]))
            sec.confidence.factual_grounding = min(sec.confidence.factual_grounding, 0.4)
            sec.assumptions = list(
                dict.fromkeys(sec.assumptions + ["Removed metrics not found in contract"])
            )

        if sec.section_type == "team" and sec.bullets:
            verified: list[str] = []
            for item in sec.bullets:
                tokens = [t for t in re.split(r"\W+", item.lower()) if len(t) > 3]
                if any(t in corpus for t in tokens):
                    verified.append(item)
                else:
                    warnings.append(f"Unverified team entry removed: {item[:60]}")
            sec.bullets = verified
            if not verified and section.bullets:
                sec.missing_data.append("team")

        adjusted.append(sec)

    return HallucinationReport(warnings=sorted(set(warnings)), adjusted_sections=adjusted)
