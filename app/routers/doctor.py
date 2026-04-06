from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordinacion import (
    CitaCreateRequest,
    CitaResponse,
    CitaUpdateEstadoRequest,
    SolicitudVinculacionCreateRequest,
    SolicitudVinculacionResponse,
    UsuarioBasicoResponse,
)
from app.schemas.diagnostico import AnalisisResponse
from app.services.coordinacion_service import coordinacion_service

router = APIRouter(prefix="/api/doctor", tags=["Doctor"])


@router.get("/pacientes/buscar", response_model=list[UsuarioBasicoResponse])
async def buscar_pacientes(
    q: str,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.buscar_pacientes(q)


@router.post("/solicitudes", response_model=SolicitudVinculacionResponse)
async def crear_solicitud_vinculacion(
    payload: SolicitudVinculacionCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.crear_solicitud_vinculacion(
        doctor_user_id=current_user["id"],
        patient_user_id=payload.patient_user_id,
    )


@router.get("/solicitudes", response_model=list[SolicitudVinculacionResponse])
async def listar_solicitudes(
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.listar_solicitudes_doctor(current_user["id"])


@router.get("/pacientes", response_model=list[UsuarioBasicoResponse])
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


@router.post("/pacientes/{patient_user_id}/analizar", response_model=AnalisisResponse)
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


@router.post("/citas", response_model=CitaResponse)
async def crear_cita(
    payload: CitaCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.crear_cita(
        doctor_user_id=current_user["id"],
        patient_user_id=payload.patient_user_id,
        titulo=payload.titulo,
        fecha_hora=payload.fecha_hora,
        descripcion=payload.descripcion,
    )


@router.get("/citas", response_model=list[CitaResponse])
async def listar_citas_doctor(
    estado: str | None = None,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.listar_citas_doctor(current_user["id"], estado=estado)


@router.patch("/citas/{cita_id}/estado", response_model=CitaResponse)
async def actualizar_estado_cita(
    cita_id: str,
    payload: CitaUpdateEstadoRequest,
    current_user: dict = Depends(require_roles(UserRole.doctor.value)),
):
    return coordinacion_service.actualizar_estado_cita_doctor(
        doctor_user_id=current_user["id"],
        cita_id=cita_id,
        estado=payload.estado.value,
    )
