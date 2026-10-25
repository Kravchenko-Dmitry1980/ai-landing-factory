"""Accounts and invite links, for administrators only (the router is mounted behind require_admin)."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_admin
from app.core.dependencies import get_account_repository, get_settings
from app.repositories.account_repository import Invite, LastAdminError, User
from app.schemas.auth import InviteCreated, InviteCreateRequest, InvitePublic, UserPublic, UserUpdateRequest

router = APIRouter()


def _created(invite: Invite, token: str) -> InviteCreated:
    return InviteCreated(invite=InvitePublic.of(invite), path=f"/invite/{token}")


def _invite_ttl() -> timedelta:
    return timedelta(days=get_settings().invite_ttl_days)


@router.get("/users", response_model=list[UserPublic])
def list_users() -> list[UserPublic]:
    return [UserPublic.of(user) for user in get_account_repository().list_users()]


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: str, body: UserUpdateRequest, admin: User = Depends(require_admin)) -> UserPublic:
    if user_id == admin.id:
        raise HTTPException(409, "Свою учётную запись изменить нельзя: попросите другого администратора.")
    try:
        user = get_account_repository().update_user(user_id, role=body.role, is_active=body.is_active)
    except LastAdminError:
        raise HTTPException(409, "Так в системе не останется ни одного администратора.") from None
    if user is None:
        raise HTTPException(404, "Такой учётной записи нет.")
    return UserPublic.of(user)


@router.post("/users/{user_id}/reset-link", response_model=InviteCreated, status_code=201)
def password_reset_link(user_id: str, admin: User = Depends(require_admin)) -> InviteCreated:
    accounts = get_account_repository()
    user = accounts.get_user(user_id)
    if user is None:
        raise HTTPException(404, "Такой учётной записи нет.")
    if not user.is_active:
        raise HTTPException(409, "Учётная запись отключена. Сначала включите её.")
    invite, token = accounts.create_invite(
        role=user.role, note="", created_by=admin.id, ttl=_invite_ttl(), user_id=user.id
    )
    return _created(invite, token)


@router.get("/invites", response_model=list[InvitePublic])
def list_invites() -> list[InvitePublic]:
    return [InvitePublic.of(invite) for invite in get_account_repository().list_open_invites()]


@router.post("/invites", response_model=InviteCreated, status_code=201)
def create_invite(body: InviteCreateRequest, admin: User = Depends(require_admin)) -> InviteCreated:
    invite, token = get_account_repository().create_invite(
        role=body.role, note=body.note.strip(), created_by=admin.id, ttl=_invite_ttl()
    )
    return _created(invite, token)


@router.delete("/invites/{invite_id}", status_code=204)
def revoke_invite(invite_id: str) -> None:
    if not get_account_repository().revoke_invite(invite_id):
        raise HTTPException(404, "Такого приглашения нет: его уже использовали или отозвали.")
