# Shared by backup.sh, restore.sh and healthcheck.sh (sourced, not run).

# cron starts with PATH=/usr/bin:/bin; docker-compose often lives in /usr/local/bin.
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

# The containers have fixed names (container_name in docker-compose.yml): scripts reach the
# data volume through the backend container, never by a volume name parsed from .env.
BACKEND_CONTAINER=lend-backend
GATEWAY_CONTAINER=lend-gateway
FRONTEND_CONTAINER=lend-frontend
DATA_IN_CONTAINER=/app/backend/data
DEFAULT_BACKUP_DIR=/opt/ai-landing-factory/backups

# docker-compose v1 is what the server has; LEND_COMPOSE="docker compose" for Compose v2.
COMPOSE="${LEND_COMPOSE:-docker-compose}"
require_compose() {
  command -v "${COMPOSE%% *}" >/dev/null 2>&1 && return 0
  echo "Command ${COMPOSE%% *} not found (PATH=${PATH}). Install docker-compose or set LEND_COMPOSE." >&2
  exit 1
}

# The backend's own image runs the helper containers (tar, gzip): nothing extra is pulled
# from the internet at night, and the helper always matches the release.
helper_image() {
  docker inspect -f '{{.Image}}' "${BACKEND_CONTAINER}" 2>/dev/null && return 0
  echo "Container ${BACKEND_CONTAINER} does not exist. Start Lend once first: sudo ${COMPOSE} up -d" >&2
  exit 1
}

# A value from .env read the way docker-compose reads it: the last line wins, spaces around "="
# and "export " are allowed, quotes are dropped.
setting() {
  [[ -f .env ]] || return 0
  sed -n -E "s/^[[:space:]]*(export[[:space:]]+)?$1[[:space:]]*=[[:space:]]*//p" .env \
    | tail -n 1 | sed -E "s/[[:space:]]+\$//; s/^['\"]//; s/['\"]\$//"
}

# Loopback addresses of the backend and frontend for checks from the server itself
# (docker-compose.yml publishes them on 127.0.0.1, the ports can be moved in .env).
backend_local_url() {
  local port
  port="$(setting LEND_BACKEND_LOCAL_PORT)"
  echo "http://127.0.0.1:${port:-18001}"
}
frontend_local_url() {
  local port
  port="$(setting LEND_FRONTEND_LOCAL_PORT)"
  echo "http://127.0.0.1:${port:-13000}"
}

# A path the caller gave, resolved before the script changes directory. Symbolic links are
# followed: a container gets the folder of the real file mounted, not of the link.
absolute_path() {
  local target="$1"
  if readlink -f "$target" 2>/dev/null; then
    return 0
  fi
  if [[ -d "$target" ]]; then
    (cd "$target" && pwd)
  else
    echo "$(cd "$(dirname "$target")" && pwd)/$(basename "$target")"
  fi
}
