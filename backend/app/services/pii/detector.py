import logging

import re

from typing import Callable



from app.config import Settings

from app.schemas.pii import PIIEntity, PIIEntityType

from app.services.pii import patterns as pat

from app.services.pii.report import hash_original



logger = logging.getLogger(__name__)



_NatashaDetector: Callable[[str], list[tuple[str, int, int]]] | None = None

_natasha_checked = False

_natasha_available = False

_natasha_load_error: str | None = None





def natasha_available() -> bool:

    global _natasha_checked, _natasha_available

    if not _natasha_checked:

        _load_natasha()

    return _natasha_available





def natasha_load_error() -> str | None:

    """Last Natasha init error message, if any."""

    if not _natasha_checked:

        _load_natasha()

    return _natasha_load_error





def reset_natasha_cache() -> None:

    """Reset lazy Natasha cache (tests only)."""

    global _NatashaDetector, _natasha_checked, _natasha_available, _natasha_load_error

    _NatashaDetector = None

    _natasha_checked = False

    _natasha_available = False

    _natasha_load_error = None





def _load_natasha() -> Callable[[str], list[tuple[str, int, int]]] | None:

    global _NatashaDetector, _natasha_checked, _natasha_available, _natasha_load_error

    _natasha_checked = True

    if _NatashaDetector is not None:

        _natasha_available = True

        return _NatashaDetector



    try:

        from natasha import MorphVocab, NamesExtractor  # type: ignore



        morph_vocab = MorphVocab()

        names_extractor = NamesExtractor(morph_vocab)



        def extract(text: str) -> list[tuple[str, int, int]]:

            out: list[tuple[str, int, int]] = []

            try:

                for match in names_extractor(text):

                    span_text = text[match.start : match.stop].strip()

                    if span_text:

                        out.append((span_text, match.start, match.stop))

            except Exception as exc:

                logger.warning("Natasha names extraction failed: %s", exc)

            return out



        # Smoke test — invalid init must not leave half-enabled state

        smoke = extract("Кравченко Дмитрий Александрович — тимлид проекта")

        if not smoke:

            logger.warning("Natasha smoke test returned no spans; regex fallback only")



        _NatashaDetector = extract

        _natasha_available = True

        _natasha_load_error = None

        logger.info("Natasha NamesExtractor enabled (layer 2)")

        return extract

    except ImportError as exc:

        _natasha_available = False

        _natasha_load_error = f"import_error: {exc}"

        logger.debug("Natasha not installed; using regex/heuristics only")

        return None

    except Exception as exc:

        _natasha_available = False

        _natasha_load_error = str(exc)

        logger.warning("Natasha init failed; using regex/heuristics only: %s", exc)

        return None





class PIIDetector:

    """Hybrid local PII detection — no cloud calls."""



    def __init__(self, settings: Settings) -> None:

        self._settings = settings



    def detect_text(

        self,

        text: str,

        source_file: str | None = None,

    ) -> tuple[list[PIIEntity], list[str]]:

        if not text.strip():

            return [], []



        warnings: list[str] = []

        entities: list[PIIEntity] = []

        entities.extend(self._regex_layer(text, source_file))



        if self._settings.pii_mask_names:

            natasha = _load_natasha()

            if natasha:

                entities.extend(self._natasha_layer(text, source_file, natasha))

            elif self._settings.enable_pii_detection:

                warnings.append("natasha_not_available")



        return self._dedupe_entities(entities), warnings



    def _make_entity(

        self,

        entity_type: PIIEntityType,

        original: str,

        confidence: float,

        source_file: str | None,

        start: int,

        end: int,

        detector: str,

        text: str,

    ) -> PIIEntity:

        ctx_start = max(0, start - 30)

        ctx_end = min(len(text), end + 30)

        ctx = text[ctx_start:ctx_end]

        redacted_ctx = ctx.replace(original, "[REDACTED]")
        redacted_ctx = pat.EMAIL_RE.sub("[REDACTED]", redacted_ctx)
        redacted_ctx = pat.FIO_RE.sub("[REDACTED]", redacted_ctx)
        redacted_ctx = pat.PHONE_RE.sub("[REDACTED]", redacted_ctx)
        redacted_ctx = re.sub(r"[\w.+-]+@[\w.-]+", "[REDACTED]", redacted_ctx)

        return PIIEntity(

            type=entity_type,

            original=original,

            placeholder="",

            confidence=confidence,

            source_file=source_file,

            start=start,

            end=end,

            detector=detector,

            context_preview_redacted=redacted_ctx,

            original_hash=hash_original(original),

        )



    def _regex_layer(self, text: str, source_file: str | None) -> list[PIIEntity]:

        found: list[PIIEntity] = []



        def add_matches(

            pattern: re.Pattern[str],

            entity_type: PIIEntityType,

            confidence: float,

            enabled: bool = True,

        ) -> None:

            if not enabled:

                return

            for m in pattern.finditer(text):

                original = m.group(0).strip()

                if len(original) < 3 and entity_type != PIIEntityType.EMAIL:

                    continue

                found.append(

                    self._make_entity(

                        entity_type,

                        original,

                        confidence,

                        source_file,

                        m.start(),

                        m.end(),

                        "regex",

                        text,

                    )

                )



        add_matches(pat.EMAIL_RE, PIIEntityType.EMAIL, 0.95, self._settings.pii_mask_emails)

        add_matches(pat.PHONE_RE, PIIEntityType.PHONE, 0.9, self._settings.pii_mask_phones)

        add_matches(pat.URL_RE, PIIEntityType.URL, 0.85, True)

        add_matches(pat.TELEGRAM_RE, PIIEntityType.TELEGRAM, 0.9, True)

        add_matches(pat.PASSPORT_RU_RE, PIIEntityType.PASSPORT_ID, 0.92, True)

        add_matches(pat.INN_RE, PIIEntityType.PASSPORT_ID, 0.88, True)

        add_matches(pat.SNILS_RE, PIIEntityType.PASSPORT_ID, 0.9, True)

        add_matches(pat.ADDRESS_RE, PIIEntityType.ADDRESS, 0.75, True)

        add_matches(pat.ORG_RE, PIIEntityType.ORGANIZATION, 0.8, True)

        add_matches(pat.ROLE_PERSON_RE, PIIEntityType.ROLE_PERSON, 0.82, True)



        for m in pat.MEDICAL_KEYWORDS.finditer(text):

            start = max(0, m.start() - 10)

            end = min(len(text), m.end() + 40)

            snippet = text[start:end].strip()

            found.append(

                self._make_entity(

                    PIIEntityType.MEDICAL_DATA,

                    snippet,

                    0.7,

                    source_file,

                    start,

                    end,

                    "regex",

                    text,

                )

            )



        if self._settings.pii_mask_names:

            for pattern in (pat.FIO_RE, pat.LATIN_NAME_RE):

                for m in pattern.finditer(text):

                    original = m.group(0).strip()

                    if self._is_blocklisted(original):

                        continue

                    if entity_type := self._classify_name(original, text, m.start()):

                        found.append(

                            self._make_entity(

                                entity_type,

                                original,

                                confidence=0.78,

                                source_file=source_file,

                                start=m.start(),

                                end=m.end(),

                                detector="regex",

                                text=text,

                            )

                        )



        return found



    def _natasha_layer(

        self,

        text: str,

        source_file: str | None,

        extract: Callable[[str], list[tuple[str, int, int]]],

    ) -> list[PIIEntity]:

        found: list[PIIEntity] = []

        for name, start, end in extract(text):

            if self._is_blocklisted(name):

                continue

            if self._looks_like_org_context(text, start):

                continue

            if len(name.split()) < 2:

                continue

            found.append(

                self._make_entity(

                    PIIEntityType.PERSON_NAME,

                    name,

                    0.92,

                    source_file,

                    start,

                    end,

                    "natasha",

                    text,

                )

            )

        return found



    @staticmethod

    def _is_blocklisted(original: str) -> bool:

        first = original.split()[0]

        if first in pat.NAME_BLOCKLIST:

            return True

        lower = original.lower()

        for token in pat.NON_PERSON_TOKENS:

            if token in lower:

                return True

        return False



    @staticmethod

    def _looks_like_org_context(text: str, start: int) -> bool:

        window = text[max(0, start - 50) : start].lower()

        org_markers = ("им.", "им ", "моники", "больниц", "клиник", "институт", "центр")

        return any(m in window for m in org_markers)



    @staticmethod

    def _classify_name(original: str, text: str, start: int) -> PIIEntityType | None:

        window = text[max(0, start - 40) : start].lower()

        if any(

            k in window

            for k in ("клиент", "заказчик", "customer", "client", "компания", "организация")

        ):

            return PIIEntityType.ORGANIZATION

        return PIIEntityType.PERSON_NAME



    @staticmethod

    def _normalize_name(value: str) -> str:

        return " ".join(value.lower().split())



    def _dedupe_entities(self, entities: list[PIIEntity]) -> list[PIIEntity]:

        """Prefer person/email over broad medical spans; merge same person names."""

        if not entities:

            return []



        priority = {

            PIIEntityType.PERSON_NAME: 10,

            PIIEntityType.ROLE_PERSON: 9,

            PIIEntityType.EMAIL: 10,

            PIIEntityType.PHONE: 10,

            PIIEntityType.MEDICAL_DATA: 3,

            PIIEntityType.ORGANIZATION: 5,

        }



        by_normalized: dict[str, PIIEntity] = {}

        for ent in entities:

            if ent.type in (PIIEntityType.PERSON_NAME, PIIEntityType.ROLE_PERSON):

                key = self._normalize_name(ent.original)

                existing = by_normalized.get(key)

                if existing and existing.confidence >= ent.confidence:

                    continue

                by_normalized[key] = ent



        merged: list[PIIEntity] = []

        for ent in entities:

            if ent.type in (PIIEntityType.PERSON_NAME, PIIEntityType.ROLE_PERSON):

                key = self._normalize_name(ent.original)

                if by_normalized.get(key) is not ent:

                    continue

            merged.append(ent)



        sorted_entities = sorted(

            merged,

            key=lambda e: (

                -priority.get(e.type, 5),

                -(e.end - e.start),

                -e.confidence,

                e.start,

            ),

        )

        kept: list[PIIEntity] = []

        occupied: list[tuple[int, int]] = []



        for ent in sorted_entities:

            overlap = any(not (ent.end <= s or ent.start >= e) for s, e in occupied)

            if overlap:

                continue

            kept.append(ent)

            occupied.append((ent.start, ent.end))



        return sorted(kept, key=lambda e: e.start)


