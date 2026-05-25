import re

# Layer 1 — regex / heuristics (local only)

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-().]*)?"
    r"(?:\(?\d{2,4}\)?[\s\-.]*)?"
    r"\d{3}[\s\-.]?\d{2,3}[\s\-.]?\d{2,4}\b",
)

URL_RE = re.compile(
    r"https?://[^\s<>\"']+|"
    r"\b(?:www\.)[a-z0-9][-a-z0-9.]*\.[a-z]{2,}(?:/[^\s]*)?",
    re.IGNORECASE,
)

TELEGRAM_RE = re.compile(
    r"(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_]{3,32}|"
    r"@[A-Za-z][A-Za-z0-9_]{4,31}",
    re.IGNORECASE,
)

PASSPORT_RU_RE = re.compile(
    r"\b(?:паспорт|серия|№)\s*[\d\s]{4,12}\b",
    re.IGNORECASE,
)

INN_RE = re.compile(r"\b(?:ИНН|inn)[\s:]*\d{10,12}\b", re.IGNORECASE)
SNILS_RE = re.compile(r"\b\d{3}-\d{3}-\d{3}\s\d{2}\b")

# Russian FIO: 2–3 capitalized tokens
FIO_RE = re.compile(
    r"\b[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2}\b",
)

# Latin names (conservative)
LATIN_NAME_RE = re.compile(
    r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b",
)

ADDRESS_RE = re.compile(
    r"\b(?:ул\.|улица|пр\.|проспект|пер\.|д\.|дом|кв\.|квартира|"
    r"г\.|город|обл\.|область|район|индекс|"
    r"street|st\.|avenue|ave\.|road|rd\.)\s*[^,\n]{3,80}",
    re.IGNORECASE,
)

ORG_RE = re.compile(
    r"\b(?:ООО|ОАО|ЗАО|ПАО|АО|ИП|LLC|Inc\.?|Ltd\.?|GmbH|Corp\.?)\s+"
    r"[«\"]?[А-ЯЁA-Za-z0-9][А-ЯЁA-Za-z0-9\s«»\".-]{2,60}",
    re.IGNORECASE,
)

MEDICAL_KEYWORDS = re.compile(
    r"\b(?:диагноз|МКБ[-\s]?\d|пациент|история\s+болезни|"
    r"глюкоз|инсулин|гипертония|онколог|эндокринолог|"
    r"аллергия|рецепт|дозировка|лабораторн)\b",
    re.IGNORECASE,
)

ROLE_PERSON_RE = re.compile(
    r"(?:главный|ведущий|старший|младший)?\s*"
    r"(?:врач|эндокринолог|хирург|терапевт|директор|руководитель|"
    r"менеджер|архитектор|разработчик|аналитик|консультант)\s+"
    r"[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?",
    re.IGNORECASE,
)

# Common non-PII capitalized phrases to skip as names
NAME_BLOCKLIST = frozenset(
    {
        "Проект",
        "Задача",
        "Задачи",
        "Результат",
        "Результаты",
        "Цель",
        "Цели",
        "Клиент",
        "Команда",
        "Стек",
        "Вводные",
        "Выходные",
        "Landing",
        "Factory",
        "Microsoft",
        "Google",
        "OpenAI",
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Qwen",
        "Meditron",
        "МОНИКИ",
        "Natasha",
    }
)

# Substrings that indicate org/product, not a person name
NON_PERSON_TOKENS = frozenset(
    {
        "openai",
        "qwen",
        "meditron",
        "моники",
        "владимирского",
        "microsoft",
        "google",
    }
)
