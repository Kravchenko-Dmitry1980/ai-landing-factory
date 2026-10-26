#!/usr/bin/env bash
# Is Lend up? The containers, the database, and the whole path a visitor takes through the gateway.
# On the server, from deploy/docker:   sudo bash ./healthcheck.sh
# FAIL lines mean something is broken (exit code 1); WARN lines need attention but the site works.
set -uo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
source ./lib.sh

GATEWAY="$(setting LEND_GATEWAY)"; GATEWAY="${GATEWAY:-http}"
HTTP_PORT="$(setting LEND_HTTP_PORT)"; HTTP_PORT="${HTTP_PORT:-80}"
HTTPS_PORT="$(setting LEND_HTTPS_PORT)"; HTTPS_PORT="${HTTPS_PORT:-443}"
CERTS_DIR="$(setting LEND_CERTS_DIR)"; CERTS_DIR="${CERTS_DIR:-./certs}"
BIND="$(setting LEND_BIND)"
HOST=127.0.0.1
[[ -n "${BIND}" && "${BIND}" != "0.0.0.0" ]] && HOST="${BIND}"
BACKUP_DIR="${LEND_BACKUP_DIR:-${DEFAULT_BACKUP_DIR}}"

failed=0
warned=0
ok() { echo "OK    $*"; }
fail() { echo "FAIL  $*"; failed=1; }
warn() { echo "WARN  $*"; warned=1; }

# check <label> <expected status, e.g. 200 or 301|308> <url> [curl options]
check() {
  local label="$1" expected="$2" url="$3"
  shift 3
  local code error errors
  errors="$(mktemp)"
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "$@" "$url" 2>"$errors")"
  error="$(tr -d '\r' <"$errors" | head -n 1)"
  rm -f "$errors"
  if [[ "$code" =~ ^(${expected})$ ]]; then
    ok "$label ($code)"
  elif [[ "$code" == "000" ]]; then
    fail "$label: no answer from $url (${error:-connection failed})"
  else
    fail "$label: expected $expected, got $code ($url)"
  fi
}

echo "== Containers =="
for name in "${GATEWAY_CONTAINER}" "${BACKEND_CONTAINER}" "${FRONTEND_CONTAINER}"; do
  state="$(docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}} restarts={{.RestartCount}}' "$name" 2>/dev/null)"
  case "$state" in
    "") fail "$name does not exist (sudo ${COMPOSE} up -d)" ;;
    "running healthy "* | "running  "*) ok "$name: $state" ;;
    "running starting "*) fail "$name is still starting: try again in a minute" ;;
    *) fail "$name: $state" ;;
  esac
done

echo "== Database and data folder =="
check "backend ready (database opens, data folder is writable)" 200 "$(backend_local_url)/health/ready"
check "frontend answers" 200 "$(frontend_local_url)/login"

if [[ "$GATEWAY" == "https" ]]; then
  BASE="https://${HOST}:${HTTPS_PORT}"
  echo "== Through the gateway (HTTPS, ${BASE}) =="
  check "plain HTTP health" 200 "http://${HOST}:${HTTP_PORT}/health"
  check "plain HTTP goes to HTTPS" 301 "http://${HOST}:${HTTP_PORT}/login"
  # The certificate names the server, not 127.0.0.1: only the routes are checked here.
  INSECURE=(-k)
else
  BASE="http://${HOST}:${HTTP_PORT}"
  echo "== Through the gateway (${GATEWAY}, ${BASE}) =="
  INSECURE=()
fi
check "backend health" 200 "${BASE}/health" "${INSECURE[@]}"
check "sign-in page" 200 "${BASE}/login" "${INSECURE[@]}"
check "pages need a session (redirect to sign-in)" 307 "${BASE}/" "${INSECURE[@]}"
check "API needs a session" 401 "${BASE}/api/v1/auth/me" "${INSECURE[@]}"

if [[ "$GATEWAY" == "proxy" ]]; then
  # The shared proxy is asked on this server for Lend's name, as a visitor would ask it:
  # its route to the gateway and its certificate for the name (checked, no -k).
  DOMAIN="$(setting LEND_DOMAIN)"
  PROXY_HTTP_PORT="$(setting LEND_PROXY_HTTP_PORT)"; PROXY_HTTP_PORT="${PROXY_HTTP_PORT:-80}"
  PROXY_HTTPS_PORT="$(setting LEND_PROXY_HTTPS_PORT)"; PROXY_HTTPS_PORT="${PROXY_HTTPS_PORT:-443}"
  if [[ -z "$DOMAIN" ]]; then
    warn "LEND_DOMAIN is empty: the route through the server's shared proxy is not checked"
  else
    PUBLIC="https://${DOMAIN}:${PROXY_HTTPS_PORT}"
    echo "== Through the shared proxy (${PUBLIC}, asked on this server) =="
    TO_LOCAL=(--resolve "${DOMAIN}:${PROXY_HTTPS_PORT}:127.0.0.1")
    check "backend health" 200 "${PUBLIC}/health" "${TO_LOCAL[@]}"
    check "sign-in page" 200 "${PUBLIC}/login" "${TO_LOCAL[@]}"
    check "plain HTTP goes to HTTPS" "301|302|307|308" "http://${DOMAIN}:${PROXY_HTTP_PORT}/login" \
      --resolve "${DOMAIN}:${PROXY_HTTP_PORT}:127.0.0.1"
  fi
fi

if [[ "$GATEWAY" == "https" ]]; then
  echo "== Certificate =="
  cert="${CERTS_DIR}/fullchain.pem"
  if [[ ! -f "$cert" ]]; then
    fail "no certificate at $cert"
  elif ! command -v openssl >/dev/null 2>&1; then
    warn "openssl is not installed: the certificate expiry is not checked"
  elif ! openssl x509 -checkend 0 -noout -in "$cert" >/dev/null; then
    fail "the certificate has expired: $(openssl x509 -enddate -noout -in "$cert")"
  elif ! openssl x509 -checkend $((21 * 86400)) -noout -in "$cert" >/dev/null; then
    warn "the certificate expires within 3 weeks: $(openssl x509 -enddate -noout -in "$cert")"
  else
    ok "certificate valid, $(openssl x509 -enddate -noout -in "$cert")"
  fi
fi

echo "== Backups (${BACKUP_DIR}) =="
latest="$(ls -1t "${BACKUP_DIR}"/lend-data-*.tgz 2>/dev/null | grep -v -- '-before-restore' | head -n 1)"
if [[ -z "$latest" ]]; then
  warn "no backups yet: sudo bash ./backup.sh (and the nightly cron job from the deploy guide)"
elif [[ -z "$(find "$latest" -mmin -$((36 * 60)))" ]]; then
  warn "the latest backup is older than 36 hours: $latest. Is the cron job running?"
else
  ok "latest backup $(basename "$latest")"
fi

echo
if [[ "$failed" -ne 0 ]]; then
  echo "Something is wrong. Logs: sudo ${COMPOSE} logs --tail=100 gateway backend frontend"
  exit 1
fi
[[ "$warned" -ne 0 ]] && echo "Lend is up, see the warnings above." || echo "Lend is up."
