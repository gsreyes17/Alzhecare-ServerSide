from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordinacion import (
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentUpdateStatusRequest,
    BindingCreateRequest,
    BindingResponse,
    BasicUserResponse,
)
from app.schemas.diagnostico import AnalysisResponse
from app.services.coordinacion_service import coordination_service

router = APIRouter(prefix="/api/doctor", tags=["Doctor"])


@router.get("/patients/search", response_model=list[BasicUserResponse])
async def search_patients(
    q: str,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.search_patients(q)


@router.post("/requests", response_model=BindingResponse)
async def create_link_request(
    payload: BindingCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.create_link_request(
        doctor_user_id=current_user["id"],
        patient_user_id=payload.patient_user_id,
    )


@router.get("/requests", response_model=list[BindingResponse])
async def list_requests(
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.list_doctor_requests(current_user["id"])


@router.get("/patients", response_model=list[BasicUserResponse])
async def list_assigned_patients(
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.list_doctor_patients(current_user["id"])


@router.get("/patients/{patient_user_id}/history")
async def get_patient_history(
    patient_user_id: str,
    limit: int = 100,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return {
        "diagnoses": coordination_service.get_patient_history_for_doctor(
            doctor_user_id=current_user["id"],
            patient_user_id=patient_user_id,
            limit=limit,
        )
    }


@router.post("/patients/{patient_user_id}/analyze", response_model=AnalysisResponse)
async def analyze_for_patient(
    patient_user_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        created = await coordination_service.analyze_for_patient(
            doctor_user_id=current_user["id"],
            patient_user_id=patient_user_id,
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


@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    payload: AppointmentCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.create_appointment(
        doctor_user_id=current_user["id"],
        patient_user_id=payload.patient_user_id,
        title=payload.title,
        date_time=payload.date_time,
        description=payload.description,
    )


@router.get("/appointments", response_model=list[AppointmentResponse])
async def list_doctor_appointments(
    status: str | None = None,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.list_doctor_appointments(current_user["id"], status=status)


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: str,
    payload: AppointmentUpdateStatusRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordination_service.update_doctor_appointment_status(
        doctor_user_id=current_user["id"],
        appointment_id=appointment_id,
        status=payload.status.value,
    )
