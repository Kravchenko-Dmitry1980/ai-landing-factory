#!/usr/bin/env bash
# Restores a backup made by backup.sh: everything in the data volume is REPLACED by the archive.
# On the server, from deploy/docker:
#   sudo bash ./restore.sh /opt/ai-landing-factory/backups/lend-data-YYYYMMDD_HHMMSS.tgz
# Before anything is erased: the archive is read through, Lend is stopped and the current data
# is saved as it is (a "before-restore" archive next to the given one, restorable the same way).
# The archive is unpacked next to the old data first; the old data goes only after that worked.
set -euo pipefail
umask 077

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "${HERE}/lib.sh"
if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: sudo bash ./restore.sh <lend-data-....tgz>" >&2
  exit 1
fi
ARCHIVE="$(absolute_path "$1")"
cd "${HERE}"
require_compose
HELPER="$(helper_image)"

ARCHIVE_DIR="$(dirname "${ARCHIVE}")"
ARCHIVE_NAME="$(basename "${ARCHIVE}")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SAFETY_NAME="lend-data-${STAMP}-before-restore.tgz"
STAGING="${DATA_IN_CONTAINER}/.restore-staging"

echo "== Checking ${ARCHIVE_NAME} =="
listing="$(tar tzf "${ARCHIVE}")" || { echo "The archive cannot be read: it is damaged or not a .tgz." >&2; exit 1; }
if grep -qx './lend-backup.sqlite3' <<<"${listing}"; then
  database="./lend-backup.sqlite3"   # made by backup.sh while the site was running
elif grep -qx './lend.sqlite3' <<<"${listing}"; then
  database="./lend.sqlite3"          # a before-restore copy, made while the site was stopped
else
  echo "No account database in the archive: this is not a Lend backup." >&2
  exit 1
fi
echo "OK: $(grep -c . <<<"${listing}") entries, database ${database}"

echo
echo "All accounts, landings and publications on this server will be replaced by ${ARCHIVE_NAME}."
echo "Lend stops for a minute; the current data is saved first to ${ARCHIVE_DIR}/${SAFETY_NAME}."
answer=""
read -r -p "Type RESTORE to continue: " answer || true
[[ "${answer}" == "RESTORE" ]] || { echo "Cancelled, nothing changed."; exit 1; }

stopped=0
on_error() {
  echo >&2
  echo "RESTORE DID NOT FINISH (see the error above)." >&2
  if [[ "${stopped}" -eq 1 ]]; then
    echo "Lend is stopped. The data from before the restore is in ${ARCHIVE_DIR}/${SAFETY_NAME}" >&2
    echo "(if that file exists, the old data is safe). Next steps:" >&2
    echo "  put the old data back:  sudo bash ./restore.sh ${ARCHIVE_DIR}/${SAFETY_NAME}" >&2
    echo "  or just start again:    sudo ${COMPOSE} start" >&2
  fi
}
trap on_error ERR

$COMPOSE stop gateway frontend backend
stopped=1

echo "== Saving the current data =="
docker run --rm --volumes-from "${BACKEND_CONTAINER}:ro" -v "${ARCHIVE_DIR}:/backup" "${HELPER}" sh -c "
  set -e
  tar czf '/backup/${SAFETY_NAME}.partial' -C '${DATA_IN_CONTAINER}' --exclude=./.restore-staging .
  tar tzf '/backup/${SAFETY_NAME}.partial' > /dev/null
  mv '/backup/${SAFETY_NAME}.partial' '/backup/${SAFETY_NAME}'
"
echo "Saved: ${ARCHIVE_DIR}/${SAFETY_NAME}"

echo "== Restoring =="
docker run --rm --volumes-from "${BACKEND_CONTAINER}" -v "${ARCHIVE_DIR}:/backup:ro" "${HELPER}" sh -c "
  set -e
  rm -rf '${STAGING}'
  mkdir '${STAGING}'
  tar xzf '/backup/${ARCHIVE_NAME}' -C '${STAGING}'
  find '${DATA_IN_CONTAINER}' -mindepth 1 -maxdepth 1 ! -name .restore-staging -exec rm -rf {} +
  find '${STAGING}' -mindepth 1 -maxdepth 1 -exec mv {} '${DATA_IN_CONTAINER}/' \;
  rmdir '${STAGING}'
  if [ '${database}' = './lend-backup.sqlite3' ]; then
    mv '${DATA_IN_CONTAINER}/lend-backup.sqlite3' '${DATA_IN_CONTAINER}/lend.sqlite3'
  fi
"

# start, not up: the same containers come back, nothing is recreated (docker-compose v1 on
# Docker 29 fails to recreate containers, see the deploy guide).
$COMPOSE start
trap - ERR
echo
echo "Restored from ${ARCHIVE_NAME}. Waiting for Lend to start..."
READY_URL="$(backend_local_url)/health/ready"
for _ in $(seq 1 30); do
  if curl -fsS --max-time 3 "${READY_URL}" >/dev/null 2>&1; then
    echo "Lend is running. Full check: sudo bash ./healthcheck.sh"
    exit 0
  fi
  sleep 3
done
echo "Lend has not answered for 90 seconds. Check: sudo bash ./healthcheck.sh and sudo ${COMPOSE} logs --tail=100 backend" >&2
exit 1
