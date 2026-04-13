import io
import os
import tempfile
from datetime import datetime, timezone

from fastapi import HTTPException
from PIL import Image

from app.repositories.diagnostico_repository import DiagnosisRepository
from app.schemas.diagnostico import DiagnosisDocument
from app.services.s3_service import s3_service
from app.services.torch_service import torch_service


class DiagnosisService:
    def __init__(self) -> None:
        self.repo = DiagnosisRepository()

    def _attach_fresh_signed_url(self, doc: dict) -> dict:
        key = doc.get("image_s3_key")
        if key:
            try:
                doc["image_url"] = s3_service.sign_get_url(key)
            except Exception:
                # Keep existing URL when signing fails to avoid breaking response payloads.
                pass
        return doc

    async def analyze(self, user_id: str, file_content: bytes, filename: str | None) -> dict:
        try:
            image = Image.open(io.BytesIO(file_content))
            if image.mode != "RGB":
                image = image.convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"El archivo no es una imagen válida: {exc}") from exc

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = temp_file.name
                image.save(temp_path, "JPEG", quality=90)

            analysis = await torch_service.analyze_image(temp_path)

            base_name = filename or "image.jpg"
            original_key = s3_service.upload_image(file_content, f"original_{base_name}")
            original_url = s3_service.sign_get_url(original_key)

            now = datetime.now(timezone.utc)
            diagnosis_doc = DiagnosisDocument(
                user_id=user_id,
                result=analysis["result_label"],
                confidence=float(analysis["confidence"]),
                status="completado",
                image_s3_key=original_key,
                image_url=original_url,
                model_output=analysis.get("raw", {}),
                created_at=now,
                updated_at=now,
            )

            created = self.repo.create(diagnosis_doc.model_dump())
            if created is None:
                raise HTTPException(status_code=500, detail="Error al crear el diagnóstico")
            created["id"] = str(created.pop("_id"))
            return created
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def history(self, user_id: str, limit: int = 50) -> list[dict]:
        docs = self.repo.list_by_user(user_id=user_id, limit=limit)
        for doc in docs:
            self._attach_fresh_signed_url(doc)
            doc["id"] = str(doc.pop("_id"))
        return docs

    def detail(self, user_id: str, diagnosis_id: str) -> dict | None:
        doc = self.repo.get_by_id_for_user(diagnosis_id=diagnosis_id, user_id=user_id)
        if not doc:
            return None
        self._attach_fresh_signed_url(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc


diagnosis_service = DiagnosisService()
