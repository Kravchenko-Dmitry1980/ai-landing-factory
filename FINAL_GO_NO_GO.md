# Final GO / NO-GO

Дата: 2026-07-27 · Основание: `SERVER_AUDIT_UII_DEV.md`, `DEPLOY_PREP_REPORT.md`, `UAT_ALGOFUSION_DOCX_REPAIR_REPORT.md`

## Decision

| Контур | Решение |
|---|---|
| Локальная демонстрация | **GO** |
| DOCX Algofusion full-content pipeline | **GO** |
| Продукт без AI (`LLM_PROVIDER=mock`) | **GO** |
| Показ демо-пака offline | **GO** |
| Server audit (UII dev) | **DONE** |
| Deploy package (Docker-first v1) | **READY** |
| Static demo deploy | **READY** |
| Docker-first deploy (UII dev) | **READY WHEN DEPLOY GO** |
| systemd + nginx deploy | **READY** (fallback) |
| FreeModel / AI-контур | **NO-GO** |
| Production deploy execution | **NO-GO** — deploy not executed yet |

Итог: **GO FOR DEMO + READY FOR DOCKER-FIRST DEPLOY ON UII DEV SERVER.**

## Server (audited)

- Ubuntu 24.04.4 LTS · `195.209.213.170` · `dkravchenko`
- Docker 29.1.3 + docker-compose 1.29.2 (sudo required)
- `/opt/ai-portal` — не трогать
- Deploy path: `/opt/ai-landing-factory`
- nginx not installed; 80/443 free

## Facts (Deploy prep — Docker-first)

- `docker-compose.yml` v3.8 compatible with v1.29.2
- Loopback ports: backend `18001`, frontend `13000`
- `deploy/nginx/ai-landing-docker.conf` for public access
- Runbook: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`
- Full release zip rebuilt locally
- git push / server deploy / FreeModel — не выполнялись

## Blockers

- Deploy execution awaits explicit GO + `<DOMAIN>` if public HTTP needed
- FreeModel не включать без явного запроса

## What to open

- Server audit: `SERVER_AUDIT_UII_DEV.md`
- Docker deploy: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`
- Docker README: `deploy/docker/README_DOCKER_DEPLOY.md`
