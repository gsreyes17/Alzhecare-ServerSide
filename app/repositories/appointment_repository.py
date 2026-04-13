from typing import Optional
from uuid import uuid4

from sqlalchemy import text

from app.db.sql import get_engine


class AppointmentRepository:
    def __init__(self) -> None:
        self.engine = get_engine()

    def create(self, payload: dict) -> dict:
        appointment_id = payload.get("id") or str(uuid4())
        query = text(
            """
            INSERT INTO appointments (
                id, doctor_user_id, patient_user_id, title, date_time, description, status, created_at, updated_at
            ) VALUES (
                :id, :doctor_user_id, :patient_user_id, :title, :date_time, :description, :status, :created_at, :updated_at
            )
            """
        )
        params = {
            "id": appointment_id,
            "doctor_user_id": payload["doctor_user_id"],
            "patient_user_id": payload["patient_user_id"],
            "title": payload["title"],
            "date_time": payload["date_time"],
            "description": payload["description"],
            "status": payload["status"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
        }
        with self.engine.begin() as conn:
            conn.execute(query, params)

        created = self.get_by_id(appointment_id)
        if not created:
            raise RuntimeError("No se pudo crear la cita")
        return created

    def list_by_doctor(self, doctor_user_id: str, status: str | None = None) -> list[dict]:
        where_sql = "AND status = :status" if status else ""
        params: dict = {"doctor_user_id": doctor_user_id}
        if status:
            params["status"] = status
        query = text(
            f"""
            SELECT
                id AS _id,
                doctor_user_id,
                patient_user_id,
                title,
                date_time,
                description,
                status,
                created_at,
                updated_at
            FROM appointments
            WHERE doctor_user_id = :doctor_user_id
            {where_sql}
            ORDER BY date_time DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [dict(row) for row in rows]

    def list_by_patient(self, patient_user_id: str, status: str | None = None) -> list[dict]:
        where_sql = "AND status = :status" if status else ""
        params: dict = {"patient_user_id": patient_user_id}
        if status:
            params["status"] = status
        query = text(
            f"""
            SELECT
                id AS _id,
                doctor_user_id,
                patient_user_id,
                title,
                date_time,
                description,
                status,
                created_at,
                updated_at
            FROM appointments
            WHERE patient_user_id = :patient_user_id
            {where_sql}
            ORDER BY date_time DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [dict(row) for row in rows]

    def list_all(self, status: str | None = None, skip: int = 0, limit: int = 100) -> list[dict]:
        where_sql = "WHERE status = :status" if status else ""
        params: dict = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        query = text(
            f"""
            SELECT
                id AS _id,
                doctor_user_id,
                patient_user_id,
                title,
                date_time,
                description,
                status,
                created_at,
                updated_at
            FROM appointments
            {where_sql}
            ORDER BY created_at DESC
            OFFSET :skip LIMIT :limit
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [dict(row) for row in rows]

    def count_all(self, status: str | None = None) -> int:
        where_sql = "WHERE status = :status" if status else ""
        params: dict = {"status": status} if status else {}
        query = text(f"SELECT COUNT(*) FROM appointments {where_sql}")
        with self.engine.connect() as conn:
            return int(conn.execute(query, params).scalar_one())

    def get_by_id(self, appointment_id: str) -> Optional[dict]:
        query = text(
            """
            SELECT
                id AS _id,
                doctor_user_id,
                patient_user_id,
                title,
                date_time,
                description,
                status,
                created_at,
                updated_at
            FROM appointments
            WHERE id = :appointment_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(query, {"appointment_id": appointment_id}).mappings().first()
            return dict(row) if row else None

    def update_status(self, appointment_id: str, status: str, updated_at) -> Optional[dict]:
        update_query = text(
            """
            UPDATE appointments
            SET status = :status, updated_at = :updated_at
            WHERE id = :appointment_id
            """
        )
        with self.engine.begin() as conn:
            result = conn.execute(
                update_query,
                {"appointment_id": appointment_id, "status": status, "updated_at": updated_at},
            )
            if result.rowcount == 0:
                return None
        return self.get_by_id(appointment_id)
