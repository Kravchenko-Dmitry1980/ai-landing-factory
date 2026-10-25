"""The library's search index, kept in memory: matches with reasons, topics, similar landings.

Building it is linear in the size of the texts: each word finds its topics through its own
prefixes instead of being compared with every topic word. Parsed landings are reused across
rebuilds while their published version stays the same, so a new publication costs the
parsing of one landing plus the TF-IDF weights of all, a fraction of a second for hundreds.
"""

import logging
import math
import threading
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from app.repositories.publication_repository import Publication
from app.services.library.search import FieldWords, QueryTerm, query_terms, stem, words
from app.services.library.topics import TOPICS, TOPICS_BY_KEY

logger = logging.getLogger(__name__)

MAX_TOPICS = 3
FRESH_COUNT = 12
SHELF_SIZE = 24
# A topic carousel with one card only repeats "Новые проекты".
SHELF_MIN_CARDS = 2
OTHER_SHELF = ("other", "Другие проекты", "Всё остальное, что есть в библиотеке")
SIMILAR_COUNT = 6
SIMILAR_MIN_SCORE = 0.08
# Without a shared topic or customer, the texts themselves have to be clearly alike.
SIMILAR_WORDS_MIN_SCORE = 0.2
# Stems shorter than this carry no topic and stay out of similarity.
MIN_VECTOR_STEM = 3
SLOW_BUILD_SECONDS = 1.0

# Words of any project page: they say nothing about what two projects have in common,
# and prepositions in a query ("про камеры") must not point at topics.
_STOP_WORDS = (
    "для", "что", "это", "как", "при", "или", "все", "его", "так", "уже", "также", "через", "после",
    "более", "без", "между", "который", "когда", "если", "чтобы", "этот", "свой", "наш", "они", "она",
    "был", "быть", "может", "можно", "нужно", "один", "два", "три", "год", "весь", "каждый",
    "про", "над", "под", "перед", "около", "about",
    "проект", "система", "задача", "решение", "результат", "работа", "команда", "участник", "этап",
    "использование", "использовать", "основной", "новый", "the", "and", "for", "with",
)
_STOP_STEMS = frozenset(stem(word) for word in _STOP_WORDS)
# Organisation forms do not tell customers apart: «ООО «Пример»» and «Пример» are one customer.
_LEGAL_FORMS = frozenset(
    {"ооо", "оао", "зао", "пао", "ао", "ип", "нко", "ано", "фгбу", "гбу", "мбу", "гк", "ук", "llc", "ltd", "inc"}
)

# --- topic words, looked up from the text side ------------------------------------
# A topic word with a stem of five letters or more covers longer words ("камер" → "камерами").
# Shorter stems are ambiguous as prefixes ("стат" would take "статус", "виде" would take "видел"),
# so they match only exactly, or by the whole topic word as written ("видео" → "видеонаблюдение").
_LONG_STEM = 5
_long_stems: dict[str, set[tuple[str, str]]] = {}
_short_stems: dict[str, set[tuple[str, str]]] = {}
_word_prefixes: dict[str, set[tuple[str, str]]] = {}
for _topic in TOPICS:
    for _word in _topic.words:
        _stem = stem(_word)
        if len(_stem) >= _LONG_STEM:
            _long_stems.setdefault(_stem, set()).add((_topic.key, _word))
        else:
            _short_stems.setdefault(_stem, set()).add((_topic.key, _word))
            if len(_word) >= _LONG_STEM:
                _word_prefixes.setdefault(_word, set()).add((_topic.key, _word))
_WORD_PREFIX_LENGTHS = sorted({len(w) for w in _word_prefixes})
_TOPIC_WORDS: tuple[tuple[str, str], ...] = tuple((t.key, w) for t in TOPICS for w in t.words)
_TOPIC_LABEL_WORDS: dict[str, FieldWords] = {
    t.key: FieldWords(w for w in words(t.label) if len(w) >= MIN_VECTOR_STEM) for t in TOPICS
}


@lru_cache(maxsize=200_000)
def topic_words_in(word: str) -> frozenset[tuple[str, str]]:
    """(topic, topic word) pairs that this word of a text stands for. Landings share most words."""
    word_stem = stem(word)
    found: set[tuple[str, str]] = set()
    for length in range(_LONG_STEM, len(word_stem) + 1):
        found |= _long_stems.get(word_stem[:length], set())
    found |= _short_stems.get(word_stem, set())
    for length in _WORD_PREFIX_LENGTHS:
        if len(word) >= length:
            found |= _word_prefixes.get(word[:length], set())
    return frozenset(found)


def detect_topics(word_counts: Counter, title_words: set[str]) -> tuple[str, ...]:
    """
    A topic needs two of its words in the landing, or one in the title. The strongest
    topics come first: more distinct words, then more mentions.
    """
    distinct: dict[str, set[str]] = {}
    mentions: Counter = Counter()
    in_title: set[str] = set()
    for word, count in word_counts.items():
        for key, topic_word in topic_words_in(word):
            distinct.setdefault(key, set()).add(topic_word)
            mentions[key] += count
            if word in title_words:
                in_title.add(key)
    order = {topic.key: i for i, topic in enumerate(TOPICS)}
    passed = [key for key, found in distinct.items() if len(found) >= 2 or key in in_title]
    passed.sort(key=lambda key: (-len(distinct[key]), -mentions[key], order[key]))
    return tuple(passed[:MAX_TOPICS])


def customer_key(customer: str) -> str:
    return " ".join(stem(w) for w in words(customer) if w not in _LEGAL_FORMS)


@dataclass(frozen=True)
class Hit:
    publication: Publication
    score: float
    reasons: tuple[str, ...]
    # Found through a related topic, not through its own words.
    similar_topic: bool = False


@dataclass(frozen=True)
class SearchResult:
    hits: list[Hit]
    direct_total: int
    related_total: int
    # Words of the query that count; 0 with a query means nothing searchable was typed ("?", "C++").
    terms: int


@dataclass(frozen=True)
class SimilarLanding:
    publication: Publication
    reason: str


@dataclass(frozen=True)
class Shelf:
    key: str
    label: str
    note: str
    publications: tuple[Publication, ...]


@dataclass(frozen=True)
class _Entry:
    """One landing, parsed once per published version."""

    publication: Publication
    title: FieldWords
    people: tuple[tuple[str, tuple[str, ...]], ...]
    customer: FieldWords
    customer_key: str
    summary: FieldWords
    body: FieldWords
    topics: tuple[str, ...]
    # Stem → weight in the landing (title words count three times).
    stem_counts: Counter
    # A stem → the word as written in this landing, to name shared words in reasons.
    spelled: dict[str, str]


def _entry_key(publication: Publication) -> tuple:
    return (publication.project_id, publication.version, publication.published_at)


def _entry(publication: Publication) -> _Entry:
    title_words = words(publication.title)
    summary_words = words(publication.summary)
    body_words = publication.body_text.split()
    word_counts: Counter = Counter()
    stem_counts: Counter = Counter()
    spelled: dict[str, str] = {}
    for weight, group in ((3, title_words), (1, summary_words), (1, body_words)):
        for word in group:
            word_counts[word] += weight
            word_stem = stem(word)
            stem_counts[word_stem] += weight
            spelled.setdefault(word_stem, word)
    return _Entry(
        publication=publication,
        title=FieldWords(title_words),
        people=tuple((name, tuple(words(name))) for name in publication.people),
        customer=FieldWords(words(publication.customer)),
        customer_key=customer_key(publication.customer),
        summary=FieldWords(summary_words),
        body=FieldWords(body_words),
        topics=detect_topics(word_counts, set(title_words)),
        stem_counts=stem_counts,
        spelled=spelled,
    )


def _in_vector(stem_value: str) -> bool:
    return len(stem_value) >= MIN_VECTOR_STEM and stem_value not in _STOP_STEMS


def _person_matches(term: QueryTerm, name_words: tuple[str, ...]) -> bool:
    # Surnames as written, not stems: "Петровой" finds Петрова and Петров, never Пётр.
    return any(word.startswith(form) for word in name_words for form in term.name_forms)


class LibraryIndex:
    def __init__(self, entries: list[_Entry]) -> None:
        self._entries = entries
        self._by_slug = {e.publication.slug: e for e in entries}
        self._vectors = self._tf_idf(entries)

    @staticmethod
    def _tf_idf(entries: list[_Entry]) -> dict[str, dict[str, float]]:
        """A word in every landing weighs nothing; rare shared words weigh a lot."""
        total = len(entries)
        frequency: Counter = Counter()
        for entry in entries:
            frequency.update(s for s in entry.stem_counts if _in_vector(s))
        vectors: dict[str, dict[str, float]] = {}
        for entry in entries:
            vector = {
                s: (1 + math.log(n)) * math.log((total + 1) / (frequency[s] + 1))
                for s, n in entry.stem_counts.items()
                if _in_vector(s)
            }
            norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
            vectors[entry.publication.slug] = {s: v / norm for s, v in vector.items()}
        return vectors

    # --- topics -----------------------------------------------------------

    def topics_of(self, slug: str) -> tuple[str, ...]:
        entry = self._by_slug.get(slug)
        return entry.topics if entry else ()

    def topic_counts(self) -> list[tuple[str, int]]:
        counts = Counter(key for entry in self._entries for key in entry.topics)
        return [(topic.key, counts[topic.key]) for topic in TOPICS if counts[topic.key]]

    # --- search -----------------------------------------------------------

    @staticmethod
    def _direct(entry: _Entry, terms: list[QueryTerm]) -> Hit | None:
        """Every query word has to be found somewhere; the heaviest place counts and names the reason."""
        score = 0.0
        reasons: list[tuple[float, str]] = []
        for term in terms:
            candidates: list[tuple[float, str]] = []
            if entry.title.matches(term):
                candidates.append((3.0, "в названии"))
            person = next((name for name, name_words in entry.people if _person_matches(term, name_words)), None)
            if person:
                candidates.append((2.5, f"участник: {person}"))
            if entry.customer.matches(term):
                candidates.append((2.5, "заказчик"))
            topic = next((key for key in entry.topics if _TOPIC_LABEL_WORDS[key].matches(term)), None)
            if topic:
                candidates.append((2.0, f"тема: {TOPICS_BY_KEY[topic].label}"))
            if entry.summary.matches(term):
                candidates.append((1.5, "в описании"))
            if entry.body.matches(term):
                candidates.append((1.0, "в тексте"))
            if not candidates:
                return None
            best = max(candidates, key=lambda c: c[0])
            score += best[0]
            reasons.append(best)
        ordered = [reason for _, reason in sorted(reasons, key=lambda r: -r[0])]
        return Hit(entry.publication, score, tuple(dict.fromkeys(ordered))[:2])

    @staticmethod
    def query_topics(terms: list[QueryTerm]) -> dict[str, int]:
        """
        Topics the query is about, by how many of its words belong to each: "камеры" → vision.
        A word still being typed counts too ("распозна" → "распознавание"), from four letters.
        """
        found: dict[str, int] = {}
        for term in terms:
            if term.stem in _STOP_STEMS or len(term.word) < MIN_VECTOR_STEM:
                continue
            keys = {key for key, _ in topic_words_in(term.word)}
            if len(term.word) >= 4:
                keys |= {key for key, topic_word in _TOPIC_WORDS if topic_word.startswith(term.word)}
            keys |= {key for key, label in _TOPIC_LABEL_WORDS.items() if label.matches(term)}
            for key in keys:
                found[key] = found.get(key, 0) + 1
        return found

    def search(self, query: str) -> SearchResult:
        """
        Landings that contain every query word, best first; then landings on a topic the query
        is about whose own text does not use those words ("похожая тема").
        """
        if not query.strip():
            hits = [Hit(e.publication, 0.0, ()) for e in self._newest(self._entries)]
            return SearchResult(hits, len(hits), 0, 0)
        terms = query_terms(query)
        if not terms:
            return SearchResult([], 0, 0, 0)
        direct = [hit for entry in self._entries if (hit := self._direct(entry, terms))]
        direct.sort(key=lambda h: (h.score, h.publication.published_at), reverse=True)
        found = {hit.publication.slug for hit in direct}
        topics = self.query_topics(terms)
        related: list[Hit] = []
        for entry in self._newest(self._entries):
            shared = [key for key in entry.topics if key in topics]
            if entry.publication.slug in found or not shared:
                continue
            best = max(shared, key=lambda key: topics[key])
            related.append(
                Hit(
                    entry.publication,
                    0.5 * topics[best] / len(terms),
                    (f"похожая тема: {TOPICS_BY_KEY[best].label}",),
                    similar_topic=True,
                )
            )
        related.sort(key=lambda h: (h.score, h.publication.published_at), reverse=True)
        return SearchResult(direct + related, len(direct), len(related), len(terms))

    # --- shelves and neighbours -----------------------------------------------

    @staticmethod
    def _newest(entries: list[_Entry]) -> list[_Entry]:
        return sorted(entries, key=lambda e: e.publication.published_at, reverse=True)

    def fresh(self) -> list[Publication]:
        return [e.publication for e in self._newest(self._entries)[:FRESH_COUNT]]

    def shelves(self) -> list[Shelf]:
        """
        One carousel per topic with at least two landings, the fullest first, then
        "Другие проекты" with everything the front page would not show otherwise.
        """
        newest = self._newest(self._entries)
        shown = {e.publication.slug for e in newest[:FRESH_COUNT]}
        result: list[Shelf] = []
        for key, count in sorted(self.topic_counts(), key=lambda kc: -kc[1]):
            if count < SHELF_MIN_CARDS:
                continue
            topic = TOPICS_BY_KEY[key]
            members = [e for e in newest if key in e.topics][:SHELF_SIZE]
            shown |= {e.publication.slug for e in members}
            result.append(Shelf(key, topic.label, topic.note, tuple(e.publication for e in members)))
        rest = [e.publication for e in newest if e.publication.slug not in shown]
        if rest:
            key, label, note = OTHER_SHELF
            result.append(Shelf(key, label, note, tuple(rest)))
        return result

    def similar(self, slug: str) -> list[SimilarLanding]:
        """
        Neighbours of a landing: the same customer or topic, or many shared rare words.
        The reason names what they share, so staff see why a project is suggested.
        """
        target = self._by_slug.get(slug)
        if target is None:
            return []
        own = self._vectors[slug]
        ranked: list[tuple[float, SimilarLanding]] = []
        for entry in self._entries:
            if entry is target:
                continue
            other = self._vectors[entry.publication.slug]
            overlap = {s: own[s] * w for s, w in other.items() if s in own}
            score = sum(overlap.values())
            shared_topics = [key for key in target.topics if key in entry.topics]
            if target.customer_key and entry.customer_key == target.customer_key:
                score += 0.3
                reason = f"общий заказчик: {entry.publication.customer}"
            elif shared_topics:
                # The landing's main topic says more about it than a side one.
                score += 0.25 if shared_topics[0] == target.topics[0] else 0.15
                reason = f"общая тема: {TOPICS_BY_KEY[shared_topics[0]].label}"
            elif score >= SIMILAR_WORDS_MIN_SCORE:
                top = [s for s in sorted(overlap, key=overlap.get, reverse=True) if overlap[s] > 0][:2]
                reason = "общие слова: " + ", ".join(target.spelled.get(s, s) for s in top) if top else ""
            else:
                reason = ""
            if score >= SIMILAR_MIN_SCORE and reason:
                ranked.append((score, SimilarLanding(entry.publication, reason)))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in ranked[:SIMILAR_COUNT]]


# --- the cached index -------------------------------------------------------------

_lock = threading.Lock()
_index: tuple[tuple, LibraryIndex] | None = None
_entries: dict[tuple, _Entry] = {}


def publication_topics(publication: Publication) -> tuple[str, ...]:
    """Topics of one landing without building the whole index (one parse at most)."""
    key = _entry_key(publication)
    with _lock:
        entry = _entries.get(key)
    if entry is None:
        entry = _entry(publication)
        with _lock:
            _entries[key] = entry
    return entry.topics


def library_index(current: list[Publication], load_full: Callable[[], list[Publication]]) -> LibraryIndex:
    """
    The index for exactly these published versions. `current` may come without texts (cheap to
    read on every request); the full texts are loaded only when the index has to be rebuilt.
    The rebuild runs outside the lock, so other requests keep using the previous index meanwhile.
    """
    global _index
    key = tuple(sorted(_entry_key(p) for p in current))
    with _lock:
        cached = _index
        reusable = dict(_entries)
    if cached is not None and cached[0] == key:
        return cached[1]
    started = time.monotonic()
    full = load_full()
    entries = [reusable.get(_entry_key(p)) or _entry(p) for p in full]
    index = LibraryIndex(entries)
    with _lock:
        _entries.clear()
        _entries.update({_entry_key(e.publication): e for e in entries})
        # Another request may have stored a newer index meanwhile; keep it.
        if _index is cached:
            _index = (tuple(sorted(_entry_key(p) for p in full)), index)
    elapsed = time.monotonic() - started
    log = logger.warning if elapsed > SLOW_BUILD_SECONDS else logger.info
    log("Library index rebuilt: %d landings in %.2f s", len(entries), elapsed)
    return index
