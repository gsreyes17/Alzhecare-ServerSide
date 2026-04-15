from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str
    AWS_S3_BASE_PATH: str
    AWS_S3_PROFILE_BASE_PATH: str
    SIGNED_URL_EXPIRES_SECONDS: int

    CORS_ALLOW_ORIGINS: str = "*"

    DATABASE_URL: str
    SQL_AUTO_INIT: bool
    SQL_VERIFY_SCHEMA_ON_STARTUP: bool
    SQL_SEED_TEST_USERS: bool
    SQL_TEST_USERS_PASSWORD: str
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if not value or not value.strip() or value.strip().lower() in {"change_this_secret_key", "changeme"}:
            raise ValueError("SECRET_KEY invalida o vacia. Configura una clave robusta en el entorno.")
        if len(value.strip()) < 24:
            raise ValueError("SECRET_KEY debe tener al menos 24 caracteres.")
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("DATABASE_URL es obligatoria.")
        return value

    @field_validator("SQL_TEST_USERS_PASSWORD")
    @classmethod
    def validate_seed_password(cls, value: str, info) -> str:
        seed_enabled = bool(info.data.get("SQL_SEED_TEST_USERS", False))
        if seed_enabled and (not value or len(value) < 8):
            raise ValueError("SQL_TEST_USERS_PASSWORD debe existir y tener >= 8 caracteres cuando SQL_SEED_TEST_USERS=true")
        return value

    @property
    def cors_origins(self) -> list[str]:
        raw = (self.CORS_ALLOW_ORIGINS or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings() # pyright: ignore[reportCallIssue]
