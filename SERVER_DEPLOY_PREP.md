# Server Deploy Preparation

## 1. Current Local Status

| Поле | Значение |
|---|---|
| Project | `C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh` |
| Branch | `main` |
| UAT status | Локальный UAT — **PASS**; DOCX Algofusion — **PASS** |
| Deploy prep | **READY FOR DOCKER-FIRST** (`DEPLOY_PREP_REPORT.md`) |
| Server audit | **DONE** — `SERVER_AUDIT_UII_DEV.md` |
| AI status | FreeModel — **BLOCKED**, `LLM_PROVIDER=mock` |
| Primary mode | **Docker-first** (docker-compose v1) + optional nginx |

## 2. Server Audit Summary (UII dev)

| Field | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| IP | `195.209.213.170` |
| SSH user | `dkravchenko` |
| Docker | 29.1.3 installed, **sudo required** |
| docker-compose | **v1.29.2** (`docker-compose` command) |
| docker compose v2 | **absent** |
| nginx / caddy / apache | **not installed** |
| Ports 80/443 | **free** |
| `/opt/ai-portal` | **exists — DO NOT TOUCH** |
| `/var/www` | absent |
| Deploy path | `/opt/ai-landing-factory` (create) |
| RAM / Disk | sufficient |

## 3. Deployment Mode Candidates

| Mode | Fit | Pros | Cons | Recommendation |
|---|---|---|---|---|
| **C. Docker-first + nginx** | **Отличный** | Docker уже есть; изоляция; rollback через compose | sudo для docker; nginx ставить отдельно | **Primary для UII dev** |
| **A. Static demo only** | Хороший | Минимальный риск | Нет upload/generate | Опционально для первого показа |
| **B. systemd + nginx** | Средний | Без контейнеров | venv/node на хосте | Fallback |

Артефакты:

- Full zip: `.runtime/release/ai-landing-full-product.zip`
- Static zip: `.runtime/release/ai-landing-static-demo.zip`
- Docker runbook: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`
- nginx (Docker): `deploy/nginx/ai-landing-docker.conf`

## 4. Docker Port Mapping (loopback)

| Service | Host bind | Container | Public via nginx |
|---|---|---|---|
| Backend | `127.0.0.1:18001` | `8001` | `/api/`, `/health` |
| Frontend | `127.0.0.1:13000` | `3000` | `/` |

**Не публиковать** 18001/13000 на `0.0.0.0`. nginx — единственная публичная точка.

## 5. Required Environment Variables

Шаблоны:

- `deploy/docker/.env.docker.example` — **primary for Docker deploy**
- `backend/.env.production.example` — systemd fallback
- `frontend/.env.production.example` — build-time URL

Docker `.env` (в `deploy/docker/.env`):

| Variable | Example | Notes |
|---|---|---|
| `LLM_PROVIDER` | `mock` | AI off |
| `LLM_ENABLED` | `false` | |
| `BACKEND_CORS_ORIGINS` | `http://<DOMAIN>,https://<DOMAIN>` | after nginx |
| `NEXT_PUBLIC_API_URL` | `http://<DOMAIN>/api/v1` | rebuild frontend image after change |

## 6. Still Needed from Operator

1. `<DOMAIN>` / DNS A-record → `195.209.213.170`
2. SSL strategy (certbot after nginx)
3. Explicit **deploy GO** (SSH execution)
4. FreeModel yes/no — default **no**

## 7. Pre-Deploy Checklist

- [x] Local UAT passed
- [x] Server audited (`SERVER_AUDIT_UII_DEV.md`)
- [x] docker-compose v1 package ready
- [x] nginx docker template ready
- [x] Full release zip rebuilt
- [ ] FreeModel smoke — **BLOCKED**
- [ ] Domain / DNS confirmed
- [ ] Deploy execution — **NOT DONE**

## 8. Suggested Commands (Docker-first)

**Не выполнять автоматически. Только на сервере после явного GO.**

```bash
# 1. layout
sudo mkdir -p /opt/ai-landing-factory/releases
# upload + unzip ai-landing-full-product.zip
sudo ln -sfn /opt/ai-landing-factory/releases/<ID> /opt/ai-landing-factory/current

# 2. env
cd /opt/ai-landing-factory/current/deploy/docker
sudo cp .env.docker.example .env && sudo chmod 600 .env
# edit BACKEND_CORS_ORIGINS, NEXT_PUBLIC_API_URL

# 3. containers (v1 — sudo required)
sudo docker-compose build
sudo docker-compose up -d
sudo docker-compose ps
curl -fsS http://127.0.0.1:18001/health
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:13000/

# 4. public HTTP (nginx not preinstalled)
sudo apt-get install -y nginx
sudo cp deploy/nginx/ai-landing-docker.conf /etc/nginx/sites-available/
# edit server_name
sudo nginx -t && sudo systemctl reload nginx
```

Полный runbook: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`.

## 9. Rollback (Docker)

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose down
sudo ln -sfn /opt/ai-landing-factory/releases/<PREV> /opt/ai-landing-factory/current
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose up -d
curl -fsS http://127.0.0.1:18001/health
```

## 10. Constraints

- **Do not touch** `/opt/ai-portal`
- Use **`sudo docker-compose`**, not `docker compose`
- No git push / no deploy execution during prep
- FreeModel disabled
