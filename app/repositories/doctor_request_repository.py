from typing import Optional
from uuid import uuid4

from sqlalchemy import text

from app.db.sql import get_engine
from app.schemas.coordination import RequestStatus


class DoctorRequestRepository:
    def __init__(self) -> None:
        self.engine = get_engine()

    def create(self, payload: dict) -> dict:
        request_id = payload.get("id") or str(uuid4())
        query = text(
            """
            INSERT INTO doctor_requests (
                id, doctor_user_id, patient_user_id, status, created_at, updated_at
            ) VALUES (
                :id, :doctor_user_id, :patient_user_id, :status, :created_at, :updated_at
            )
            """
        )
        params = {
            "id": request_id,
            "doctor_user_id": payload["doctor_user_id"],
            "patient_user_id": payload["patient_user_id"],
            "status": payload["status"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
        }
        with self.engine.begin() as conn:
            conn.execute(query, params)

        created = self.get_by_id_for_patient(request_id, payload["patient_user_id"])
        if not created:
            raise RuntimeError("No se pudo crear la solicitud de vinculación")
        return created

    def get_pending(self, doctor_user_id: str, patient_user_id: str) -> Optional[dict]:
        query = text(
            """
            SELECT id AS _id, doctor_user_id, patient_user_id, status, created_at, updated_at
            FROM doctor_requests
            WHERE doctor_user_id = :doctor_user_id
              AND patient_user_id = :patient_user_id
              AND status = :status
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(
                query,
                {
                    "doctor_user_id": doctor_user_id,
                    "patient_user_id": patient_user_id,
                    "status": RequestStatus.pending.value,
                },
            ).mappings().first()
            return dict(row) if row else None

    def list_by_doctor(self, doctor_user_id: str) -> list[dict]:
        query = text(
            """
            SELECT id AS _id, doctor_user_id, patient_user_id, status, created_at, updated_at
            FROM doctor_requests
            WHERE doctor_user_id = :doctor_user_id
            ORDER BY created_at DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"doctor_user_id": doctor_user_id}).mappings().all()
            return [dict(row) for row in rows]

    def list_pending_by_patient(self, patient_user_id: str) -> list[dict]:
        query = text(
            """
            SELECT id AS _id, doctor_user_id, patient_user_id, status, created_at, updated_at
            FROM doctor_requests
            WHERE patient_user_id = :patient_user_id
              AND status = :status
            ORDER BY created_at DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(
                query,
                {"patient_user_id": patient_user_id, "status": RequestStatus.pending.value},
            ).mappings().all()
            return [dict(row) for row in rows]

    def get_by_id_for_patient(self, request_id: str, patient_user_id: str) -> Optional[dict]:
        query = text(
            """
            SELECT id AS _id, doctor_user_id, patient_user_id, status, created_at, updated_at
            FROM doctor_requests
            WHERE id = :request_id AND patient_user_id = :patient_user_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(
                query,
                {"request_id": request_id, "patient_user_id": patient_user_id},
            ).mappings().first()
            return dict(row) if row else None

    def update_status(self, request_id: str, status: str, updated_at) -> Optional[dict]:
        update_query = text(
            """
            UPDATE doctor_requests
            SET status = :status, updated_at = :updated_at
            WHERE id = :request_id
            """
        )
        with self.engine.begin() as conn:
            result = conn.execute(
                update_query,
                {"request_id": request_id, "status": status, "updated_at": updated_at},
            )
            if result.rowcount == 0:
                return None

        query = text(
            """
            SELECT id AS _id, doctor_user_id, patient_user_id, status, created_at, updated_at
            FROM doctor_requests
            WHERE id = :request_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(query, {"request_id": request_id}).mappings().first()
            return dict(row) if row else None
