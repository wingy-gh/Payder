import base64
import hashlib
import hmac
import json
import secrets
import time
from functools import lru_cache

from app.core.config import get_settings

_ITERATIONS = 310_000
SESSION_TTL = 60 * 60 * 24 * 14
ADMIN_TTL = 60 * 60 * 8


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


@lru_cache
def _dummy_hash() -> str:
    return hash_password(secrets.token_urlsafe(16))


def dummy_verify(password: str) -> None:
    """Тратит столько же времени, сколько реальная проверка пароля.

    Вызывается, когда пользователя не существует, чтобы по времени ответа
    нельзя было отличить «нет такого логина» от «неверный пароль».
    """
    verify_password(password, _dummy_hash())


def verify_admin_password(candidate: str) -> bool:
    expected = get_settings().admin_password
    # Сравниваем хеши одинаковой длины, чтобы не светить длину пароля по времени.
    return hmac.compare_digest(
        hashlib.sha256(candidate.encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body: str) -> bytes:
    return hmac.new(get_settings().secret_key.encode(), body.encode(), hashlib.sha256).digest()


def _issue(claims: dict, ttl: int) -> str:
    payload = {**claims, "exp": int(time.time()) + ttl}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_b64(_sign(body))}"


def _read(token: str) -> dict | None:
    try:
        body, signature_text = token.split(".", 1)
        if not hmac.compare_digest(_unb64(signature_text), _sign(body)):
            return None
        payload = json.loads(_unb64(body))
        if not isinstance(payload, dict) or int(payload["exp"]) < int(time.time()):
            return None
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def create_session_token(user_id: int, version: int = 0) -> str:
    return _issue({"sub": user_id, "ver": version, "typ": "user"}, SESSION_TTL)


def read_session_token(token: str) -> tuple[int, int] | None:
    """Возвращает (user_id, token_version) или None."""
    payload = _read(token)
    if payload is None or payload.get("typ", "user") != "user":
        return None
    try:
        return int(payload["sub"]), int(payload.get("ver", 0))
    except (KeyError, ValueError, TypeError):
        return None


def create_admin_token() -> str:
    return _issue({"typ": "admin", "jti": secrets.token_urlsafe(8)}, ADMIN_TTL)


def read_admin_token(token: str) -> bool:
    payload = _read(token)
    return payload is not None and payload.get("typ") == "admin"
