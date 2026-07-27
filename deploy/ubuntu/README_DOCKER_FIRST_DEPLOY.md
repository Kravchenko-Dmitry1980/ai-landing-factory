# Docker-first deploy — Ubuntu 24.04 (UII dev server)

**Target server:** `195.209.213.170` · user `dkravchenko` · Ubuntu 24.04.4 LTS

**Do not execute from Windows automatically.** Run these commands on the server via SSH after uploading the release archive.

Primary tool: **`sudo docker-compose`** (v1.29.2). Do **not** use `docker compose` (plugin absent).

Full audit: [`SERVER_AUDIT_UII_DEV.md`](../../SERVER_AUDIT_UII_DEV.md)

## Constraints

| Rule | Detail |
|---|---|
| Do not touch | `/opt/ai-portal` (existing) |
| Create | `/opt/ai-landing-factory` |
| Docker | requires `sudo` for `dkravchenko` |
| nginx | not installed — install only if public HTTP needed |
| AI | `LLM_PROVIDER=mock`, FreeModel **disabled** |

## Loopback ports

| Service | URL |
|---|---|
| Backend | `http://127.0.0.1:18001/health` |
| Frontend | `http://127.0.0.1:13000/` |

## 1. Prepare directory

```bash
ssh dkravchenko@195.209.213.170

sudo mkdir -p /opt/ai-landing-factory/releases
# verify ai-portal untouched:
ls -la /opt/ai-portal
```

## 2. Upload release (from operator machine)

```bash
scp ai-landing-full-product.zip dkravchenko@195.209.213.170:/tmp/
```

## 3. Unpack release

```bash
RELEASE_ID=20260727_1
sudo mkdir -p /opt/ai-landing-factory/releases/${RELEASE_ID}
sudo unzip -o /tmp/ai-landing-full-product.zip -d /opt/ai-landing-factory/releases/${RELEASE_ID}

# flatten single top-level folder if present
cd /opt/ai-landing-factory/releases/${RELEASE_ID}
if [ $(find . -mindepth 1 -maxdepth 1 | wc -l) -eq 1 ]; then
  ONLY=$(find . -mindepth 1 -maxdepth 1)
  [ -d "$ONLY" ] && sudo sh -c "shopt -s dotglob && mv \"$ONLY\"/* . && rmdir \"$ONLY\""
fi

sudo ln -sfn /opt/ai-landing-factory/releases/${RELEASE_ID} /opt/ai-landing-factory/current
```

## 4. Create environment files

```bash
cd /opt/ai-landing-factory/current/deploy/docker

sudo cp .env.docker.example .env
sudo chmod 600 .env
sudo nano .env
```

Set at minimum (replace `<DOMAIN>`):

```env
BACKEND_CORS_ORIGINS=http://<DOMAIN>,https://<DOMAIN>
NEXT_PUBLIC_API_URL=http://<DOMAIN>/api/v1
LLM_ENABLED=false
LLM_PROVIDER=mock
```

Optional shared copies for documentation:

```bash
sudo mkdir -p /opt/ai-landing-factory/shared
sudo cp .env /opt/ai-landing-factory/shared/backend.env
sudo chmod 600 /opt/ai-landing-factory/shared/backend.env
# frontend env is baked at docker build via NEXT_PUBLIC_API_URL in .env
sudo grep NEXT_PUBLIC /opt/ai-landing-factory/shared/backend.env \
  | sudo tee /opt/ai-landing-factory/shared/frontend.env
sudo chmod 600 /opt/ai-landing-factory/shared/frontend.env
```

## 5. Build and start containers

```bash
cd /opt/ai-landing-factory/current/deploy/docker

sudo docker-compose build
sudo docker-compose up -d
sudo docker-compose ps
```

Expected: `alf-backend` and `alf-frontend` running, ports `127.0.0.1:18001` and `127.0.0.1:13000`.

## 6. Health checks (loopback)

```bash
curl -fsS http://127.0.0.1:18001/health
curl -fsS -o /dev/null -w "frontend HTTP %{http_code}\n" http://127.0.0.1:13000/
sudo docker-compose logs --tail=50 backend
sudo docker-compose logs --tail=50 frontend
```

## 7. Public access via nginx (optional)

nginx is **not** preinstalled. Install only when `<DOMAIN>` should serve HTTP:

```bash
sudo apt-get update
sudo apt-get install -y nginx

sudo tee /etc/nginx/conf.d/map-connection.conf >/dev/null <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
EOF

sudo cp /opt/ai-landing-factory/current/deploy/nginx/ai-landing-docker.conf \
  /etc/nginx/sites-available/ai-landing-docker.conf
# edit server_name YOUR_DOMAIN -> <DOMAIN>
sudo nano /etc/nginx/sites-available/ai-landing-docker.conf
sudo ln -sfn /etc/nginx/sites-available/ai-landing-docker.conf \
  /etc/nginx/sites-enabled/ai-landing-docker.conf

sudo nginx -t
sudo systemctl reload nginx

curl -fsS -o /dev/null -w "nginx /health HTTP %{http_code}\n" http://<DOMAIN>/health
curl -fsS -o /dev/null -w "nginx / HTTP %{http_code}\n" http://<DOMAIN>/
```

## 8. Rollback

```bash
cd /opt/ai-landing-factory/current/deploy/docker

# stop current stack
sudo docker-compose down

# switch symlink to previous release
PREV_ID=<PREVIOUS_RELEASE_ID>
sudo ln -sfn /opt/ai-landing-factory/releases/${PREV_ID} /opt/ai-landing-factory/current

# restore .env backup if needed
sudo cp /opt/ai-landing-factory/shared/backend.env.backup \
  /opt/ai-landing-factory/current/deploy/docker/.env

cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose up -d
curl -fsS http://127.0.0.1:18001/health
```

Before upgrade, backup:

```bash
sudo cp /opt/ai-landing-factory/current/deploy/docker/.env \
  /opt/ai-landing-factory/shared/backend.env.backup
sudo chmod 600 /opt/ai-landing-factory/shared/backend.env.backup
sudo docker run --rm -v alf_backend_data:/data -v /tmp:/backup \
  alpine tar czf /backup/alf-data-$(date +%F).tgz -C /data .
```

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `permission denied` on docker | prefix with `sudo` |
| `docker compose` not found | use `docker-compose` (v1) |
| frontend 502 / empty API | rebuild after `.env` change: `sudo docker-compose build frontend && sudo docker-compose up -d` |
| CORS errors | fix `BACKEND_CORS_ORIGINS` in `.env`, restart backend |
| upload fails via nginx | check `client_max_body_size 50m` in nginx config |
| port conflict on 13000/18001 | `sudo ss -tlnp \| grep -E '13000\|18001'` |

## 10. What not to do

- Do not modify `/opt/ai-portal`
- Do not enable FreeModel without explicit approval
- Do not publish 18001/13000 to `0.0.0.0` — keep loopback + nginx
