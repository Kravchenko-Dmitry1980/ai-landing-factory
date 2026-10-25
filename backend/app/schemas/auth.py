from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.repositories.account_repository import Invite, Role, User

LOGIN_PATTERN = re.compile(r"^[a-z0-9._@-]{3,64}$")
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 100


def normalize_login(value: str) -> str:
    return value.strip().lower()


class UserPublic(BaseModel):
    id: str
    login: str
    name: str
    role: Role
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    @classmethod
    def of(cls, user: User) -> UserPublic:
        return cls(
            id=user.id,
            login=user.login,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )


class LoginRequest(BaseModel):
    login: str = Field(max_length=200)
    password: str = Field(max_length=1000)


class InvitePublic(BaseModel):
    id: str
    # account: creates a new account; reset: sets a new password for an existing one.
    kind: Literal["account", "reset"]
    role: Role
    note: str
    user_name: str | None = None
    created_by_name: str | None = None
    created_at: datetime
    expires_at: datetime

    @classmethod
    def of(cls, invite: Invite) -> InvitePublic:
        return cls(
            id=invite.id,
            kind="reset" if invite.user_id else "account",
            role=invite.role,
            note=invite.note,
            user_name=invite.user_name,
            created_by_name=invite.created_by_name,
            created_at=invite.created_at,
            expires_at=invite.expires_at,
        )


class InviteCreated(BaseModel):
    invite: InvitePublic
    # The link is shown once: only its digest is stored.
    path: str


class InviteCreateRequest(BaseModel):
    role: Role = "editor"
    note: str = Field(default="", max_length=200)


class AcceptInviteRequest(BaseModel):
    login: str | None = Field(default=None, max_length=200)
    name: str | None = Field(default=None, max_length=200)
    password: str = Field(max_length=1000)


class UserUpdateRequest(BaseModel):
    role: Role | None = None
    is_active: bool | None = None
