from app.db.mongo import get_doctor_patient_links_collection


class DoctorPatientRepository:
    def __init__(self) -> None:
        self.collection = get_doctor_patient_links_collection()

    def create(self, payload: dict) -> dict:
        result = self.collection.insert_one(payload)
        created = self.collection.find_one({"_id": result.inserted_id})
        if not created:
            raise RuntimeError("No se pudo crear el vínculo doctor-paciente")
        return created

    def exists_link(self, doctor_user_id: str, patient_user_id: str) -> bool:
        return (
            self.collection.find_one(
                {
                    "doctor_user_id": doctor_user_id,
                    "patient_user_id": patient_user_id,
                    "estado": "activo",
                }
            )
            is not None
        )

    def list_patient_ids_by_doctor(self, doctor_user_id: str) -> list[str]:
        cursor = self.collection.find({"doctor_user_id": doctor_user_id, "estado": "activo"})
        return [doc["patient_user_id"] for doc in cursor]

    def list_doctor_ids_by_patient(self, patient_user_id: str) -> list[str]:
        cursor = self.collection.find({"patient_user_id": patient_user_id, "estado": "activo"})
        return [doc["doctor_user_id"] for doc in cursor]
