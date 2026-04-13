from typing import Optional

from bson import ObjectId

from app.db.mongo import get_doctor_requests_collection
from app.schemas.coordinacion import RequestStatus


class DoctorRequestRepository:
    def __init__(self) -> None:
        self.collection = get_doctor_requests_collection()

    def create(self, payload: dict) -> dict:
        result = self.collection.insert_one(payload)
        created = self.collection.find_one({"_id": result.inserted_id})
        if not created:
            raise RuntimeError("No se pudo crear la solicitud de vinculación")
        return created

    def get_pending(self, doctor_user_id: str, patient_user_id: str) -> Optional[dict]:
        return self.collection.find_one(
            {
                "doctor_user_id": doctor_user_id,
                "patient_user_id": patient_user_id,
                "status": RequestStatus.pending.value,
            }
        )

    def list_by_doctor(self, doctor_user_id: str) -> list[dict]:
        cursor = self.collection.find({"doctor_user_id": doctor_user_id}).sort("created_at", -1)
        return list(cursor)

    def list_pending_by_patient(self, patient_user_id: str) -> list[dict]:
        cursor = self.collection.find(
            {
                "patient_user_id": patient_user_id,
                "status": RequestStatus.pending.value,
            }
        ).sort("created_at", -1)
        return list(cursor)

    def get_by_id_for_patient(self, request_id: str, patient_user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(request_id)
        except Exception:
            return None
        return self.collection.find_one({"_id": oid, "patient_user_id": patient_user_id})

    def update_status(self, request_id: str, status: str, updated_at) -> Optional[dict]:
        try:
            oid = ObjectId(request_id)
        except Exception:
            return None
        self.collection.update_one({"_id": oid}, {"$set": {"status": status, "updated_at": updated_at}})
        return self.collection.find_one({"_id": oid})
