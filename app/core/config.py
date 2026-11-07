from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Payder"
    database_url: str = f"sqlite:///{(ROOT_DIR / 'data' / 'payder.db').as_posix()}"
    admin_password: str = "change-me"
    secret_key: str = "replace-with-a-long-random-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
