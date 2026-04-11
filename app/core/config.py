from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Alzhecare API"
    debug: bool = True

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    initial_admin_username: str | None = None
    initial_admin_password: str | None = None
    initial_admin_nombre: str | None = None
    initial_admin_apellido: str | None = None
    initial_admin_email: str | None = None

    torch_model_path: str = str(Path("app") / "models" / "v1" / "alzheimer_ensemble_v1.pth")
    torch_label_classes_path: str = str(Path("app") / "models" / "v1" / "le_classes.pkl")
    torch_device: str = "auto"

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    aws_s3_bucket: str
    aws_s3_base_path: str = "analyses"
    aws_s3_profile_base_path: str = "profiles"
    signed_url_expires_seconds: int = 3600

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "roboflow_simple"
    mongodb_users_collection: str = "users"
    mongodb_analyses_collection: str = "analyses"
    mongodb_doctor_requests_collection: str = "doctor_requests"
    mongodb_doctor_patient_links_collection: str = "doctor_patient_links"
    mongodb_appointments_collection: str = "appointments"
    mongodb_notifications_collection: str = "notifications"


@lru_cache
def get_settings() -> Settings:
    return Settings()
