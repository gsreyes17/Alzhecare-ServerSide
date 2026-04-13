from typing import List, Optional

from bson import ObjectId

from app.db.mongo import get_analyses_collection


class DiagnosticoRepository:
    def __init__(self) -> None:
        self.collection = get_analyses_collection()

    def create(self, payload: dict) -> Optional[dict]:
        result = self.collection.insert_one(payload)
        return self.collection.find_one({"_id": result.inserted_id})

    def list_by_user(self, user_id: str, limit: int = 50) -> List[dict]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return list(cursor)

    def get_by_id_for_user(self, diagnostico_id: str, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(diagnostico_id)
        except Exception:
            return None
        return self.collection.find_one({"_id": oid, "user_id": user_id})
