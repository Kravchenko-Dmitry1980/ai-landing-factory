"""Accounts, login sessions and invite links in the SQLite database.

Passwords arrive here already hashed: scrypt is slow on purpose and must not run
inside a write transaction.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from uuid import uuid4

from app.core.security import new_token, token_digest
from app.models.domain import utc_now
from app.repositories.database import Database, iso

Role = Literal["viewer", "editor", "admin"]
ROLES: tuple[Role, ...] = ("viewer", "editor", "admin")


class LoginTakenError(Exception):
    pass


class InviteUnusableError(Exception):
    """The invite does not exist, has expired, was used or revoked, or its account was switched off."""


class LastAdminError(Exception):
    """The change would leave nobody who can manage accounts."""


@dataclass(frozen=True)
class User:
    id: str
    login: str
    name: str
    role: Role
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


@dataclass(frozen=True)
class Invite:
    id: str
    role: Role
    note: str
    # Set for a password reset: the account whose password the link replaces.
    user_id: str | None
    user_name: str | None
    created_by_name: str | None
    created_at: datetime
    expires_at: datetime


def _time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        login=row["login"],
        name=row["name"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        last_login_at=_time(row["last_login_at"]),
    )


def _invite(row: sqlite3.Row) -> Invite:
    return Invite(
        id=row["id"],
        role=row["role"],
        note=row["note"],
        user_id=row["user_id"],
        user_name=row["user_name"],
        created_by_name=row["created_by_name"],
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
    )


_INVITE_SELECT = """
    SELECT i.*, target.name AS user_name, author.name AS created_by_name
    FROM invites i
    LEFT JOIN users target ON target.id = i.user_id
    LEFT JOIN users author ON author.id = i.created_by
"""


def _active_admins(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1").fetchone()[0]


class AccountRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    # --- accounts -------------------------------------------------------

    def count_users(self) -> int:
        with self._db.read() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create_user(self, *, login: str, name: str, role: Role, password_hash: str) -> User:
        with self._db.write() as conn:
            return self._insert_user(conn, login=login, name=name, role=role, password_hash=password_hash)

    @staticmethod
    def _insert_user(conn: sqlite3.Connection, *, login: str, name: str, role: Role, password_hash: str) -> User:
        user_id = str(uuid4())
        try:
            conn.execute(
                "INSERT INTO users (id, login, name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, login, name, role, password_hash, iso(utc_now())),
            )
        except sqlite3.IntegrityError as exc:
            if "users.login" in str(exc):
                raise LoginTakenError(login) from exc
            raise
        return _user(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    def get_user(self, user_id: str) -> User | None:
        with self._db.read() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user(row) if row else None

    def find_login(self, login: str) -> tuple[User, str] | None:
        """The account and its password hash, for checking a login attempt."""
        with self._db.read() as conn:
            row = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
        return (_user(row), row["password_hash"]) if row else None

    def list_users(self) -> list[User]:
        with self._db.read() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY is_active DESC, name COLLATE NOCASE").fetchall()
        return [_user(row) for row in rows]

    def update_user(self, user_id: str, *, role: Role | None = None, is_active: bool | None = None) -> User | None:
        with self._db.write() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row is None:
                return None
            current = _user(row)
            new_role = role or current.role
            new_active = current.is_active if is_active is None else is_active
            losing_admin = current.role == "admin" and current.is_active and (new_role != "admin" or not new_active)
            if losing_admin and _active_admins(conn) <= 1:
                raise LastAdminError(user_id)
            conn.execute(
                "UPDATE users SET role = ?, is_active = ? WHERE id = ?",
                (new_role, int(new_active), user_id),
            )
            if not new_active:
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            return _user(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    def set_password(self, user_id: str, password_hash: str) -> bool:
        """Replaces the password and ends every session of the account."""
        with self._db.write() as conn:
            changed = conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
            ).rowcount
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        return changed == 1

    # --- sessions -------------------------------------------------------

    def create_session(self, user_id: str, ttl: timedelta) -> str:
        token = new_token()
        now = utc_now()
        with self._db.write() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (iso(now),))
            conn.execute(
                "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token_digest(token), user_id, iso(now), iso(now + ttl)),
            )
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (iso(now), user_id))
        return token

    def session_user(self, token: str) -> User | None:
        with self._db.read() as conn:
            row = conn.execute(
                """
                SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1
                """,
                (token_digest(token), iso(utc_now())),
            ).fetchone()
        return _user(row) if row else None

    def delete_session(self, token: str) -> None:
        with self._db.write() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_digest(token),))

    # --- invites --------------------------------------------------------

    def create_invite(
        self,
        *,
        role: Role,
        note: str,
        created_by: str | None,
        ttl: timedelta,
        user_id: str | None = None,
    ) -> tuple[Invite, str]:
        token = new_token()
        invite_id = str(uuid4())
        now = utc_now()
        with self._db.write() as conn:
            if user_id is not None:
                # A new reset link replaces the old ones for the same account.
                conn.execute("DELETE FROM invites WHERE user_id = ? AND used_at IS NULL", (user_id,))
            conn.execute(
                """
                INSERT INTO invites (id, token_hash, role, note, user_id, created_by, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (invite_id, token_digest(token), role, note, user_id, created_by, iso(now), iso(now + ttl)),
            )
            row = conn.execute(f"{_INVITE_SELECT} WHERE i.id = ?", (invite_id,)).fetchone()
        return _invite(row), token

    def usable_invite(self, token: str) -> Invite | None:
        with self._db.read() as conn:
            row = self._usable_invite_row(conn, token)
        return _invite(row) if row else None

    @staticmethod
    def _usable_invite_row(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
        return conn.execute(
            f"""{_INVITE_SELECT}
            WHERE i.token_hash = ? AND i.used_at IS NULL AND i.expires_at > ?
              AND (i.user_id IS NULL OR target.is_active = 1)
            """,
            (token_digest(token), iso(utc_now())),
        ).fetchone()

    def list_open_invites(self) -> list[Invite]:
        with self._db.read() as conn:
            rows = conn.execute(
                f"{_INVITE_SELECT} WHERE i.used_at IS NULL AND i.expires_at > ? ORDER BY i.created_at DESC",
                (iso(utc_now()),),
            ).fetchall()
        return [_invite(row) for row in rows]

    def revoke_invite(self, invite_id: str) -> bool:
        with self._db.write() as conn:
            return conn.execute("DELETE FROM invites WHERE id = ? AND used_at IS NULL", (invite_id,)).rowcount == 1

    def accept_invite(self, token: str, *, login: str | None, name: str | None, password_hash: str) -> User:
        """Creates the invited account, or sets the new password for a reset link. Single use."""
        with self._db.write() as conn:
            row = self._usable_invite_row(conn, token)
            if row is None:
                raise InviteUnusableError()
            if row["user_id"] is None:
                if not login or not name:
                    raise ValueError("A new account needs a login and a name")
                user = self._insert_user(conn, login=login, name=name, role=row["role"], password_hash=password_hash)
            else:
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, row["user_id"]))
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["user_id"],))
                user = _user(conn.execute("SELECT * FROM users WHERE id = ?", (row["user_id"],)).fetchone())
            conn.execute("UPDATE invites SET used_at = ? WHERE id = ?", (iso(utc_now()), row["id"]))
        return user
