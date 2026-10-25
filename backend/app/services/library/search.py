"""Library search without models: word prefixes with light Russian ending trimming.

"контроля" finds "контроль", "Иванова" finds "Иванов". Real morphology and
"similar topic" search come later; this is enough for titles, surnames and customers.
"""

import re

_WORD = re.compile(r"[0-9a-zа-я]+")
_SOFT_ENDINGS = frozenset("аяоеуюыиьй")
MAX_TERMS = 12


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower().replace("ё", "е"))


def _stem(term: str) -> str:
    # Russian endings are one or two letters; trimming them lets other forms of the word match.
    if len(term) >= 7:
        return term[:-2]
    if len(term) >= 5:
        return term[:-1]
    # Short surnames and nouns: "куса" finds "Кус", "бота" finds "бот", "сайт" stays whole.
    if len(term) == 4 and term[-1] in _SOFT_ENDINGS:
        return term[:-1]
    return term


def query_terms(query: str) -> list[str]:
    seen: list[str] = []
    for word in words(query):
        if (len(word) >= 2 or word.isdigit()) and word not in seen:
            seen.append(word)
    return [_stem(word) for word in seen[:MAX_TERMS]]


def score(terms: list[str], fields: list[tuple[float, list[str]]]) -> float:
    """Every term has to match some word; a match in a heavier field counts more. 0 means no match."""
    total = 0.0
    for term in terms:
        best = max((weight for weight, field_words in fields if any(w.startswith(term) for w in field_words)), default=0.0)
        if best == 0.0:
            return 0.0
        total += best
    return total
