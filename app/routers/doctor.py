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
from app.services.coordinacion_service import coordinacion_service

router = APIRouter(prefix="/api/doctor", tags=["Doctor"])


@router.get("/pacientes/buscar", response_model=list[BasicUserResponse])
async def buscar_pacientes(
    q: str,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.buscar_pacientes(q)


@router.post("/solicitudes", response_model=BindingResponse)
async def crear_solicitud_vinculacion(
    payload: BindingCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.crear_solicitud_vinculacion(
        doctor_user_id=current_user["id"],
        patient_user_id=payload.patient_user_id,
    )


@router.get("/solicitudes", response_model=list[BindingResponse])
async def listar_solicitudes(
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.listar_solicitudes_doctor(current_user["id"])


@router.get("/pacientes", response_model=list[BasicUserResponse])
async def listar_pacientes_asignados(
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.listar_pacientes_doctor(current_user["id"])


@router.get("/pacientes/{patient_user_id}/historial")
async def historial_paciente(
    patient_user_id: str,
    limit: int = 100,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return {
        "diagnosticos": coordinacion_service.historial_paciente_para_doctor(
            doctor_user_id=current_user["id"],
            patient_user_id=patient_user_id,
            limit=limit,
        )
    }


@router.post("/pacientes/{patient_user_id}/analizar", response_model=AnalysisResponse)
async def analizar_para_paciente(
    patient_user_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        created = await coordinacion_service.analizar_para_paciente(
            doctor_user_id=current_user["id"],
            patient_user_id=patient_user_id,
            file_content=contents,
            filename=file.filename,
        )
        return AnalysisResponse(
            id=created["id"],
            result=created["resultado"],
            confidence=created["confianza"],
            image_url=created["imagen_original_url"],
            created_at=created["created_at"],
        )
    finally:
        await file.close()


@router.post("/citas", response_model=AppointmentResponse)
async def crear_cita(
    payload: AppointmentCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.crear_cita(
        doctor_user_id=current_user["id"],
        patient_user_id=payload.patient_user_id,
        titulo=payload.title,
        fecha_hora=payload.date_time,
        descripcion=payload.description,
    )


@router.get("/citas", response_model=list[AppointmentResponse])
async def listar_citas_doctor(
    estado: str | None = None,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.listar_citas_doctor(current_user["id"], estado=estado)


@router.patch("/citas/{cita_id}/estado", response_model=AppointmentResponse)
async def actualizar_estado_cita(
    cita_id: str,
    payload: AppointmentUpdateStatusRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.actualizar_estado_cita_doctor(
        doctor_user_id=current_user["id"],
        cita_id=cita_id,
        estado=payload.status.value,
    )
