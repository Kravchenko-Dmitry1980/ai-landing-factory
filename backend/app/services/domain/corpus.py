"""Shared contract corpus utilities for domain intelligence."""

import re

from app.schemas.landing_contract import LandingContract

_SPLIT_RE = re.compile(r"[,;|\n•·]+")


def contract_corpus(contract: LandingContract) -> str:
    parts: list[str] = []
    for field in (contract.title, contract.client, contract.lead, contract.quote):
        if field:
            parts.append(field)
    parts.extend(contract.goals)
    for block in contract.blocks:
        parts.append(block.title)
        parts.append(block.content)
        parts.extend(block.bullets)
    return "\n".join(parts)


def contract_corpus_lower(contract: LandingContract) -> str:
    return contract_corpus(contract).lower()


def is_grounded(label: str, corpus: str) -> bool:
    norm = label.lower().strip()
    if len(norm) < 3:
        return False
    if norm in corpus:
        return True
    tokens = [t for t in re.split(r"\W+", norm) if len(t) > 2]
    if not tokens:
        return False
    return sum(1 for t in tokens if t in corpus) >= max(1, len(tokens) // 2)


def tokens_from_text(text: str) -> list[str]:
    items: list[str] = []
    for chunk in _SPLIT_RE.split(text):
        chunk = chunk.strip(" -–—•")
        if 2 < len(chunk) <= 80:
            items.append(chunk)
    return items


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:64] or "entity"
