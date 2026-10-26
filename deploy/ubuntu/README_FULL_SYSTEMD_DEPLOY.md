# Full product deploy — systemd + nginx (Ubuntu 22.04 / 24.04)

> **Основной способ выкладки — Docker:** [`README_DOCKER_FIRST_DEPLOY.md`](README_DOCKER_FIRST_DEPLOY.md). Он проверен целиком и не требует nginx на сервере.
> Если всё же ставить через systemd, учесть три вещи. `DATA_DIR` в `shared/backend.env` должен указывать вне папки релиза, иначе учётные записи и библиотека пропадут с новым релизом. У фронтенда нужен `INTERNAL_API_URL=http://127.0.0.1:8001/api/v1`. nginx должен пропускать `/api/v1/` без изменения пути (`deploy/nginx/ai-landing-full.conf`). Подробности — `docs/ACCOUNTS_AND_LIBRARY.md`.


**Status:** template / ready when server params provided.  
**Do not run against production until SSH/IP/domain are known.**

Recommended mode for the full product. Static demo is safer for first public show.

## Requirements

- Ubuntu 22.04 or 24.04 LTS
- Python 3.10+ (3.12 preferred)
- Node.js 20+
- nginx
- sudo access
- Ports 80 (and later 443) free for nginx
- Loopback ports `127.0.0.1:8001` (backend) and `127.0.0.1:3000` (frontend)

## Server layout

```
/opt/ai-landing-factory/
  current -> releases/<RELEASE_ID>
  releases/<RELEASE_ID>/     # unpacked full-product zip
  shared/
    backend.env              # chmod 600
    frontend.env             # chmod 600 (optional at runtime)
/var/www/ai-landing-demo/    # optional static fallback
```

Placeholders used below:

| Placeholder | Meaning |
|---|---|
| `<SERVER_IP>` | server address |
| `<SSH_USER>` | SSH login |
| `<SSH_PORT>` | SSH port (default 22) |
| `<DOMAIN>` | public hostname |
| `<DEPLOY_PATH>` | default `/opt/ai-landing-factory` |

## Upload release archive

On the operator machine (after `scripts/build_full_release.ps1`):

```bash
scp -P <SSH_PORT> .runtime/release/ai-landing-full-product.zip <SSH_USER>@<SERVER_IP>:/tmp/
scp -P <SSH_PORT> -r deploy/ubuntu <SSH_USER>@<SERVER_IP>:/tmp/alf-ubuntu/
```

## Install prerequisites

```bash
ssh -p <SSH_PORT> <SSH_USER>@<SERVER_IP>
sudo bash /tmp/alf-ubuntu/install_prereqs.sh
```

## Create backend .env

```bash
sudo mkdir -p <DEPLOY_PATH>/shared
sudo install -m 600 /dev/null <DEPLOY_PATH>/shared/backend.env
sudo nano <DEPLOY_PATH>/shared/backend.env
```

Copy from `backend/.env.production.example`, then set at least:

- `BACKEND_CORS_ORIGINS=https://<DOMAIN>`
- `LLM_PROVIDER=mock` / `LLM_ENABLED=false` unless AI is approved
- leave `OPENAI_API_KEY` empty for mock mode

## Create frontend .env.production

Build-time file (before `npm run build`):

```bash
# inside release frontend/
cp .env.production.example .env.production
# set NEXT_PUBLIC_API_URL=https://<DOMAIN>/api/v1
```

Or export env before build:

```bash
export NEXT_PUBLIC_API_URL=https://<DOMAIN>/api/v1
npm ci && npm run build
```

## Install Python deps

```bash
cd <DEPLOY_PATH>/current
python3 -m venv .venv
./.venv/bin/pip install -r backend/requirements.txt
```

## Install Node deps + build frontend

```bash
cd <DEPLOY_PATH>/current/frontend
npm ci
npm run build
```

## Install systemd units

```bash
sudo cp <DEPLOY_PATH>/current/deploy/systemd/alf-backend.service /etc/systemd/system/
sudo cp <DEPLOY_PATH>/current/deploy/systemd/alf-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alf-backend alf-frontend
```

Units bind:

- backend: `127.0.0.1:8001` (`uvicorn app.main:app`)
- frontend: `127.0.0.1:3000` (`npm run start`)

## Install nginx config

```bash
sudo tee /etc/nginx/conf.d/map-connection.conf >/dev/null <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
EOF

sudo cp <DEPLOY_PATH>/current/deploy/nginx/ai-landing-full.conf \
  /etc/nginx/sites-available/ai-landing-full.conf
# edit server_name YOUR_DOMAIN -> <DOMAIN>
sudo ln -sfn /etc/nginx/sites-available/ai-landing-full.conf \
  /etc/nginx/sites-enabled/ai-landing-full.conf
sudo nginx -t && sudo systemctl reload nginx
```

Routing:

- `/api/` → `http://127.0.0.1:8001/api/v1/`
- `/health` → `http://127.0.0.1:8001/health`
- `/` → `http://127.0.0.1:3000`
- `client_max_body_size 50m`

## One-shot deploy script

```bash
sudo DEPLOY_PATH=<DEPLOY_PATH> bash deploy/ubuntu/deploy_release.sh \
  /tmp/ai-landing-full-product.zip <RELEASE_ID>
```

## Healthcheck

```bash
bash <DEPLOY_PATH>/current/deploy/ubuntu/healthcheck.sh
# or:
curl -fsS http://127.0.0.1:8001/health
curl -I http://127.0.0.1:3000/
curl -I http://<DOMAIN>/health
```

## Logs

```bash
sudo journalctl -u alf-backend -f
sudo journalctl -u alf-frontend -f
sudo tail -f /var/log/nginx/error.log
```

## Rollback

```bash
sudo bash <DEPLOY_PATH>/current/deploy/ubuntu/rollback.sh <PREV_RELEASE_ID>
```

Also keep a static demo fallback (`deploy/static`) if the full stack fails.

## Troubleshooting

| Symptom | Check |
|---|---|
| 502 Bad Gateway | `systemctl status alf-backend alf-frontend`; ports 8001/3000 |
| CORS errors | `BACKEND_CORS_ORIGINS` must include `https://<DOMAIN>` |
| Upload fails | nginx `client_max_body_size`; backend disk under `backend/data` |
| Blank API | frontend built with wrong `NEXT_PUBLIC_API_URL` — rebuild |
| Permission denied on data | ensure service user can write `backend/data` |

## SSL

Not automated here. After HTTP works:

```bash
# example only — requires certbot package and DNS pointing to <SERVER_IP>
sudo certbot --nginx -d <DOMAIN>
```

## Security notes

- Never commit real `.env`
- `chmod 600` on `shared/backend.env`
- Keep uvicorn/Next on loopback only; nginx is the public edge
- FreeModel / paid AI: keep disabled until explicitly approved
