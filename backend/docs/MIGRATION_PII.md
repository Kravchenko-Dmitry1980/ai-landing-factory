# PII-Safe Hybrid Architecture — Migration Notes

## What changed

Stage **C.5** runs on `POST /contract/enrich` (and on-demand `GET /pii-report`):

```
ExtractionResult → PII detect → redact → cloud-safe LLM → rehydrate → LandingContract
```

Upload / extraction / heuristic contract **unchanged**. Raw extractions stay in `data/extractions/`.

## Env (add to `backend/.env`)

```env
PRIVACY_MODE=hybrid_safe
ENABLE_PII_DETECTION=true
ENABLE_REHYDRATION=true
PII_MASK_NAMES=true
PII_MASK_EMAILS=true
PII_MASK_PHONES=true
```

| Mode | Behavior |
|------|----------|
| `hybrid_safe` | OpenAI receives **redacted** text only (default) |
| `local_only` | Blocks `openai` provider; mock/heuristic OK |
| `cloud_unsafe_dev` | Sends raw text — dev only |

## New storage

- `data/pii_reports/{project_id}.json` — full report server-side (contains originals)
- API returns `PIIReportPublic` — **no** original values

## New API (backward compatible)

- `GET /api/v1/projects/privacy` — global privacy status
- `GET /api/v1/projects/{id}/pii-report` — public entity table

## Optional dependency

```powershell
pip install natasha
```

Improves Russian PERSON detection (Layer 2). Without it: regex/heuristics only.

## Verify

```powershell
cd c:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe -m pytest tests\test_pii_stage.py tests\test_llm_contract_builder.py -q
```

## Rollback

Set `ENABLE_PII_DETECTION=false` — enrich behaves as before (no redaction, audit logs `pii_detection_skipped`).

## Security logging

Logger `pii.audit` — never logs raw PII. Do not set `PII_AUDIT_LOG_ORIGINALS=true` in production.
