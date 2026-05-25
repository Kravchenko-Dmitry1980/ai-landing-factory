# PII / Natasha Failure Analysis

## Summary

Full backend suite showed **26 failures** when tests ran against **system Python** (`ProgramData\Miniconda3`) with a **broken Natasha install**. Running against project **`.venv`** with fixes applied yields **0 failed**.

## Failure groups (original run)

| Group | Count | Root cause |
|-------|-------|------------|
| MorphVocab / tag_morph | ~20 | `doc.tag_morph(MorphVocab())` — wrong API; MorphVocab has no `.map` |
| pymorphy2 / pkg_resources | ~4 | `setuptools>=82` removed `pkg_resources`; pymorphy2 needs `<82` |
| pytest-asyncio missing | 4 | `@pytest.mark.asyncio` tests without plugin |
| Broken partial Natasha | variable | Import succeeds, runtime init/extract throws |

## Root cause

1. **Wrong Natasha API** in `detector.py`: used `Doc.tag_morph(morph_vocab)` pipeline. Correct approach for name detection: `NamesExtractor(morph_vocab)(text)` — no morph tagging required.

2. **Environment split**: CI/shell used global Python without pinned deps; `.venv` had no `natasha` at all (regex fallback worked, but API tests importing `app.main` failed on missing `docx`/`pypdf`).

3. **setuptools 82+** breaks `pymorphy2` dictionary discovery on Windows/Python 3.12.

## Fix applied

### Code (`app/services/pii/detector.py`)

- Lazy import via `try/except` on **any** exception during init.
- Use `NamesExtractor` callable API instead of `Doc.tag_morph`.
- Smoke test on init; on failure → `natasha_not_available` warning + regex fallback.
- `reset_natasha_cache()` for tests.
- `natasha_load_error()` for diagnostics.

### Dependencies (`requirements.txt`)

```
natasha>=1.6.0
pymorphy2-dicts-ru>=2.4.0
setuptools>=69.0.0,<82.0.0
pytest-asyncio>=0.23.0
```

### Tooling

- `scripts/check_pii_env.py` — import + smoke check
- `pytest.ini` — `asyncio_mode = auto`

## How to verify

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\pip.exe install -r requirements.txt
..\.venv\Scripts\python.exe scripts\check_pii_env.py
..\.venv\Scripts\python.exe -m pytest tests\test_pii_natasha.py tests\test_pii_russian_names.py -q
..\.venv\Scripts\python.exe -m pytest tests\ -q
```

Expected:

- `PII env OK` (Natasha or regex fallback)
- All PII tests pass
- Full suite: **0 failed**

## Behaviour matrix

| Natasha installed | Init OK | Detector used | Warning |
|-------------------|---------|---------------|---------|
| Yes | Yes | `natasha` + `regex` | — |
| Yes | No | `regex` only | `natasha_not_available` |
| No | — | `regex` only | `natasha_not_available` |

Public API never exposes `original` values regardless of mode.
