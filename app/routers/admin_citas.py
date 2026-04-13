from fastapi import APIRouter, Depends

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordinacion import AppointmentResponse, AppointmentUpdateStatusRequest
from app.services.coordinacion_service import coordination_service

router = APIRouter(prefix="/api/admin/citas", tags=["Admin Citas"])


@router.get("")
async def list_admin_appointments(
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
):
    return coordination_service.list_admin_appointments(status=status, skip=skip, limit=limit)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_admin_appointment_status(
    appointment_id: str,
    payload: AppointmentUpdateStatusRequest,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
):
    return coordination_service.update_admin_appointment_status(appointment_id, payload.status.value)
