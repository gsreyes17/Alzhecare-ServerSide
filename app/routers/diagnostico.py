from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_current_active_user
from app.schemas.diagnostico import AnalysisResponse, DiagnosisResponse
from app.services.diagnostico_service import diagnosis_service

router = APIRouter(prefix="/api/diagnoses", tags=["Diagnoses"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
) -> AnalysisResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        created = await diagnosis_service.analyze(
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


@router.get("/history", response_model=Dict[str, Any])
async def get_diagnosis_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
) -> Dict[str, Any]:
    docs = diagnosis_service.history(user_id=current_user["id"], limit=limit)
    return {"diagnoses": docs, "total": len(docs)}


@router.get("/my-diagnoses", response_model=List[DiagnosisResponse])
async def get_my_diagnoses(
    current_user: dict = Depends(get_current_active_user),
) -> List[DiagnosisResponse]:
    docs = diagnosis_service.history(user_id=current_user["id"], limit=100)
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


@router.get("/detail/{diagnosis_id}", response_model=Dict[str, Any])
async def get_diagnosis_detail(
    diagnosis_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Dict[str, Any]:
    doc = diagnosis_service.detail(user_id=current_user["id"], diagnosis_id=diagnosis_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    return doc


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(
    diagnosis_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> DiagnosisResponse:
    doc = diagnosis_service.detail(user_id=current_user["id"], diagnosis_id=diagnosis_id)
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
