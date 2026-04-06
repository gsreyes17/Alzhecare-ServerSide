from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_current_active_user
from app.schemas.diagnostico import AnalisisResponse, DiagnosticoResponse
from app.services.diagnostico_service import diagnostico_service

router = APIRouter(prefix="/api/diagnosticos", tags=["Diagnosticos"])


@router.post("/analizar", response_model=AnalisisResponse)
async def analizar_imagen(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
) -> AnalisisResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        created = await diagnostico_service.analizar(
            user_id=current_user["id"],
            file_content=contents,
            filename=file.filename,
        )
        return AnalisisResponse(
            id=created["id"],
            resultado=created["resultado"],
            confianza=created["confianza"],
            clase_original=created["clase_original"],
            imagen_original_url=created["imagen_original_url"],
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


@router.get("/mis-diagnosticos", response_model=List[DiagnosticoResponse])
async def obtener_mis_diagnosticos(
    current_user: dict = Depends(get_current_active_user),
) -> List[DiagnosticoResponse]:
    docs = diagnostico_service.historial(user_id=current_user["id"], limit=100)
    return [
        DiagnosticoResponse(
            id=doc["id"],
            user_id=doc["user_id"],
            resultado=doc["resultado"],
            confianza=doc["confianza"],
            clase_original=doc["clase_original"],
            estado=doc["estado"],
            imagen_original_url=doc["imagen_original_url"],
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


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obtener_diagnostico(
    diagnostico_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> DiagnosticoResponse:
    doc = diagnostico_service.detalle(user_id=current_user["id"], diagnostico_id=diagnostico_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    return DiagnosticoResponse(
        id=doc["id"],
        user_id=doc["user_id"],
        resultado=doc["resultado"],
        confianza=doc["confianza"],
        clase_original=doc["clase_original"],
        estado=doc["estado"],
        imagen_original_url=doc["imagen_original_url"],
        created_at=doc["created_at"],
    )
