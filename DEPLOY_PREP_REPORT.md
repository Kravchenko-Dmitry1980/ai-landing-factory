# Deploy Prep Report

Дата: 2026-07-26  
Проект: `C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh`  
Ветка: `main`

## 1. Status

**READY FOR SERVER PARAMS**

Локальная подготовка деплоя завершена. Реальный деплой на сервер **не выполнялся** (нет параметров сервера / stop-list).

## 2. Scope Completed

| Area | Status | Notes |
|---|---|---|
| Mode A — static demo | DONE | zip + nginx template + README |
| Mode B — systemd + nginx | DONE | units, nginx, ubuntu scripts/docs |
| Mode C — Docker draft | DONE | experimental, not primary |
| Env templates | DONE | production + docker examples |
| Security audit | PASS (WARN) | no tracked secrets; CDN string WARN in vendored aframe |
| Backend tests (targeted) | PASS | Algofusion 9 + regression 39 |
| Frontend lint/build | PASS | lint clean; `npm run build` OK |
| Local runtime | PASS | `/health` 200, frontend 200 |
| Release archives | DONE | static + full under `.runtime/release/` |
| Server deploy | NOT DONE | blocked — no server params |
| FreeModel / AI | NO-GO | not touched |

## 3. Created Files

| File | Purpose |
|---|---|
| `deploy/static/README_STATIC_DEPLOY.md` | Static demo runbook |
| `deploy/nginx/ai-landing-static.conf` | nginx static |
| `deploy/nginx/ai-landing-full.conf` | nginx reverse proxy |
| `deploy/systemd/alf-backend.service` | uvicorn on 127.0.0.1:8001 |
| `deploy/systemd/alf-frontend.service` | Next.js on 127.0.0.1:3000 |
| `deploy/ubuntu/*` | prereqs / deploy / rollback / healthcheck / README |
| `deploy/docker/*` | compose + Dockerfiles + env example |
| `backend/.env.production.example` | safe prod backend env |
| `frontend/.env.production.example` | `NEXT_PUBLIC_API_URL` only |
| `scripts/build_static_demo_release.ps1` | static zip builder |
| `scripts/build_full_release.ps1` | full product zip builder |
| `scripts/deploy_preflight.ps1` | local readiness checks |
| `DEPLOY_SECURITY_AUDIT.md` | secrets hygiene |
| `DEPLOY_RELEASE_CHECKLIST.md` | release checklist |

## 4. Build Results

| Check | Result |
|---|---|
| `python -m compileall backend` | PASS |
| Algofusion pytest (3 files) | 9 passed |
| product/university/wow/llm pytest | 39 passed |
| `npm run lint` | PASS |
| `npm run build` | PASS |
| `GET http://127.0.0.1:8001/health` | 200 `{"status":"ok"}` |
| `GET http://localhost:3000` | 200 |
| Browser smoke (IronBee) | Home + Showcase OK; known optional `/semantic-landing` 404 |

## 5. Release Artifacts

| Artifact | Path | Status |
|---|---|---|
| Static demo zip | `.runtime/release/ai-landing-static-demo.zip` | OK (~1.9 MB) |
| Static folder | `.runtime/release/static-demo/` | OK (index + wow + showcase + standard) |
| Full product zip | `.runtime/release/ai-landing-full-product.zip` | OK (~3.9 MB) |
| Full stage | `.runtime/release/full-product/` | OK (no `.env` / `.venv` / `node_modules` / `.git`) |

## 6. Deployment Modes

| Mode | Status | Recommendation |
|---|---|---|
| A — Static demo only | READY WHEN SERVER PROVIDED | **First public step** — lowest risk |
| B — systemd + nginx | READY WHEN SERVER PROVIDED | **Recommended for full product** |
| C — Docker Compose | DRAFT | Experimental; not primary |

## 7. Server Info Still Needed

1. OS (Ubuntu 22.04/24.04 expected)
2. IP / hostname
3. SSH user
4. SSH port
5. Domain / subdomain
6. Deploy path (default `/opt/ai-landing-factory`)
7. SSL strategy
8. Docker allowed yes/no
9. nginx already installed yes/no
10. Public vs basic auth / internal only
11. FreeModel / AI on server yes/no (default: **no**, mock mode)

## 8. Next Command After Server Params

1. Confirm Mode A or B.
2. For A: upload `.runtime/release/ai-landing-static-demo.zip` + apply `deploy/nginx/ai-landing-static.conf`.
3. For B: follow `deploy/ubuntu/README_FULL_SYSTEMD_DEPLOY.md` with placeholders filled; use `deploy/ubuntu/deploy_release.sh` on the server.
4. Run `deploy/ubuntu/healthcheck.sh`.
5. Do **not** enable FreeModel until budget/key explicitly approved.

## 9. Entry points verified

- Backend module: `app.main:app` (WorkingDirectory `backend/`)
- Frontend start: `npm run start -- --hostname 127.0.0.1 --port 3000`
- API prefix: `/api/v1` (nginx maps public `/api/` → backend `/api/v1/`)
