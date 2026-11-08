from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]

_PLACEHOLDERS = {"", "change-me", "replace-with-a-long-random-secret"}
_HOWTO = "python -c \"import secrets; print(secrets.token_urlsafe(48))\""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Payder"
    database_url: str = f"sqlite:///{(ROOT_DIR / 'data' / 'payder.db').as_posix()}"

    # Секреты обязательны: безопасных значений по умолчанию нет.
    # Без них приложение не запустится (см. .env.example).
    admin_password: str
    secret_key: str

    # Ставьте true, если TLS завершается на прокси и приложение видит http.
    cookie_secure: bool = False
    # Дополнительные источники запросов (Origin), которым разрешены POST/PUT,
    # например ["https://payder.example.com"]. Свой Host разрешён всегда.
    allowed_origins: list[str] = []
    # Сколько раз за сутки один пользователь может открыть реквизиты новых карточек.
    help_daily_limit: int = 10
    # Временная документация API включается только в локальной тестовой среде.
    enable_docs: bool = False

    @field_validator("secret_key")
    @classmethod
    def _check_secret_key(cls, value: str) -> str:
        if value.strip() in _PLACEHOLDERS or len(value) < 32:
            raise ValueError(f"SECRET_KEY должен быть случайным и не короче 32 символов. Сгенерировать: {_HOWTO}")
        return value

    @field_validator("admin_password")
    @classmethod
    def _check_admin_password(cls, value: str) -> str:
        if value.strip() in _PLACEHOLDERS or len(value) < 12:
            raise ValueError(f"ADMIN_PASSWORD не должен быть значением по умолчанию и должен быть не короче 12 символов. Сгенерировать: {_HOWTO}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
