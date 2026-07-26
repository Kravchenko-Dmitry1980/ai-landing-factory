# Docker Compose draft (experimental)

**Not the primary deploy mode.** Prefer systemd + nginx (`deploy/ubuntu/`).

This draft is for local/container preview reproducibility. It must not replace current `.\run.ps1` local workflow.

## What is included

| File | Purpose |
|---|---|
| `docker-compose.yml` | backend + frontend services |
| `backend.Dockerfile` | FastAPI / uvicorn image |
| `frontend.Dockerfile` | Next.js production image |
| `.env.docker.example` | safe env template (no secrets) |

## Requirements

- Docker Engine + Compose v2
- Copy `.env.docker.example` → `.env` in this folder (gitignored if named `.env`)

## Local preview (optional)

```bash
cd deploy/docker
cp .env.docker.example .env
# edit .env if needed — leave API keys empty for mock mode
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8001/health

Ports are for **local docker preview only**. On a real server, put a reverse proxy in front and avoid publishing backend publicly.

## Notes

- Volume `alf_backend_data` mounts to `/app/backend/data`
- Backend healthcheck hits `/health`
- Frontend `depends_on` backend (service_healthy)
- OCR/VLM stay disabled in the example env
- FreeModel/OpenAI keys: do not bake into images

## Recommendation

| Mode | Use when |
|---|---|
| Static demo | First public show, zero risk |
| systemd + nginx | Full product on Ubuntu |
| Docker Compose | Later, if ops require containers |
