# Server Deploy Preparation

## 1. Current Local Status

| Поле | Значение |
|---|---|
| Project | `C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh` |
| Branch | `main` |
| UAT status | Локальный UAT — **PASS**; DOCX Algofusion repair — **PASS** |
| Deploy prep | **READY FOR SERVER PARAMS** (`DEPLOY_PREP_REPORT.md`) |
| AI status | FreeModel — **BLOCKED**, продукт работает в `LLM_PROVIDER=mock` |
| Stack | Backend: Python 3.12 + FastAPI/uvicorn (`app.main:app`). Frontend: Next.js 15 (`npm run start`). Хранилище: файловое (`backend/data`) |
| Docker / systemd / nginx | **Черновики готовы** в `deploy/` |

## 2. Deployment Mode Candidates

| Mode | Fit | Pros | Cons | Recommendation |
|---|---|---|---|---|
| **A. Static demo only** | Отличный | nginx + файлы; ноль AI/backend риска | Нет upload/generate | **Шаг 1 — сделать сразу** |
| **B. systemd + nginx** | Хороший | Ближе к локальному запуску; rollback по symlink | Ручная настройка venv/node | **Шаг 2 — рекомендуемый full product** |
| **C. Docker Compose** | Средний | Изоляция | Experimental draft | Позже при необходимости |

Артефакты:

- Static: `.runtime/release/ai-landing-static-demo.zip`
- Full: `.runtime/release/ai-landing-full-product.zip`
- Docs: `deploy/static/`, `deploy/ubuntu/`, `deploy/docker/`

## 3. Required Server Info

Перед реальным деплоем нужны:

1. OS сервера (ожидается Ubuntu 22.04/24.04 LTS)
2. IP / hostname
3. SSH user
4. SSH port
5. Deploy path (например `/opt/ai-landing-factory`)
6. Domain / subdomain
7. SSL-стратегия (Let's Encrypt / готовый сертификат / без TLS)
8. Docker allowed: yes/no
9. nginx уже установлен: yes/no
10. Публичный доступ или только внутренняя сеть / basic auth
11. Стратегия секретов (файл `.env` chmod 600 / systemd `EnvironmentFile`)
12. Нужен ли AI-контур (FreeModel) или деплоим в `mock`-режиме
13. Ожидаемая нагрузка и объём загружаемых файлов

## 4. Required Environment Variables

См. актуальные шаблоны:

- `backend/.env.production.example`
- `frontend/.env.production.example`
- `deploy/docker/.env.docker.example`
- `backend/.env.example` (обновлён: `OPENAI_BASE_URL`, комментарий CORS)

Ключевые production-значения:

| Variable | Example | Notes |
|---|---|---|
| `PRODUCT_MODE` | `simple` | |
| `LLM_ENABLED` | `false` | |
| `LLM_PROVIDER` | `mock` | AI off by default |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | FreeModel URL только при явном GO |
| `OPENAI_API_KEY` | _(empty)_ | secret |
| `BACKEND_CORS_ORIGINS` | `https://your-domain.example` | **required on server** |
| `NEXT_PUBLIC_API_URL` | `https://your-domain.example/api/v1` | public, no secrets |

## 5. Ports

| Service | Bind | Public? |
|---|---|---|
| Backend uvicorn | `127.0.0.1:8001` | нет |
| Frontend Next | `127.0.0.1:3000` | нет |
| nginx | `80` / later `443` | да |

Nginx mapping (full mode):

- `/api/` → `http://127.0.0.1:8001/api/v1/`
- `/health` → `http://127.0.0.1:8001/health`
- `/` → `http://127.0.0.1:3000`
- `client_max_body_size 50m`

## 6. Files Not To Commit

- `backend/.env`, `frontend/.env.local`, любые реальные ключи
- `.runtime/` (включая release zip — локальные артефакты)
- `logs/`, `backend/data/`
- мусорный `-files logs`

Можно коммитить: `*.env.*.example`, `deploy/**`, scripts, reports.

## 7. Pre-Deploy Checklist

- [x] Local UAT passed
- [ ] FreeModel smoke — **BLOCKED**
- [x] Backend health OK
- [x] Frontend build OK
- [x] Demo pack / static zip OK
- [x] `.env.production.example` templates
- [x] secrets absent from git
- [x] nginx / systemd / ubuntu / docker drafts
- [x] rollback script ready (`deploy/ubuntu/rollback.sh`)
- [ ] server access confirmed
- [ ] deploy mode selected with user after params

## 8. Suggested Ubuntu Commands

**Не выполнять до предоставления доступа и явного подтверждения.**

Static:

```bash
sudo mkdir -p /var/www/ai-landing-demo
sudo unzip -o ai-landing-static-demo.zip -d /var/www/ai-landing-demo
# apply deploy/nginx/ai-landing-static.conf
sudo nginx -t && sudo systemctl reload nginx
```

Full:

```bash
sudo bash deploy/ubuntu/install_prereqs.sh
sudo DEPLOY_PATH=/opt/ai-landing-factory bash deploy/ubuntu/deploy_release.sh \
  /tmp/ai-landing-full-product.zip 20260726_1
sudo bash /opt/ai-landing-factory/current/deploy/ubuntu/healthcheck.sh
```

Полный runbook: `deploy/ubuntu/README_FULL_SYSTEMD_DEPLOY.md`.

## 9. Rollback Plan

| Шаг | Действие |
|---|---|
| Prev release | `/opt/ai-landing-factory/releases/<prev>` |
| Switch | `sudo bash deploy/ubuntu/rollback.sh <PREV_RELEASE_ID>` |
| Verify | `curl -fsS http://127.0.0.1:8001/health` |
| Emergency | nginx → static demo (`/var/www/ai-landing-demo`) |

## 10. Stop-list (still in force)

No push, no SSH/SCP deploy, no DNS/SSL issuance, no FreeModel smoke, no deletion of user data — until explicit server params + approval.
