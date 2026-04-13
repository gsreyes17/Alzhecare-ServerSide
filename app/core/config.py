from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Alzhecare API"
    debug: bool = False

    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    torch_model_path: str = str(Path("app") / "models" / "v1" / "alzheimer_ensemble_v1.pth")
    torch_label_classes_path: str = str(Path("app") / "models" / "v1" / "le_classes.pkl")
    torch_device: str = "auto"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = ""
    aws_s3_base_path: str = "analyses"
    aws_s3_profile_base_path: str = "profiles"
    signed_url_expires_seconds: int = 3600
    cors_allow_origins: str = "*"

    database_url: str = ""
    sql_auto_init: bool = False
    sql_verify_schema_on_startup: bool = True
    sql_seed_test_users: bool = False
    sql_test_users_password: str = ""

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if not value or not value.strip() or value.strip().lower() in {"change_this_secret_key", "changeme"}:
            raise ValueError("SECRET_KEY invalida o vacia. Configura una clave robusta en el entorno.")
        if len(value.strip()) < 24:
            raise ValueError("SECRET_KEY debe tener al menos 24 caracteres.")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("DATABASE_URL es obligatoria.")
        return value

    @field_validator("sql_test_users_password")
    @classmethod
    def validate_seed_password(cls, value: str, info) -> str:
        seed_enabled = bool(info.data.get("sql_seed_test_users", False))
        if seed_enabled and (not value or len(value) < 8):
            raise ValueError("SQL_TEST_USERS_PASSWORD debe existir y tener >= 8 caracteres cuando SQL_SEED_TEST_USERS=true")
        return value

    @property
    def cors_origins(self) -> list[str]:
        raw = (self.cors_allow_origins or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
