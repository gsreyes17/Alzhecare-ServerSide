import json
from typing import Optional
from uuid import uuid4

from sqlalchemy import text

from app.db.sql import get_engine


class NotificationRepository:
    def __init__(self) -> None:
        self.engine = get_engine()

    def _normalize_row(self, row: dict) -> dict:
        output = dict(row)
        raw_data = output.get("data")
        if isinstance(raw_data, str):
            try:
                output["data"] = json.loads(raw_data)
            except Exception:
                output["data"] = {}
        return output

    def create(self, payload: dict) -> dict:
        notification_id = payload.get("id") or str(uuid4())
        query = text(
            """
            INSERT INTO notifications (
                id, user_id, type, title, message, data, read, created_at
            ) VALUES (
                :id, :user_id, :type, :title, :message, :data, :read, :created_at
            )
            """
        )
        params = {
            "id": notification_id,
            "user_id": payload["user_id"],
            "type": payload["type"],
            "title": payload["title"],
            "message": payload["message"],
            "data": json.dumps(payload.get("data", {})),
            "read": payload.get("read", False),
            "created_at": payload["created_at"],
        }
        with self.engine.begin() as conn:
            conn.execute(query, params)

        created = self.get_by_id_for_user(notification_id, payload["user_id"])
        if not created:
            raise RuntimeError("No se pudo crear la notificación")
        return created

    def list_by_user(self, user_id: str, unread_only: bool = False) -> list[dict]:
        where_sql = "AND read = FALSE" if unread_only else ""
        query = text(
            f"""
            SELECT
                id AS _id,
                user_id,
                type,
                title,
                message,
                data,
                read,
                created_at
            FROM notifications
            WHERE user_id = :user_id
            {where_sql}
            ORDER BY created_at DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"user_id": user_id}).mappings().all()
            return [self._normalize_row(dict(row)) for row in rows]

    def get_by_id_for_user(self, notification_id: str, user_id: str) -> Optional[dict]:
        query = text(
            """
            SELECT
                id AS _id,
                user_id,
                type,
                title,
                message,
                data,
                read,
                created_at
            FROM notifications
            WHERE id = :notification_id AND user_id = :user_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(
                query,
                {"notification_id": notification_id, "user_id": user_id},
            ).mappings().first()
            return self._normalize_row(dict(row)) if row else None

    def mark_as_read(self, notification_id: str) -> Optional[dict]:
        update_query = text(
            """
            UPDATE notifications
            SET read = TRUE
            WHERE id = :notification_id
            """
        )
        with self.engine.begin() as conn:
            result = conn.execute(update_query, {"notification_id": notification_id})
            if result.rowcount == 0:
                return None

        query = text(
            """
            SELECT
                id AS _id,
                user_id,
                type,
                title,
                message,
                data,
                read,
                created_at
            FROM notifications
            WHERE id = :notification_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(query, {"notification_id": notification_id}).mappings().first()
            return self._normalize_row(dict(row)) if row else None
