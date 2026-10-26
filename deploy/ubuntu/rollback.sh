#!/usr/bin/env bash
# Rollback to a previous release (symlink switch).
# Usage: sudo ./rollback.sh <PREV_RELEASE_ID>
set -euo pipefail

PREV_ID="${1:-}"
DEPLOY_ROOT="${DEPLOY_PATH:-/opt/ai-landing-factory}"
PREV_DIR="${DEPLOY_ROOT}/releases/${PREV_ID}"
CURRENT_LINK="${DEPLOY_ROOT}/current"

if [[ -z "${PREV_ID}" || ! -d "${PREV_DIR}" ]]; then
  echo "Usage: $0 <PREV_RELEASE_ID>"
  echo "Available:"
  ls -1 "${DEPLOY_ROOT}/releases" || true
  exit 1
fi

echo "Stopping services..."
sudo systemctl stop alf-frontend alf-backend || true

echo "Switching current -> ${PREV_DIR}"
sudo ln -sfn "${PREV_DIR}" "${CURRENT_LINK}"

echo "Starting services..."
sudo systemctl start alf-backend alf-frontend

sleep 2
curl -fsS http://127.0.0.1:8001/health || {
  echo "Healthcheck FAILED after rollback"
  exit 1
}

echo "Rollback OK: $(readlink -f "${CURRENT_LINK}")"
