# Server Audit — UII Dev

Дата: 2026-07-27  
Сервер: UII dev / production candidate  
**Deploy не выполнялся** — только аудит и адаптация пакета.

## Identity

| Field | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| IP | `195.209.213.170` |
| SSH user | `dkravchenko` |
| SSH port | 22 (occupied, standard) |

## Existing layout

| Path | Status | Action |
|---|---|---|
| `/opt/ai-portal` | **exists** | **DO NOT TOUCH** |
| `/var/www` | absent | not required for Docker-first |
| `/opt/ai-landing-factory` | to create | recommended deploy root |

## Web stack

| Component | Status |
|---|---|
| nginx | **not installed** |
| caddy | **not installed** |
| apache | **not installed** |
| Ports 80/443 | **free** (per `ss`) |

## Docker

| Item | Value |
|---|---|
| Docker Engine | 29.1.3 **installed** |
| docker-compose v1 | 1.29.2 **installed** (`docker-compose` command) |
| docker compose v2 plugin | **absent** |
| Docker socket | **requires sudo** for `dkravchenko` |
| containerd | internal ports in use |

## Network (occupied)

- 22 (SSH)
- 10050 (monitoring)
- systemd-resolved
- ntpd
- containerd internal

Ports **80/443 not occupied** — available for nginx after install.

## Resources

| Resource | Status |
|---|---|
| RAM | sufficient |
| Disk | sufficient |

## Deploy recommendation (post-audit)

| Mode | Fit for this server |
|---|---|
| **Docker-first + nginx** | **Primary** — Docker already installed, compose v1 available |
| Static demo | Optional first show |
| systemd bare-metal | Fallback if Docker policy changes |

### Docker port mapping (loopback)

| Service | Host | Container |
|---|---|---|
| Backend | `127.0.0.1:18001` | `8001` |
| Frontend | `127.0.0.1:13000` | `3000` |

### Commands on server

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose build
sudo docker-compose up -d
```

**Not** `docker compose` (plugin missing).

## Still needed from operator

1. `<DOMAIN>` / DNS A-record → `195.209.213.170`
2. SSL strategy (Let's Encrypt after nginx install)
3. Public vs internal-only access
4. FreeModel yes/no — default **no** (`LLM_PROVIDER=mock`)

## References

- Docker runbook: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`
- Docker README: `deploy/docker/README_DOCKER_DEPLOY.md`
- nginx template: `deploy/nginx/ai-landing-docker.conf`
- Release zip: `.runtime/release/ai-landing-full-product.zip`

## Stop-list (unchanged)

- No server deploy executed during this audit adaptation
- No git push
- No FreeModel / AI smoke
- `/opt/ai-portal` untouched
