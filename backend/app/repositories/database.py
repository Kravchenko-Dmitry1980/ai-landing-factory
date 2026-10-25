"""SQLite file with accounts, sessions, invites and publications (stdlib sqlite3, no server).

Landing contracts stay in JSON files next to it; this database holds what needs
uniqueness, lookups and transactions.
"""

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Each entry moves the schema one version up; PRAGMA user_version records how far a file got.
# Never edit an entry that has shipped: add a new one.
_MIGRATIONS: list[tuple[str, ...]] = [
    (
        """
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            login TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('viewer', 'editor', 'admin')),
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        )
        """,
        """
        CREATE TABLE sessions (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX sessions_user ON sessions (user_id)",
        # An invite creates an account. With user_id set it resets that account's password instead.
        """
        CREATE TABLE invites (
            id TEXT PRIMARY KEY,
            token_hash TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL CHECK (role IN ('viewer', 'editor', 'admin')),
            note TEXT NOT NULL DEFAULT '',
            user_id TEXT REFERENCES users (id) ON DELETE CASCADE,
            created_by TEXT REFERENCES users (id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        )
        """,
        # One row per published project. The HTML of each version lives in data/published.
        """
        CREATE TABLE publications (
            project_id TEXT PRIMARY KEY,
            slug TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL CHECK (status IN ('published', 'withdrawn')),
            version INTEGER NOT NULL,
            contract_version INTEGER NOT NULL,
            theme TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            customer TEXT NOT NULL DEFAULT '',
            lead TEXT NOT NULL DEFAULT '',
            people TEXT NOT NULL DEFAULT '[]',
            body_text TEXT NOT NULL DEFAULT '',
            first_published_at TEXT NOT NULL,
            published_at TEXT NOT NULL,
            published_by TEXT REFERENCES users (id) ON DELETE SET NULL,
            withdrawn_at TEXT
        )
        """,
        "CREATE INDEX publications_status ON publications (status, published_at)",
    ),
]


def _rollback(conn: sqlite3.Connection) -> None:
    """Undo the open transaction without hiding the error that caused it.

    SQLite rolls back by itself after some failures (disk full, I/O errors); a second
    ROLLBACK would then raise and replace the original exception.
    """
    if not conn.in_transaction:
        return
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        logger.exception("ROLLBACK failed after an earlier error in %s", conn)


def iso(moment: datetime) -> str:
    """One fixed format for stored times, so they also compare correctly as text."""
    return moment.isoformat(timespec="microseconds")


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # isolation_level=None: no implicit transactions; write() opens them explicitly.
        conn = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        """A transaction that takes the write lock up front, so checks inside it stay true."""
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                _rollback(conn)
                raise
            conn.execute("COMMIT")
        finally:
            conn.close()

    def migrate(self) -> int:
        """
        Brings the file to the latest schema; returns the version it ended at.

        Each step re-reads the version under the write lock, so two processes starting
        at once do not apply the same step twice.
        """
        conn = self.connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            current = conn.execute("PRAGMA user_version").fetchone()[0]
            if current > len(_MIGRATIONS):
                raise RuntimeError(
                    f"{self.path} has schema version {current}, newer than this code "
                    f"({len(_MIGRATIONS)}). Update the application."
                )
            for target, statements in enumerate(_MIGRATIONS, start=1):
                conn.execute("BEGIN IMMEDIATE")
                try:
                    if conn.execute("PRAGMA user_version").fetchone()[0] < target:
                        for statement in statements:
                            conn.execute(statement)
                        conn.execute(f"PRAGMA user_version = {target}")
                except BaseException:
                    _rollback(conn)
                    raise
                conn.execute("COMMIT")
            return len(_MIGRATIONS)
        finally:
            conn.close()
