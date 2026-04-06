from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import get_settings


_client: MongoClient | None = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_users_collection() -> Collection:
    settings = get_settings()
    client = _get_client()
    db = client[settings.mongodb_db_name]
    return db[settings.mongodb_users_collection]


def get_analyses_collection() -> Collection:
    settings = get_settings()
    client = _get_client()
    db = client[settings.mongodb_db_name]
    return db[settings.mongodb_analyses_collection]


def get_doctor_requests_collection() -> Collection:
    settings = get_settings()
    client = _get_client()
    db = client[settings.mongodb_db_name]
    return db[settings.mongodb_doctor_requests_collection]


def get_doctor_patient_links_collection() -> Collection:
    settings = get_settings()
    client = _get_client()
    db = client[settings.mongodb_db_name]
    return db[settings.mongodb_doctor_patient_links_collection]


def get_appointments_collection() -> Collection:
    settings = get_settings()
    client = _get_client()
    db = client[settings.mongodb_db_name]
    return db[settings.mongodb_appointments_collection]


def get_notifications_collection() -> Collection:
    settings = get_settings()
    client = _get_client()
    db = client[settings.mongodb_db_name]
    return db[settings.mongodb_notifications_collection]
