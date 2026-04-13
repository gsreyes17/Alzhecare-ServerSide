from typing import Optional

from bson import ObjectId

from app.db.mongo import get_users_collection


class UserRepository:
    def __init__(self) -> None:
        self.collection = get_users_collection()

    def get_by_username(self, username: str) -> Optional[dict]:
        return self.collection.find_one({"username": username})

    def get_by_email(self, email: str) -> Optional[dict]:
        return self.collection.find_one({"email": email})

    def get_by_id(self, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        return self.collection.find_one({"_id": oid})

    def get_by_role(self, role: str) -> Optional[dict]:
        return self.collection.find_one({"role": role})

    def list_users(
        self,
        *,
        role: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        query: dict = {}
        if role is not None:
            query["role"] = role
        if status is not None:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return list(cursor)

    def count_users(self, *, role: Optional[str] = None, status: Optional[bool] = None) -> int:
        query: dict = {}
        if role is not None:
            query["role"] = role
        if status is not None:
            query["status"] = status
        return self.collection.count_documents(query)

    def update_by_id(self, user_id: str, payload: dict) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        if not payload:
            return self.collection.find_one({"_id": oid})

        self.collection.update_one({"_id": oid}, {"$set": payload})
        return self.collection.find_one({"_id": oid})

    def create(self, payload: dict) -> Optional[dict]:
        result = self.collection.insert_one(payload)
        created = self.collection.find_one({"_id": result.inserted_id})
        return created

    def search_patients(self, query_text: str, limit: int = 30) -> list[dict]:
        query = {
            "role": "patient",
            "status": True,
            "$or": [
                {"username": {"$regex": query_text, "$options": "i"}},
                {"name": {"$regex": query_text, "$options": "i"}},
                {"lastname": {"$regex": query_text, "$options": "i"}},
                {"email": {"$regex": query_text, "$options": "i"}},
            ],
        }
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        return list(cursor)

    def get_many_by_ids(self, ids: list[str]) -> list[dict]:
        object_ids = []
        for raw_id in ids:
            try:
                object_ids.append(ObjectId(raw_id))
            except Exception:
                continue

        if not object_ids:
            return []
        return list(self.collection.find({"_id": {"$in": object_ids}}))
