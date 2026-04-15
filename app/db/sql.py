from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.core.security import get_password_hash

_engine: Engine | None = None

REQUIRED_TABLES = (
    "user_roles",
    "users",
    "diagnosis_statuses",
    "diagnoses",
    "doctor_patient_link_statuses",
    "doctor_patient_links",
    "doctor_request_statuses",
    "doctor_requests",
    "appointment_statuses",
    "appointments",
    "notification_types",
    "notifications",
)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def _read_schema_statements() -> list[str]:
    schema_path = Path(__file__).with_name("schema_normalized.sql")
    if not schema_path.exists():
        return []

    script = schema_path.read_text(encoding="utf-8")
    return [stmt.strip() for stmt in script.split(";") if stmt.strip()]


def _missing_tables(connection) -> set[str]:
    query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = current_schema()
        """
    )
    rows = connection.execute(query).mappings().all()
    existing = {row["table_name"] for row in rows}
    return set(REQUIRED_TABLES) - existing # pyright: ignore[reportReturnType]


def _seed_basic_test_users(connection) -> None:
    settings = get_settings()
    if not settings.SQL_SEED_TEST_USERS:
        return

    now = datetime.now(timezone.utc)
    password_hash = get_password_hash(settings.SQL_TEST_USERS_PASSWORD)
    users = [
        {
            "username": "admin_",
            "email": "test_admin@alzhecare.com",
            "name": "Test",
            "lastname": "Admin",
            "role": "admin",
        },
        {
            "username": "doctor_",
            "email": "test_doctor@alzhecare.com",
            "name": "Test",
            "lastname": "Doctor",
            "role": "doctor",
        },
        {
            "username": "paciente_",
            "email": "test_patient@alzhecare.com",
            "name": "Test",
            "lastname": "Patient",
            "role": "paciente",
        },
    ]

    exists_query = text(
        """
        SELECT 1
        FROM users
        WHERE username = CAST(:username AS VARCHAR)
           OR email = CAST(:email AS VARCHAR)
        LIMIT 1
        """
    )

    insert_query = text(
        """
        INSERT INTO users (
            id, username, password_hash, name, lastname, email, role_id, status, created_at, updated_at
        )
        VALUES (
            CAST(:id AS CHAR(36)),
            CAST(:username AS VARCHAR),
            CAST(:password_hash AS VARCHAR),
            CAST(:name AS VARCHAR),
            CAST(:lastname AS VARCHAR),
            CAST(:email AS VARCHAR),
            (SELECT id FROM user_roles WHERE code = CAST(:role AS VARCHAR)),
            TRUE,
            :created_at,
            :updated_at
        )
        """
    )

    for user in users:
        exists = connection.execute(
            exists_query,
            {
                "username": user["username"],
                "email": user["email"],
            },
        ).first()
        if exists:
            continue

        connection.execute(
            insert_query,
            {
                "id": str(uuid4()),
                "username": user["username"],
                "password_hash": password_hash,
                "name": user["name"],
                "lastname": user["lastname"],
                "email": user["email"],
                "role": user["role"],
                "created_at": now,
                "updated_at": now,
            },
        )


def init_sql_schema_if_enabled() -> None:
    settings = get_settings()
    if not settings.SQL_AUTO_INIT:
        return

    schema_path = Path(__file__).with_name("schema_normalized.sql")
    if not schema_path.exists():
        return

    script = schema_path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in script.split(";") if stmt.strip()]
    if not statements:
        return

    engine = get_engine()
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def verify_and_bootstrap_database() -> None:
    settings = get_settings()
    if not settings.SQL_VERIFY_SCHEMA_ON_STARTUP:
        return

    statements = _read_schema_statements()
    if not statements:
        return

    engine = get_engine()
    with engine.begin() as connection:
        missing = _missing_tables(connection)
        if missing:
            for statement in statements:
                connection.execute(text(statement))

        if not _missing_tables(connection):
            _seed_basic_test_users(connection)
