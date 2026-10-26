#!/usr/bin/env bash
# Local healthcheck for full product on the server (loopback).
set -euo pipefail

echo "== backend /health =="
curl -fsS http://127.0.0.1:8001/health
echo

echo "== frontend loopback =="
curl -fsS -o /dev/null -w "frontend HTTP %{http_code}\n" http://127.0.0.1:3000/

echo "== nginx (if domain configured) =="
if [[ -n "${DOMAIN:-}" ]]; then
  curl -fsS -o /dev/null -w "nginx /health HTTP %{http_code}\n" "http://${DOMAIN}/health" || true
  curl -fsS -o /dev/null -w "nginx / HTTP %{http_code}\n" "http://${DOMAIN}/" || true
else
  echo "Set DOMAIN=<your-domain> to probe via nginx"
fi

echo "== systemd =="
systemctl is-active alf-backend
systemctl is-active alf-frontend

echo "Healthcheck OK"
