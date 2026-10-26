"""Words, stems and word lookups for library search: Snowball stemmers, no models.

"контроля" and "контроль" share the stem "контрол". Words of three letters or fewer
stay whole: the stemmer would cut "ИИ" to "и" and "УИИ" to "у", which match everything.
"""

import re
import threading
from bisect import bisect_left
from dataclasses import dataclass
from functools import lru_cache

import snowballstemmer

_WORD = re.compile(r"[0-9a-zа-я]+")
_RUSSIAN = snowballstemmer.stemmer("russian")
_ENGLISH = snowballstemmer.stemmer("english")
# Snowball stemmers keep the word being processed inside the object; sync endpoints run in threads.
_STEM_LOCK = threading.Lock()
SHORT_WORD = 3
MAX_QUERY_TERMS = 12
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}
# Case endings of Russian surnames: "Петровой" → "петров", "Кусу" → "кус".
_NAME_ENDINGS = ("ой", "ым", "ом", "ою", "ую", "ая", "ых", "их", "а", "у", "е", "ы")


def transliterate(text: str) -> str:
    """Russian letters in Latin, the same way as landing addresses: "телеграм" → "telegram"."""
    return "".join(_TRANSLIT.get(ch, ch) for ch in text)


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower().replace("ё", "е"))


@lru_cache(maxsize=100_000)
def stem(word: str) -> str:
    if word.isdigit() or len(word) <= SHORT_WORD:
        return word
    stemmer = _ENGLISH if word.isascii() else _RUSSIAN
    with _STEM_LOCK:
        return stemmer.stemWord(word) or word


def stems(text: str) -> list[str]:
    return [stem(word) for word in words(text)]


def name_forms(word: str) -> tuple[str, ...]:
    """
    The word and its base without a case ending, for matching surnames as written:
    "петровой" → ("петровой", "петров"). Unlike stems, "Петров" does not shrink to "петр",
    so a search for Петрова never finds Пётр.
    """
    forms = [word]
    for ending in _NAME_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= SHORT_WORD:
            forms.append(word[: -len(ending)])
    return tuple(dict.fromkeys(forms))


@dataclass(frozen=True)
class QueryTerm:
    word: str
    stem: str
    name_forms: tuple[str, ...]
    # The word in Latin letters, for brands written in Latin: "телеграм" finds "Telegram".
    latin: str | None = None
    latin_stem: str | None = None


def query_terms(query: str) -> list[QueryTerm]:
    """Distinct words of the query; one-letter words carry no meaning and are dropped."""
    found: dict[str, QueryTerm] = {}
    for word in words(query):
        if (len(word) >= 2 or word.isdigit()) and word not in found:
            latin = transliterate(word) if not word.isascii() and len(word) >= 4 else None
            found[word] = QueryTerm(word, stem(word), name_forms(word), latin, stem(latin) if latin else None)
    return list(found.values())[:MAX_QUERY_TERMS]


def _has_prefix(sorted_values: tuple[str, ...], prefix: str) -> bool:
    i = bisect_left(sorted_values, prefix)
    return i < len(sorted_values) and sorted_values[i].startswith(prefix)


class FieldWords:
    """The words of one field, looked up by prefix in logarithmic time."""

    __slots__ = ("words", "stems")

    def __init__(self, field_words) -> None:
        unique = set(field_words)
        self.words: tuple[str, ...] = tuple(sorted(unique))
        self.stems: tuple[str, ...] = tuple(sorted({stem(w) for w in unique}))

    def matches(self, term: QueryTerm) -> bool:
        """Another form of the word ("контроля" → "контроль") or a word still being typed ("конт")."""
        if _has_prefix(self.stems, term.stem) or _has_prefix(self.words, term.word):
            return True
        return bool(term.latin) and (_has_prefix(self.stems, term.latin_stem) or _has_prefix(self.words, term.latin))
