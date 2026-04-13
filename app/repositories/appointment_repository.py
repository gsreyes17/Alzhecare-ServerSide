from typing import Optional

from bson import ObjectId

from app.db.mongo import get_appointments_collection


class AppointmentRepository:
    def __init__(self) -> None:
        self.collection = get_appointments_collection()

    def create(self, payload: dict) -> dict:
        result = self.collection.insert_one(payload)
        created = self.collection.find_one({"_id": result.inserted_id})
        if not created:
            raise RuntimeError("No se pudo crear la cita")
        return created

    def list_by_doctor(self, doctor_user_id: str, status: str | None = None) -> list[dict]:
        query: dict = {"doctor_user_id": doctor_user_id}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("date_time", -1)
        return list(cursor)

    def list_by_patient(self, patient_user_id: str, status: str | None = None) -> list[dict]:
        query: dict = {"patient_user_id": patient_user_id}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("date_time", -1)
        return list(cursor)

    def list_all(self, status: str | None = None, skip: int = 0, limit: int = 100) -> list[dict]:
        query: dict = {}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return list(cursor)

    def count_all(self, status: str | None = None) -> int:
        query: dict = {}
        if status:
            query["status"] = status
        return self.collection.count_documents(query)

    def get_by_id(self, appointment_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(appointment_id)
        except Exception:
            return None
        return self.collection.find_one({"_id": oid})

    def update_status(self, appointment_id: str, status: str, updated_at) -> Optional[dict]:
        try:
            oid = ObjectId(appointment_id)
        except Exception:
            return None
        self.collection.update_one({"_id": oid}, {"$set": {"status": status, "updated_at": updated_at}})
        return self.collection.find_one({"_id": oid})
