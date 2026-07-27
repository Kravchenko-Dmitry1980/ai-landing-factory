# Docker Compose deploy (docker-compose v1)

**Primary deploy mode for UII dev server** (Ubuntu 24.04, Docker 29.x, `docker-compose` 1.29.x).

Uses **`sudo docker-compose`** (v1). The `docker compose` v2 plugin is **not required**.

Runbook: [`deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`](../ubuntu/README_DOCKER_FIRST_DEPLOY.md)  
Server audit: [`SERVER_AUDIT_UII_DEV.md`](../../SERVER_AUDIT_UII_DEV.md)

## What is included

| File | Purpose |
|---|---|
| `docker-compose.yml` | backend + frontend (compose file v3.8, v1 compatible) |
| `backend.Dockerfile` | FastAPI / uvicorn image |
| `frontend.Dockerfile` | Next.js production image |
| `.env.docker.example` | safe env template (no secrets) |
| `../nginx/ai-landing-docker.conf` | nginx → loopback Docker ports |

## Server ports (loopback only)

| Service | Host bind | Container |
|---|---|---|
| Backend | `127.0.0.1:18001` | `8001` |
| Frontend | `127.0.0.1:13000` | `3000` |

Public access: install nginx and use `deploy/nginx/ai-landing-docker.conf`.

## Ubuntu 24.04 — UII dev server facts

| Item | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| Docker | 29.1.3 installed |
| docker-compose | **v1.29.2** (`docker-compose` command) |
| docker compose plugin | **absent** — do not use `docker compose` |
| Docker socket | requires **`sudo`** for user `dkravchenko` |
| nginx / caddy / apache | **not installed** |
| `/var/www` | **absent** |
| `/opt/ai-portal` | **exists — do not touch** |
| Deploy path | `/opt/ai-landing-factory` (create) |
| Ports 80/443 | free |
| FreeModel / AI | **disabled** (`LLM_PROVIDER=mock`) |

## Server deploy (summary)

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo cp .env.docker.example .env
# edit .env — set BACKEND_CORS_ORIGINS and NEXT_PUBLIC_API_URL for your DOMAIN
sudo docker-compose build
sudo docker-compose up -d
sudo docker-compose ps
curl -fsS http://127.0.0.1:18001/health
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:13000/
```

Full steps: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`.

## Local preview (optional, Windows/Linux)

```bash
cd deploy/docker
cp .env.docker.example .env
# Linux with sudo:
sudo docker-compose build
sudo docker-compose up -d
# Windows Docker Desktop (if socket available without sudo):
docker-compose build
docker-compose up -d
```

- Frontend: http://127.0.0.1:13000
- Backend: http://127.0.0.1:18001/health

## docker-compose v1 notes

- File format: `version: '3.8'`
- Use `sudo docker-compose`, not `docker compose`
- `depends_on` without `condition: service_healthy` (v1 limitation)
- Backend healthcheck still runs; frontend may start before backend is fully ready — retry curl if needed
- Build context `../..` = repository root when compose file is in `deploy/docker/`

## Environment

Copy `.env.docker.example` → `.env` in `deploy/docker/`:

```bash
sudo cp .env.docker.example .env
sudo chmod 600 .env
```

Key variables for nginx / SSH-tunnel public access:

```env
BACKEND_CORS_ORIGINS=http://127.0.0.1:8080,http://localhost:8080,http://YOUR_DOMAIN
NEXT_PUBLIC_API_URL=/api/v1
INTERNAL_API_URL=http://backend:8001/api/v1
```

| Variable | Used by | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Browser / client bundle | Relative `/api/v1` via nginx is correct |
| `INTERNAL_API_URL` | Next.js SSR (Node) | Must be absolute; Docker DNS `backend:8001` |

Rebuild frontend after changing either URL:

```bash
sudo docker-compose build frontend
sudo docker rm -f alf-frontend
# --no-deps avoids docker-compose v1 KeyError: ContainerConfig on backend recreate
sudo docker-compose up -d --no-deps --no-build frontend
```

## Rollback

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose down
# restore previous release directory + .env backup, then:
sudo docker-compose up -d
```

## Other modes

| Mode | Use when |
|---|---|
| Static demo | First public show, zero backend risk |
| Docker + nginx | **UII dev server (recommended now)** |
| systemd + nginx | Bare-metal without Docker |

## Security

- Volume `alf_backend_data` → `/app/backend/data`
- OCR/VLM disabled in example env
- FreeModel/OpenAI keys: leave empty unless explicitly approved
- Do not publish 18001/13000 beyond loopback; nginx is the public edge
