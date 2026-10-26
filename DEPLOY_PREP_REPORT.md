# Deploy Prep Report

> Отчёт подготовки от июля 2026, команды в нём устарели. Актуальная инструкция выкладки: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`.

Дата: 2026-07-27  
Проект: `C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh`  
Ветка: `main`

## 1. Status

**READY FOR DOCKER-FIRST DEPLOY (SERVER AUDITED)**

Серверный аудит UII dev выполнен (`SERVER_AUDIT_UII_DEV.md`). Deploy package адаптирован под **docker-compose v1** + loopback ports + nginx template. Реальный деплой на сервер **не выполнялся**.

## 2. Scope Completed

| Area | Status | Notes |
|---|---|---|
| Mode A — static demo | DONE | zip + nginx template |
| Mode B — systemd + nginx | DONE | alternative path |
| Mode C — Docker-first | DONE | **primary for UII dev server** |
| docker-compose v1 compat | DONE | `version: '3.8'`, `sudo docker-compose` |
| Server audit doc | DONE | `SERVER_AUDIT_UII_DEV.md` |
| nginx docker template | DONE | `ai-landing-docker.conf` → 13000/18001 |
| Docker-first runbook | DONE | `README_DOCKER_FIRST_DEPLOY.md` |
| Env templates | DONE | `.env.docker.example` updated |
| Release archives | DONE | full zip rebuilt |
| Server deploy | NOT DONE | awaiting explicit deploy GO |
| FreeModel / AI | NO-GO | not touched |

## 3. Created / Updated Files

| File | Purpose |
|---|---|
| `deploy/docker/docker-compose.yml` | v1 compatible, loopback 13000/18001 |
| `deploy/docker/README_DOCKER_DEPLOY.md` | primary docker docs, Ubuntu 24.04 section |
| `deploy/nginx/ai-landing-docker.conf` | nginx → Docker loopback |
| `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md` | step-by-step server runbook |
| `SERVER_AUDIT_UII_DEV.md` | audited server facts |
| `SERVER_DEPLOY_PREP.md` | updated recommendation |
| `FINAL_GO_NO_GO.md` | Docker-first READY |

## 4. Build Results

| Check | Result |
|---|---|
| Prior backend/frontend tests | PASS (unchanged) |
| Full release zip rebuild | PASS |
| Zip forbidden entries check | PASS (no `.env`/`.git`/`.venv`/`node_modules`/`backend/data`) |

## 5. Release Artifacts

| Artifact | Path | Status |
|---|---|---|
| Full product zip | `.runtime/release/ai-landing-full-product.zip` | rebuilt |
| Static demo zip | `.runtime/release/ai-landing-static-demo.zip` | unchanged |

## 6. Deployment Modes

| Mode | Status | Recommendation |
|---|---|---|
| A — Static demo | READY | Optional first show |
| B — systemd + nginx | READY | Bare-metal fallback |
| C — Docker-first (v1) | **READY FOR UII DEV** | **Primary for 195.209.213.170** |

## 7. Server Facts (audited)

| Field | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| IP | 195.209.213.170 |
| User | dkravchenko |
| Docker | 29.1.3 (sudo required) |
| docker-compose | v1.29.2 |
| docker compose plugin | absent |
| nginx | not installed (80/443 free) |
| `/opt/ai-portal` | exists — do not touch |
| Deploy path | `/opt/ai-landing-factory` |

## 8. Still Needed

1. `<DOMAIN>` / DNS
2. SSL plan
3. Explicit deploy GO (SSH execution)
4. FreeModel decision (default: no)

## 9. Next Commands (on server, after upload)

```bash
sudo mkdir -p /opt/ai-landing-factory/releases
# unzip ai-landing-full-product.zip → current
cd /opt/ai-landing-factory/current/deploy/docker
sudo cp .env.docker.example .env && sudo chmod 600 .env
sudo docker-compose build
sudo docker-compose up -d
curl http://127.0.0.1:18001/health
```

See `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`.

## 10. Docker ports

| Service | Loopback |
|---|---|
| Backend | `127.0.0.1:18001` |
| Frontend | `127.0.0.1:13000` |
| nginx public | 80 → loopback |
