"""What the library knows about a published landing: card text and the words search looks at."""

import re
from dataclasses import dataclass, field

from app.schemas.landing_contract import LandingContract
from app.services.export.public_team import publishable_team
from app.services.library.search import words

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}
SLUG_MAX_LENGTH = 60
MAX_PEOPLE = 60
MAX_BODY_CHARS = 50_000


@dataclass(frozen=True)
class PublicationMeta:
    title: str
    summary: str
    customer: str
    lead: str
    people: list[str] = field(default_factory=list)
    # Lower-case words of every section except the team, for search only.
    body_text: str = ""


def slugify(text: str) -> str:
    """Latin address part, the same transliteration as the frontend file names: "Контроль кассы" → "kontrol-kassy"."""
    latin = "".join(_TRANSLIT.get(ch, ch) for ch in text.lower())
    slug = re.sub(r"[^a-z0-9]+", "-", latin).strip("-")[:SLUG_MAX_LENGTH].rstrip("-")
    return slug or "lend"


def publication_meta(contract: LandingContract, summary: str) -> PublicationMeta:
    """
    Only names that the landing itself shows go into search: the team after the
    publication policy (the same one the page is rendered with) and the project lead.
    """
    blocks = {block.key: block for block in contract.blocks}
    lead = (contract.lead or "").strip()
    people: list[str] = []
    for name in [member.name.strip() for member in publishable_team(blocks.get("team"), contract.fidelity)] + [lead]:
        if name and name not in people:
            people.append(name)
    texts: list[str] = []
    for block in contract.blocks:
        if block.key != "team":
            texts.extend([block.title, block.content, *block.bullets])
    return PublicationMeta(
        title=((contract.title or "").strip() or "Проект")[:200],
        summary=summary.strip()[:600],
        customer=(contract.client or "").strip()[:200],
        lead=lead[:200],
        people=people[:MAX_PEOPLE],
        body_text=" ".join(words(" ".join(texts)))[:MAX_BODY_CHARS],
    )
