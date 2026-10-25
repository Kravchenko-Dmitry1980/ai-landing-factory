"""Account commands for whoever runs the server. Run from backend/: python -m app.cli <command>.

  create-admin --login L --name "Имя Фамилия"   the first administrator (asks for the password)
  invite [--role editor] [--note "..."]           an invite link, when no administrator can sign in
  dev-seed                                        local test accounts, written to data/dev-accounts.txt
"""

import argparse
import getpass
import secrets
import sys
from datetime import timedelta

from app.api.v1.auth import validate_login, validate_name, validate_password
from app.core.dependencies import get_account_repository, get_settings
from app.core.security import hash_password
from app.repositories.account_repository import ROLES, LoginTakenError
from app.schemas.auth import normalize_login

DEV_ACCOUNTS = (("admin", "Администратор (тест)", "admin"), ("hr", "Сотрудник HR (тест)", "editor"), ("reader", "Читатель (тест)", "viewer"))


def _check(validator, value: str) -> None:
    from fastapi import HTTPException

    try:
        validator(value)
    except HTTPException as exc:
        raise SystemExit(exc.detail) from None


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    first = getpass.getpass("Пароль: ")
    if getpass.getpass("Пароль ещё раз: ") != first:
        raise SystemExit("Пароли не совпали.")
    return first


def create_admin(args: argparse.Namespace) -> None:
    login = normalize_login(args.login)
    name = " ".join(args.name.split())
    _check(validate_login, login)
    _check(validate_name, name)
    password = _read_password(args.password_stdin)
    _check(validate_password, password)
    try:
        get_account_repository().create_user(login=login, name=name, role="admin", password_hash=hash_password(password))
    except LoginTakenError:
        raise SystemExit(f"Логин {login} уже занят.") from None
    print(f"Администратор {login} создан. Войдите на сайте: /login")


def invite(args: argparse.Namespace) -> None:
    created, token = get_account_repository().create_invite(
        role=args.role,
        note=args.note,
        created_by=None,
        ttl=timedelta(days=get_settings().invite_ttl_days),
    )
    print(f"Приглашение ({created.role}) до {created.expires_at:%d.%m.%Y}: /invite/{token}")
    print("Добавьте к адресу сайта, например https://lend.example.ru/invite/...")


def dev_seed(_args: argparse.Namespace) -> None:
    """Test accounts for a developer machine; the passwords go to a git-ignored file, never to the screen."""
    accounts = get_account_repository()
    target = get_settings().data_dir / "dev-accounts.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    created = 0
    for login, name, role in DEV_ACCOUNTS:
        if accounts.find_login(login):
            continue
        password = secrets.token_urlsafe(12)
        # The password is written down first: a failed write leaves no account nobody can open.
        with target.open("a", encoding="utf-8") as f:
            f.write(f"{login}\t{role}\t{password}\n")
        accounts.create_user(login=login, name=name, role=role, password_hash=hash_password(password))
        created += 1
    if created:
        print(f"Созданы тестовые учётные записи: {created}. Логины и пароли: {target}")
    elif target.exists():
        print(f"Тестовые учётные записи уже есть. Логины и пароли: {target}")
    else:
        print(f"Тестовые учётные записи уже есть, но файла с паролями {target} нет.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Учётные записи Ленда")
    commands = parser.add_subparsers(dest="command", required=True)

    admin = commands.add_parser("create-admin", help="создать администратора")
    admin.add_argument("--login", required=True)
    admin.add_argument("--name", required=True)
    admin.add_argument("--password-stdin", action="store_true", help="прочитать пароль из первой строки stdin")
    admin.set_defaults(handler=create_admin)

    link = commands.add_parser("invite", help="выпустить ссылку-приглашение")
    link.add_argument("--role", choices=ROLES, default="editor")
    link.add_argument("--note", default="")
    link.set_defaults(handler=invite)

    seed = commands.add_parser("dev-seed", help="тестовые учётные записи для разработки")
    seed.set_defaults(handler=dev_seed)

    args = parser.parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
