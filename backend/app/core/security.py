"""Password hashing and secret tokens (stdlib only: scrypt, secrets, sha256)."""

import base64
import hashlib
import hmac
import secrets

# About 16 MB of memory and tens of milliseconds per hash: cheap for a login, costly for guessing.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LEN = 32
_SCRYPT_MAXMEM = 64 * 1024 * 1024

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 256


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_LEN,
        maxmem=_SCRYPT_MAXMEM,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = _unb64(digest)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_unb64(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
            maxmem=_SCRYPT_MAXMEM,
        )
    except ValueError:
        # A malformed stored hash never matches; the caller treats it as a wrong password.
        return False
    return hmac.compare_digest(candidate, expected)


# Checked against when the login does not exist, so both cases take the same time.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    """Only this digest is stored: a leaked database does not give working sessions or invites."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
