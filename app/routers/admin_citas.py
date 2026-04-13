from fastapi import APIRouter, Depends

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordinacion import AppointmentResponse, AppointmentUpdateStatusRequest
from app.services.coordinacion_service import coordinacion_service

router = APIRouter(prefix="/api/admin/citas", tags=["Admin Citas"])


@router.get("")
async def listar_citas_admin(
    estado: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
):
    return coordinacion_service.listar_citas_admin(estado=estado, skip=skip, limit=limit)


@router.patch("/{cita_id}/estado", response_model=AppointmentResponse)
async def actualizar_estado_cita_admin(
    cita_id: str,
    payload: AppointmentUpdateStatusRequest,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
):
    return coordinacion_service.actualizar_estado_cita_admin(cita_id, payload.status.value)
