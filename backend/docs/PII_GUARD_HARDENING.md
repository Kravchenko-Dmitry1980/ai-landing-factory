# PII Guard Hardening (Stage C.6)

## Overview

PII Guard is a standalone privacy layer that runs **immediately after upload/extraction**, before heuristic contract building and optional LLM enrich.

```
Upload → Extraction → PII PreScan → PIIReport (public in UI)
                    → Heuristic Contract → [Enrich] → SafeCloudPayload → LLM → Rehydration
```

## Detection layers

1. **Regex / heuristics** — email, phone, URL, passport/INN, FIO patterns, org markers
2. **Natasha (optional, local)** — Russian person names (`detector=natasha`)
3. **Merge / dedupe** — overlapping spans, same FIO → single placeholder
4. **Redaction** — placeholders `[PERSON_1]`, `[EMAIL_1]`, …

If `natasha` is not installed: fallback to regex-only + warning `natasha_not_available`.

## Privacy modes

| Mode | Pre-scan | Cloud LLM | Payload to cloud |
|------|----------|-----------|------------------|
| `hybrid_safe` | yes | allowed if redacted | placeholders only |
| `local_only` | yes | OpenAI blocked | blocked (`local_only`) |
| `cloud_unsafe_dev` | yes | allowed | raw text (UI/API warning) |

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/projects/privacy` | Global privacy config + storage policy |
| GET | `/api/v1/projects/{id}/pii-report` | Public PII report (no originals) |
| POST | `/api/v1/projects/{id}/pii-prescan` | Re-run pre-scan |
| GET | `/api/v1/projects/{id}/safe-cloud-payload` | Preview of LLM-bound text |
| POST | `/api/v1/projects/privacy/cleanup` | TTL cleanup of expired reports |

Upload response includes optional `pii_summary`.

## Storage

- Full reports: `backend/data/pii_reports/{project_id}.json` (may be Fernet-encrypted)
- Raw extractions: `backend/data/extractions/` (unchanged, not sent to cloud in hybrid_safe)
- TTL default: 72h (`PII_REPORT_TTL_HOURS`)

See [PII_STORAGE_POLICY.md](./PII_STORAGE_POLICY.md).

## Audit logging

Logger `pii.audit` records: project_id, mode, counts, risk, detectors, safe_for_cloud.
**Never** logs original PII values.

## Tests

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_pii_*.py -q
```
