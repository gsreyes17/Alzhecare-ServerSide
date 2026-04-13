import json
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import text

from app.db.sql import get_engine


class DiagnosisRepository:
    def __init__(self) -> None:
        self.engine = get_engine()

    def _normalize_row(self, row: dict) -> dict:
        output = dict(row)
        raw_model_output = output.get("model_output")
        if isinstance(raw_model_output, str):
            try:
                output["model_output"] = json.loads(raw_model_output)
            except Exception:
                output["model_output"] = {}
        return output

    def create(self, payload: dict) -> Optional[dict]:
        diagnosis_id = payload.get("id") or str(uuid4())
        query = text(
            """
            INSERT INTO diagnoses (
                id, user_id, result, confidence, status, image_s3_key, image_url, model_output, created_at, updated_at
            ) VALUES (
                :id, :user_id, :result, :confidence, :status, :image_s3_key, :image_url, :model_output, :created_at, :updated_at
            )
            """
        )
        params = {
            "id": diagnosis_id,
            "user_id": payload["user_id"],
            "result": payload["result"],
            "confidence": payload["confidence"],
            "status": payload["status"],
            "image_s3_key": payload["image_s3_key"],
            "image_url": payload["image_url"],
            "model_output": json.dumps(payload.get("model_output", {})),
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
        }
        with self.engine.begin() as conn:
            conn.execute(query, params)
        return self.get_by_id_for_user(diagnosis_id=diagnosis_id, user_id=payload["user_id"])

    def list_by_user(self, user_id: str, limit: int = 50) -> List[dict]:
        query = text(
            """
            SELECT
                id AS _id,
                user_id,
                result,
                confidence,
                status,
                image_s3_key,
                image_url,
                model_output,
                created_at,
                updated_at
            FROM diagnoses
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"user_id": user_id, "limit": limit}).mappings().all()
            return [self._normalize_row(dict(row)) for row in rows]

    def get_by_id_for_user(self, diagnosis_id: str, user_id: str) -> Optional[dict]:
        query = text(
            """
            SELECT
                id AS _id,
                user_id,
                result,
                confidence,
                status,
                image_s3_key,
                image_url,
                model_output,
                created_at,
                updated_at
            FROM diagnoses
            WHERE id = :diagnosis_id AND user_id = :user_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(query, {"diagnosis_id": diagnosis_id, "user_id": user_id}).mappings().first()
            return self._normalize_row(dict(row)) if row else None
