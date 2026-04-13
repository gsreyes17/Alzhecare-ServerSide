from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_current_active_user
from app.schemas.diagnostico import AnalysisResponse, DiagnosisResponse
from app.services.diagnostico_service import diagnostico_service

router = APIRouter(prefix="/api/diagnosticos", tags=["Diagnosticos"])


@router.post("/analizar", response_model=AnalysisResponse)
async def analizar_imagen(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
) -> AnalysisResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        created = await diagnostico_service.analizar(
            user_id=current_user["id"],
            file_content=contents,
            filename=file.filename,
        )
        return AnalysisResponse(
            id=created["id"],
            result=created["result"],
            confidence=created["confidence"],
            image_url=created["image_url"],
            created_at=created["created_at"],
        )
    finally:
        await file.close()


@router.get("/historial", response_model=Dict[str, Any])
async def obtener_historial_diagnosticos(
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
) -> Dict[str, Any]:
    docs = diagnostico_service.historial(user_id=current_user["id"], limit=limit)
    return {"diagnosticos": docs, "total": len(docs)}


@router.get("/mis-diagnosticos", response_model=List[DiagnosisResponse])
async def obtener_mis_diagnosticos(
    current_user: dict = Depends(get_current_active_user),
) -> List[DiagnosisResponse]:
    docs = diagnostico_service.historial(user_id=current_user["id"], limit=100)
    return [
        DiagnosisResponse(
            id=doc["id"],
            user_id=doc["user_id"],
            result=doc["result"],
            confidence=doc["confidence"],
            status=doc["status"],
            image_url=doc["image_url"],
            created_at=doc["created_at"],
        )
        for doc in docs
    ]


@router.get("/detalle/{diagnostico_id}", response_model=Dict[str, Any])
async def obtener_detalle_diagnostico(
    diagnostico_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Dict[str, Any]:
    doc = diagnostico_service.detalle(user_id=current_user["id"], diagnostico_id=diagnostico_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    return doc


@router.get("/{diagnostico_id}", response_model=DiagnosisResponse)
async def obtener_diagnostico(
    diagnostico_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> DiagnosisResponse:
    doc = diagnostico_service.detalle(user_id=current_user["id"], diagnostico_id=diagnostico_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    return DiagnosisResponse(
        id=doc["id"],
        user_id=doc["user_id"],
        result=doc["result"],
        confidence=doc["confidence"],
        status=doc["status"],
        image_url=doc["image_url"],
        created_at=doc["created_at"],
    )
