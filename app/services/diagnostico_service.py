import io
import os
import tempfile
from datetime import datetime, timezone

from fastapi import HTTPException
from PIL import Image

from app.repositories.diagnostico_repository import DiagnosticoRepository
from app.schemas.diagnostico import DiagnosticoDocument
from app.services.roboflow_service import roboflow_service
from app.services.s3_service import s3_service


class DiagnosticoService:
    def __init__(self) -> None:
        self.repo = DiagnosticoRepository()

    def _attach_fresh_signed_url(self, doc: dict) -> dict:
        key = doc.get("imagen_original_s3_key")
        if key:
            try:
                doc["imagen_original_url"] = s3_service.sign_get_url(key)
            except Exception:
                # Keep existing URL when signing fails to avoid breaking response payloads.
                pass
        return doc

    async def analizar(self, user_id: str, file_content: bytes, filename: str | None) -> dict:
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

            analysis = await roboflow_service.analyze_image(temp_path)

            base_name = filename or "image.jpg"
            original_key = s3_service.upload_image(file_content, f"original_{base_name}")
            original_url = s3_service.sign_get_url(original_key)

            now = datetime.now(timezone.utc)
            diagnostico_doc = DiagnosticoDocument(
                user_id=user_id,
                resultado=analysis["result_label"],
                confianza=float(analysis["confidence"]),
                clase_original=analysis["class_name"],
                estado="completado",
                imagen_original_s3_key=original_key,
                imagen_original_url=original_url,
                datos_roboflow=analysis.get("raw", {}),
                created_at=now,
                updated_at=now,
            )

            created = self.repo.create(diagnostico_doc.model_dump())
            created["id"] = str(created.pop("_id"))
            return created
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def historial(self, user_id: str, limit: int = 50) -> list[dict]:
        docs = self.repo.list_by_user(user_id=user_id, limit=limit)
        for doc in docs:
            self._attach_fresh_signed_url(doc)
            doc["id"] = str(doc.pop("_id"))
        return docs

    def detalle(self, user_id: str, diagnostico_id: str) -> dict | None:
        doc = self.repo.get_by_id_for_user(diagnostico_id=diagnostico_id, user_id=user_id)
        if not doc:
            return None
        self._attach_fresh_signed_url(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc


diagnostico_service = DiagnosticoService()
