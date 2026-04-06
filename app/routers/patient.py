from fastapi import APIRouter, Depends

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordinacion import (
    CitaResponse,
    NotificacionMarcarLeidaResponse,
    NotificacionResponse,
    SolicitudVinculacionResponderRequest,
    SolicitudVinculacionResponse,
)
from app.services.coordinacion_service import coordinacion_service

router = APIRouter(prefix="/api/patient", tags=["Patient"])


@router.get("/solicitudes", response_model=list[SolicitudVinculacionResponse])
async def listar_solicitudes_pendientes(
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordinacion_service.listar_solicitudes_pendientes_paciente(current_user["id"])


@router.patch("/solicitudes/{request_id}", response_model=SolicitudVinculacionResponse)
async def responder_solicitud(
    request_id: str,
    payload: SolicitudVinculacionResponderRequest,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordinacion_service.responder_solicitud_paciente(
        patient_user_id=current_user["id"],
        request_id=request_id,
        accion=payload.accion,
    )


@router.get("/notificaciones", response_model=list[NotificacionResponse])
async def listar_notificaciones(
    solo_no_leidas: bool = False,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordinacion_service.listar_notificaciones_usuario(
        user_id=current_user["id"],
        solo_no_leidas=solo_no_leidas,
    )


@router.patch("/notificaciones/{notification_id}/leida", response_model=NotificacionMarcarLeidaResponse)
async def marcar_notificacion_leida(
    notification_id: str,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    ok = coordinacion_service.marcar_notificacion_leida(current_user["id"], notification_id)
    return NotificacionMarcarLeidaResponse(ok=ok)


@router.get("/citas", response_model=list[CitaResponse])
async def listar_citas_paciente(
    estado: str | None = None,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordinacion_service.listar_citas_paciente(current_user["id"], estado=estado)
