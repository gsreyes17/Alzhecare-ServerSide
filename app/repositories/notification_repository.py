from typing import Optional

from bson import ObjectId

from app.db.mongo import get_notifications_collection


class NotificationRepository:
    def __init__(self) -> None:
        self.collection = get_notifications_collection()

    def create(self, payload: dict) -> dict:
        result = self.collection.insert_one(payload)
        created = self.collection.find_one({"_id": result.inserted_id})
        if not created:
            raise RuntimeError("No se pudo crear la notificación")
        return created

    def list_by_user(self, user_id: str, solo_no_leidas: bool = False) -> list[dict]:
        query: dict = {"user_id": user_id}
        if solo_no_leidas:
            query["leida"] = False
        cursor = self.collection.find(query).sort("created_at", -1)
        return list(cursor)

    def get_by_id_for_user(self, notification_id: str, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(notification_id)
        except Exception:
            return None
        return self.collection.find_one({"_id": oid, "user_id": user_id})

    def mark_as_read(self, notification_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(notification_id)
        except Exception:
            return None
        self.collection.update_one({"_id": oid}, {"$set": {"leida": True}})
        return self.collection.find_one({"_id": oid})
