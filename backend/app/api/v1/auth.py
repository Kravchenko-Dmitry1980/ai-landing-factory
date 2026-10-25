"""Signing in and out, and accepting invite links. The only API reachable without a session."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.auth import (
    LoginThrottle,
    clear_session_cookie,
    client_address,
    current_user,
    set_session_cookie,
)
from app.core.dependencies import get_account_repository, get_settings
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    hash_password,
    verify_password,
)
from app.repositories.account_repository import InviteUnusableError, LoginTakenError, User
from app.schemas.auth import (
    LOGIN_PATTERN,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    AcceptInviteRequest,
    InvitePublic,
    LoginRequest,
    UserPublic,
    normalize_login,
)

logger = logging.getLogger(__name__)
router = APIRouter()
_throttle = LoginThrottle()

INVITE_UNUSABLE = (
    "Ссылка не работает: её уже использовали, отозвали или срок действия закончился. "
    "Если вы уже создали учётную запись по этой ссылке, просто войдите. Если нет, попросите у администратора новую."
)


def _session_ttl() -> timedelta:
    return timedelta(days=get_settings().session_ttl_days)


def _start_session(user: User, request: Request, response: Response) -> None:
    accounts = get_account_repository()
    previous = request.cookies.get(get_settings().session_cookie_name)
    if previous:
        accounts.delete_session(previous)
    set_session_cookie(response, request, accounts.create_session(user.id, _session_ttl()))


def validate_password(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(422, f"Пароль должен быть не короче {PASSWORD_MIN_LENGTH} символов.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise HTTPException(422, f"Пароль должен быть не длиннее {PASSWORD_MAX_LENGTH} символов.")


def validate_login(login: str) -> None:
    if not LOGIN_PATTERN.match(login):
        raise HTTPException(
            422,
            "Логин — от 3 до 64 символов: латинские буквы, цифры, точка, дефис, подчёркивание или @.",
        )


def validate_name(name: str) -> None:
    if not NAME_MIN_LENGTH <= len(name) <= NAME_MAX_LENGTH:
        raise HTTPException(422, f"Укажите имя и фамилию: от {NAME_MIN_LENGTH} до {NAME_MAX_LENGTH} символов.")


@router.post("/login", response_model=UserPublic)
def login(body: LoginRequest, request: Request, response: Response) -> UserPublic:
    login_name = normalize_login(body.login)
    address = client_address(request)
    if not _throttle.try_begin(login_name, address):
        logger.warning("Login throttled: %s from %s", login_name, address)
        raise HTTPException(429, "Слишком много неудачных попыток входа. Подождите 15 минут и попробуйте снова.")
    found = get_account_repository().find_login(login_name)
    # Check a password even for an unknown login, so the answer time does not reveal which logins exist.
    password_ok = verify_password(body.password, found[1] if found else DUMMY_PASSWORD_HASH)
    if not found or not password_ok:
        logger.info("Failed login: %s from %s (%s)", login_name, address, "wrong password" if found else "unknown login")
        raise HTTPException(401, "Неверный логин или пароль.")
    user = found[0]
    if not user.is_active:
        raise HTTPException(403, "Учётная запись отключена. Обратитесь к администратору.")
    _throttle.succeeded(login_name, address)
    _start_session(user, request, response)
    return UserPublic.of(user)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        get_account_repository().delete_session(token)
    clear_session_cookie(response, request)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)) -> UserPublic:
    return UserPublic.of(user)


@router.get("/invites/{token}", response_model=InvitePublic)
def invite_info(token: str) -> InvitePublic:
    invite = get_account_repository().usable_invite(token)
    if invite is None:
        raise HTTPException(404, INVITE_UNUSABLE)
    return InvitePublic.of(invite)


@router.post("/invites/{token}/accept", response_model=UserPublic)
def accept_invite(token: str, body: AcceptInviteRequest, request: Request, response: Response) -> UserPublic:
    accounts = get_account_repository()
    invite = accounts.usable_invite(token)
    if invite is None:
        raise HTTPException(404, INVITE_UNUSABLE)
    login_name = name = None
    if invite.user_id is None:
        login_name = normalize_login(body.login or "")
        name = " ".join((body.name or "").split())
        validate_name(name)
        validate_login(login_name)
    validate_password(body.password)
    try:
        user = accounts.accept_invite(token, login=login_name, name=name, password_hash=hash_password(body.password))
    except LoginTakenError:
        raise HTTPException(409, "Такой логин уже занят. Придумайте другой.") from None
    except InviteUnusableError:
        raise HTTPException(404, INVITE_UNUSABLE) from None
    _start_session(user, request, response)
    return UserPublic.of(user)
