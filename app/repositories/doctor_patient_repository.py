from uuid import uuid4

from sqlalchemy import text

from app.db.sql import get_engine


class DoctorPatientRepository:
    def __init__(self) -> None:
        self.engine = get_engine()

    def create(self, payload: dict) -> dict:
        link_id = payload.get("id") or str(uuid4())
        query = text(
            """
            INSERT INTO doctor_patient_links (
                id, doctor_user_id, patient_user_id, status, created_at, updated_at
            ) VALUES (
                :id, :doctor_user_id, :patient_user_id, :status, :created_at, :updated_at
            )
            """
        )
        params = {
            "id": link_id,
            "doctor_user_id": payload["doctor_user_id"],
            "patient_user_id": payload["patient_user_id"],
            "status": payload["status"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
        }
        with self.engine.begin() as conn:
            conn.execute(query, params)

        created = {
            "_id": link_id,
            "doctor_user_id": payload["doctor_user_id"],
            "patient_user_id": payload["patient_user_id"],
            "status": payload["status"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
        }
        return created

    def exists_link(self, doctor_user_id: str, patient_user_id: str) -> bool:
        query = text(
            """
            SELECT 1
            FROM doctor_patient_links
            WHERE doctor_user_id = :doctor_user_id
              AND patient_user_id = :patient_user_id
              AND status = 'activo'
            LIMIT 1
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(
                query,
                {"doctor_user_id": doctor_user_id, "patient_user_id": patient_user_id},
            ).first()
            return row is not None

    def list_patient_ids_by_doctor(self, doctor_user_id: str) -> list[str]:
        query = text(
            """
            SELECT patient_user_id
            FROM doctor_patient_links
            WHERE doctor_user_id = :doctor_user_id AND status = 'activo'
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"doctor_user_id": doctor_user_id}).mappings().all()
            return [row["patient_user_id"] for row in rows]

    def list_doctor_ids_by_patient(self, patient_user_id: str) -> list[str]:
        query = text(
            """
            SELECT doctor_user_id
            FROM doctor_patient_links
            WHERE patient_user_id = :patient_user_id AND status = 'activo'
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"patient_user_id": patient_user_id}).mappings().all()
            return [row["doctor_user_id"] for row in rows]
