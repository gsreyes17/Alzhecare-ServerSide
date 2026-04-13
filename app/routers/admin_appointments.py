from fastapi import APIRouter, Depends, Query

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordination import AppointmentResponse, AppointmentUpdateStatusRequest
from app.services.coordination_service import coordination_service

router = APIRouter(prefix="/api/admin/citas", tags=["Admin Citas"])


@router.get("")
async def list_admin_appointments(
    status: str | None = Query(default=None, pattern="^(programada|realizada|cancelada)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
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
