from typing import Optional
from uuid import uuid4

from sqlalchemy import text

from app.db.sql import get_engine


USER_SELECT = """
SELECT
    u.id AS _id,
    u.username,
    u.password_hash,
    u.name,
    u.lastname,
    u.email,
    r.code AS role,
    u.status,
    u.profile_image_key,
    u.created_at,
    u.updated_at
FROM users u
JOIN user_roles r ON r.id = u.role_id
"""


class UserRepository:
    def __init__(self) -> None:
        self.engine = get_engine()

    def get_by_username(self, username: str) -> Optional[dict]:
        query = text(f"{USER_SELECT} WHERE u.username = :username")
        with self.engine.connect() as conn:
            row = conn.execute(query, {"username": username}).mappings().first()
            return dict(row) if row else None

    def get_by_email(self, email: str) -> Optional[dict]:
        query = text(f"{USER_SELECT} WHERE u.email = :email")
        with self.engine.connect() as conn:
            row = conn.execute(query, {"email": email}).mappings().first()
            return dict(row) if row else None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        query = text(f"{USER_SELECT} WHERE u.id = :user_id")
        with self.engine.connect() as conn:
            row = conn.execute(query, {"user_id": user_id}).mappings().first()
            return dict(row) if row else None

    def get_by_role(self, role: str) -> Optional[dict]:
        query = text(f"{USER_SELECT} WHERE r.code = :role ORDER BY u.created_at DESC LIMIT 1")
        with self.engine.connect() as conn:
            row = conn.execute(query, {"role": role}).mappings().first()
            return dict(row) if row else None

    def list_users(
        self,
        *,
        role: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        where = []
        params: dict = {"skip": skip, "limit": limit}
        if role is not None:
            where.append("r.code = :role")
            params["role"] = role
        if status is not None:
            where.append("u.status = :status")
            params["status"] = status

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        query = text(
            f"""
            {USER_SELECT}
            {where_sql}
            ORDER BY u.created_at DESC
            OFFSET :skip LIMIT :limit
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [dict(row) for row in rows]

    def count_users(self, *, role: Optional[str] = None, status: Optional[bool] = None) -> int:
        where = []
        params: dict = {}
        if role is not None:
            where.append("r.code = :role")
            params["role"] = role
        if status is not None:
            where.append("u.status = :status")
            params["status"] = status

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        query = text(
            f"""
            SELECT COUNT(*)
            FROM users u
            JOIN user_roles r ON r.id = u.role_id
            {where_sql}
            """
        )
        with self.engine.connect() as conn:
            return int(conn.execute(query, params).scalar_one())

    def update_by_id(self, user_id: str, payload: dict) -> Optional[dict]:
        if not payload:
            return self.get_by_id(user_id)

        updates = []
        params: dict = {"user_id": user_id}

        if "username" in payload:
            updates.append("username = :username")
            params["username"] = payload["username"]
        if "password_hash" in payload:
            updates.append("password_hash = :password_hash")
            params["password_hash"] = payload["password_hash"]
        if "name" in payload:
            updates.append("name = :name")
            params["name"] = payload["name"]
        if "lastname" in payload:
            updates.append("lastname = :lastname")
            params["lastname"] = payload["lastname"]
        if "email" in payload:
            updates.append("email = :email")
            params["email"] = payload["email"]
        if "status" in payload:
            updates.append("status = :status")
            params["status"] = payload["status"]
        if "profile_image_key" in payload:
            updates.append("profile_image_key = :profile_image_key")
            params["profile_image_key"] = payload["profile_image_key"]
        if "updated_at" in payload:
            updates.append("updated_at = :updated_at")
            params["updated_at"] = payload["updated_at"]
        if "role" in payload and payload["role"] is not None:
            updates.append("role_id = (SELECT id FROM user_roles WHERE code = :role)")
            params["role"] = payload["role"]

        if not updates:
            return self.get_by_id(user_id)

        query = text(f"UPDATE users SET {', '.join(updates)} WHERE id = :user_id")
        with self.engine.begin() as conn:
            result = conn.execute(query, params)
            if result.rowcount == 0:
                return None
        return self.get_by_id(user_id)

    def create(self, payload: dict) -> Optional[dict]:
        user_id = payload.get("id") or str(uuid4())
        query = text(
            """
            INSERT INTO users (
                id, username, password_hash, name, lastname, email, role_id, status, profile_image_key, created_at, updated_at
            ) VALUES (
                :id, :username, :password_hash, :name, :lastname, :email,
                (SELECT id FROM user_roles WHERE code = :role), :status, :profile_image_key, :created_at, :updated_at
            )
            """
        )
        params = {
            "id": user_id,
            "username": payload["username"],
            "password_hash": payload["password_hash"],
            "name": payload["name"],
            "lastname": payload["lastname"],
            "email": payload["email"],
            "role": payload.get("role", "paciente"),
            "status": payload.get("status", True),
            "profile_image_key": payload.get("profile_image_key"),
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
        }
        with self.engine.begin() as conn:
            conn.execute(query, params)
        return self.get_by_id(user_id)

    def search_patients(self, query_text: str, limit: int = 30) -> list[dict]:
        query = text(
            f"""
            {USER_SELECT}
            WHERE r.code = 'paciente'
              AND u.status = TRUE
              AND (
                u.username ILIKE :search
                OR u.name ILIKE :search
                OR u.lastname ILIKE :search
                OR u.email ILIKE :search
              )
            ORDER BY u.created_at DESC
            LIMIT :limit
            """
        )
        params = {"search": f"%{query_text}%", "limit": limit}
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [dict(row) for row in rows]

    def get_many_by_ids(self, ids: list[str]) -> list[dict]:
        filtered_ids = [value for value in ids if value]
        if not filtered_ids:
            return []

        query = text(
            f"""
            {USER_SELECT}
            WHERE u.id = ANY(:ids)
            ORDER BY u.created_at DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"ids": filtered_ids}).mappings().all()
            return [dict(row) for row in rows]
