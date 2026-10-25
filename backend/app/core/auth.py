"""Who is calling: the session cookie, roles, and the same-origin check for changes."""

import logging
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, Response

from app.core.dependencies import get_account_repository, get_settings
from app.repositories.account_repository import Role, User

logger = logging.getLogger(__name__)

ROLE_RANK: dict[Role, int] = {"viewer": 0, "editor": 1, "admin": 2}
_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def current_user(request: Request) -> User:
    """Any signed-in, active account. A sync dependency: FastAPI runs the SQLite lookup in a thread."""
    token = request.cookies.get(get_settings().session_cookie_name)
    user = get_account_repository().session_user(token) if token else None
    if user is None:
        raise HTTPException(401, "Войдите в учётную запись.")
    return user


def require_role(minimum: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if ROLE_RANK[user.role] < ROLE_RANK[minimum]:
            raise HTTPException(403, "У вашей учётной записи нет прав на это действие.")
        return user

    dependency.__name__ = f"require_{minimum}"
    return dependency


require_editor = require_role("editor")
require_admin = require_role("admin")


def check_same_origin(request: Request) -> None:
    """
    Refuses changes sent from pages of other sites (CSRF), on top of the SameSite=Lax cookie.

    Browsers send Origin with every cross-origin POST/PATCH/DELETE. Requests without it
    (the Next.js server, scripts) pass: the session cookie still decides who they are.
    """
    if request.method not in _UNSAFE_METHODS:
        return
    origin = request.headers.get("origin")
    if not origin or origin in get_settings().cors_origins:
        return
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    # Host names only: nginx passes Host without the port, and cookies are shared across ports anyway.
    if urlsplit(origin).hostname and urlsplit(origin).hostname == urlsplit(f"//{host}").hostname:
        return
    logger.warning("Refused %s %s: Origin %s, Host %s", request.method, request.url.path, origin, host)
    raise HTTPException(403, "Запрос пришёл с другого сайта и отклонён.")


def _cookie_secure(request: Request) -> bool:
    mode = get_settings().session_cookie_secure.strip().lower()
    if mode in ("1", "true", "yes"):
        return True
    if mode in ("0", "false", "no"):
        return False
    forwarded = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    return request.url.scheme == "https" or forwarded == "https"


def set_session_cookie(response: Response, request: Request, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
        path="/",
    )


def clear_session_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        get_settings().session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
        path="/",
    )


def client_address(request: Request) -> str:
    # nginx and the Next.js dev proxy put the visitor's address here; the backend itself listens on loopback.
    forwarded = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "")


class LoginThrottle:
    """
    Failed logins within a sliding window, per account-and-address pair and per address.

    Counting per pair means a stranger guessing at "admin" cannot lock the real administrator
    out from another computer; the per-address limit is high enough for a whole office behind
    one NAT. In memory and per process: enough to stop password guessing against one server.
    """

    def __init__(self, window_seconds: float = 15 * 60, per_pair: int = 10, per_address: int = 100) -> None:
        self._window = window_seconds
        self._per_pair = per_pair
        self._per_address = per_address
        self._failures: defaultdict[tuple[str, ...], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _recent(self, key: tuple[str, ...], now: float) -> deque[float]:
        times = self._failures[key]
        while times and now - times[0] > self._window:
            times.popleft()
        return times

    def try_begin(self, login: str, address: str) -> bool:
        """
        False when the limit is reached. Otherwise counts this attempt as failed up front,
        so parallel attempts cannot all slip past the check while scrypt runs.
        """
        now = time.monotonic()
        with self._lock:
            if len(self._failures) > 10_000:
                # Guessing with many made-up logins must not grow memory without bound.
                for key in [k for k in self._failures if not self._recent(k, now)]:
                    del self._failures[key]
            pair = self._recent(("pair", login, address), now)
            per_address = self._recent(("address", address), now)
            if len(pair) >= self._per_pair or len(per_address) >= self._per_address:
                return False
            pair.append(now)
            per_address.append(now)
            return True

    def succeeded(self, login: str, address: str) -> None:
        with self._lock:
            self._failures.pop(("pair", login, address), None)
