#!/usr/bin/env bash
# Deploy a full-product release archive on Ubuntu (systemd + nginx).
# TEMPLATE — placeholders only. Does NOT run against a real server from Windows.
#
# Usage (on server):
#   sudo ./deploy_release.sh /path/to/ai-landing-full-product.zip <RELEASE_ID>
set -euo pipefail

ARCHIVE="${1:-}"
RELEASE_ID="${2:-$(date +%Y%m%d_%H%M%S)}"
DEPLOY_ROOT="${DEPLOY_PATH:-/opt/ai-landing-factory}"
RELEASE_DIR="${DEPLOY_ROOT}/releases/${RELEASE_ID}"
SHARED_DIR="${DEPLOY_ROOT}/shared"
CURRENT_LINK="${DEPLOY_ROOT}/current"

if [[ -z "${ARCHIVE}" || ! -f "${ARCHIVE}" ]]; then
  echo "Usage: $0 /path/to/ai-landing-full-product.zip [RELEASE_ID]"
  exit 1
fi

echo "== layout =="
sudo mkdir -p "${DEPLOY_ROOT}/releases" "${SHARED_DIR}" /var/log/ai-landing-factory
sudo mkdir -p "${RELEASE_DIR}"

echo "== unpack =="
sudo unzip -q -o "${ARCHIVE}" -d "${RELEASE_DIR}"

# If archive contains a single top-level folder, flatten
TOP_COUNT=$(find "${RELEASE_DIR}" -mindepth 1 -maxdepth 1 | wc -l)
if [[ "${TOP_COUNT}" -eq 1 ]]; then
  ONLY=$(find "${RELEASE_DIR}" -mindepth 1 -maxdepth 1)
  if [[ -d "${ONLY}" ]]; then
    sudo sh -c "shopt -s dotglob && mv \"${ONLY}\"/* \"${RELEASE_DIR}/\" && rmdir \"${ONLY}\""
  fi
fi

echo "== env files (create once) =="
if [[ ! -f "${SHARED_DIR}/backend.env" ]]; then
  sudo install -m 600 /dev/null "${SHARED_DIR}/backend.env"
  echo "Fill ${SHARED_DIR}/backend.env from backend/.env.production.example"
fi
if [[ ! -f "${SHARED_DIR}/frontend.env" ]]; then
  sudo install -m 600 /dev/null "${SHARED_DIR}/frontend.env"
  echo "Fill ${SHARED_DIR}/frontend.env (optional; NEXT_PUBLIC_* baked at build)"
fi

echo "== python venv =="
cd "${RELEASE_DIR}"
sudo python3 -m venv .venv
sudo ./.venv/bin/pip install --upgrade pip
sudo ./.venv/bin/pip install -r backend/requirements.txt

echo "== frontend build =="
cd "${RELEASE_DIR}/frontend"
if [[ -f "${SHARED_DIR}/frontend.env" ]]; then
  # shellcheck disable=SC1090
  set -a; source "${SHARED_DIR}/frontend.env"; set +a
fi
sudo -E npm ci
sudo -E npm run build

echo "== switch current symlink =="
sudo ln -sfn "${RELEASE_DIR}" "${CURRENT_LINK}"

echo "== systemd units =="
sudo cp "${RELEASE_DIR}/deploy/systemd/alf-backend.service" /etc/systemd/system/
sudo cp "${RELEASE_DIR}/deploy/systemd/alf-frontend.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alf-backend alf-frontend
sudo systemctl restart alf-backend alf-frontend

echo "== nginx =="
sudo cp "${RELEASE_DIR}/deploy/nginx/ai-landing-full.conf" /etc/nginx/sites-available/ai-landing-full.conf
# Ensure map for WebSocket Connection header exists once
if [[ ! -f /etc/nginx/conf.d/map-connection.conf ]]; then
  sudo tee /etc/nginx/conf.d/map-connection.conf >/dev/null <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
EOF
fi
sudo ln -sfn /etc/nginx/sites-available/ai-landing-full.conf /etc/nginx/sites-enabled/ai-landing-full.conf
sudo nginx -t
sudo systemctl reload nginx

echo "Deploy done: ${CURRENT_LINK} -> ${RELEASE_DIR}"
echo "Run: ${DEPLOY_ROOT}/current/deploy/ubuntu/healthcheck.sh"
