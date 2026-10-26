#!/usr/bin/env bash
# Backup of everything Lend keeps: accounts, landings, uploads, published pages.
# On the server, from deploy/docker:   sudo bash ./backup.sh [folder]   (default /opt/ai-landing-factory/backups)
# The site keeps working: the database is copied with SQLite's own online backup.
# The archive is checked before it gets its final name; a failed run leaves no archive behind.
set -euo pipefail
umask 077

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "${HERE}/lib.sh"
TARGET="${1:-${DEFAULT_BACKUP_DIR}}"
mkdir -p "${TARGET}"
TARGET="$(absolute_path "${TARGET}")"
cd "${HERE}"
require_compose
HELPER="$(helper_image)"

STAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="lend-data-${STAMP}.tgz"
PARTIAL="${ARCHIVE}.partial"
DB_COPY="${DATA_IN_CONTAINER}/lend-backup.sqlite3"

# One backup at a time: the manual one before an update and the nightly one must not meet.
if command -v flock >/dev/null 2>&1; then
  exec 9>"${TARGET}/.backup.lock"
  flock -n 9 || { echo "Another backup is running (${TARGET}/.backup.lock)." >&2; exit 1; }
fi

cleanup() {
  rm -f "${TARGET}/${PARTIAL}"
  $COMPOSE exec -T backend rm -f "${DB_COPY}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== Consistent copy of the account database =="
$COMPOSE exec -T backend python - <<'PY'
import sqlite3
from app.config import settings

source = sqlite3.connect(f"file:{settings.database_path}?mode=ro", uri=True)
copy = sqlite3.connect(settings.data_dir / "lend-backup.sqlite3")
source.backup(copy)
check = copy.execute("PRAGMA integrity_check").fetchone()[0]
users = copy.execute("SELECT COUNT(*) FROM users").fetchone()[0]
published = copy.execute("SELECT COUNT(*) FROM publications WHERE status = 'published'").fetchone()[0]
copy.close()
source.close()
if check != "ok":
    raise SystemExit(f"Database copy failed the integrity check: {check}")
print(f"accounts: {users}, published landings: {published}")
if users == 0:
    print("WARNING: no accounts in the database. Is this the right server?")
PY

echo "== Archive of the data volume =="
# The live database and its journal stay out: the consistent copy above stands in for them.
docker run --rm --volumes-from "${BACKEND_CONTAINER}:ro" -v "${TARGET}:/backup" "${HELPER}" sh -c "
  set -e
  tar czf '/backup/${PARTIAL}' -C '${DATA_IN_CONTAINER}' \
    --exclude=./lend.sqlite3 --exclude=./lend.sqlite3-wal --exclude=./lend.sqlite3-shm .
  tar tzf '/backup/${PARTIAL}' > /tmp/listing
  grep -qx './lend-backup.sqlite3' /tmp/listing
"
mv "${TARGET}/${PARTIAL}" "${TARGET}/${ARCHIVE}"
echo "Backup ready: ${TARGET}/${ARCHIVE} ($(du -h "${TARGET}/${ARCHIVE}" | cut -f1))"
