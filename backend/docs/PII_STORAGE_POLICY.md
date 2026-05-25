# PII Storage Policy

## What is stored

| Artifact | Location | Contains originals? | TTL |
|----------|----------|---------------------|-----|
| Raw extraction | `data/extractions/{project_id}.json` | yes (full text) | none (MVP) |
| Full PII report | `data/pii_reports/{project_id}.json` | yes (entities.original) | 72h default |
| Safe payload preview | built on-the-fly / optional cache | no | — |
| Upload files | `data/uploads/` | yes | none (MVP) |

## Encryption (optional)

Set in `backend/.env`:

```
PII_ENCRYPT_REPORTS=true
PII_ENCRYPTION_KEY=<Fernet key>
```

Generate key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

When enabled, full reports are stored as `FERNET:...` on disk. Public API always strips originals.

## What goes to cloud LLM

- **hybrid_safe**: redacted extraction text only (placeholders)
- **local_only**: nothing (OpenAI blocked)
- **cloud_unsafe_dev**: raw extraction (dev warning required)

Use `GET /api/v1/projects/{id}/safe-cloud-payload` to inspect before enrich.

## Cleanup

Automatic TTL cleanup removes expired reports from `data/pii_reports/`.

```powershell
# Manual API
curl -X POST http://localhost:8000/api/v1/projects/privacy/cleanup

# CLI
python backend/scripts/cleanup_pii.py
```

Config:

```
PII_REPORT_TTL_HOURS=72
PII_CLEANUP_ENABLED=true
```

## Disable cloud

```
PRIVACY_MODE=local_only
# or
LLM_ENABLED=false
```

## Logging policy

- Allowed: project_id, privacy_mode, entity counts by type, risk_level, detectors_used
- Forbidden: original names, emails, phones, raw text fragments

`PII_AUDIT_LOG_ORIGINALS` must remain `false` in production.
