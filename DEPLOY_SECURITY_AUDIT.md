# Deploy Security Audit

Дата: 2026-07-26

## Summary

**PASS** (with low WARN on vendored A-Frame string literals)

## Checked

- git tracked files (`git ls-files`)
- env files / examples / gitignore exceptions
- logs / runtime artifacts (not staged)
- deploy templates (nginx, systemd, docker, ubuntu scripts)
- pattern scan for `sk-`, `OPENAI_API_KEY=`, `ANTHROPIC_API_KEY=`, `FREEMODEL`, `password=`, `SECRET_KEY=`
- full-product zip forbidden entries (`.env`, `.venv`, `node_modules`, `.git`, uploads)

## Findings

| Severity | File | Problem | Action |
|---|---|---|---|
| INFO | `backend/.env`, `frontend/.env.local` | Local secrets files exist on disk | Keep gitignored; never commit (verified ignored) |
| INFO | Tracked `*tokens*` paths | Theme design tokens, not API secrets | No action |
| INFO | Docs mentioning FreeModel / `OPENAI_API_KEY=` | Examples / status docs with empty or placeholder values | OK |
| WARN | `showcase/vendor/aframe/aframe.min.js` (in static release) | Minified vendor contains string refs to `unpkg.com` / `fonts.googleapis.com` | Acceptable: runtime uses local vendor path; not loaded from CDN by our HTML |
| PASS | Full product zip | No `.env` / `.venv` / `node_modules` / `.git` / uploads | Keep builder checks |
| PASS | `backend/.env.production.example` etc. | Tracked via gitignore exceptions | OK to commit examples only |

## Secrets Policy

- `.env` never committed
- production secrets through server file `chmod 600` / systemd `EnvironmentFile`
- frontend env must contain no secrets (`NEXT_PUBLIC_*` is public)
- FreeModel / OpenAI keys stay empty unless explicitly approved
- Do not commit `backend/data/`, `.runtime/`, `logs/`

## Gitignore notes

Exceptions added for:

- `backend/.env.production.example`
- `frontend/.env.production.example`
- `deploy/docker/.env.docker.example`
