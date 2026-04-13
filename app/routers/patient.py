from fastapi import APIRouter, Depends

from app.dependencies import require_roles
from app.schemas.auth import UserRole
from app.schemas.coordinacion import (
    AppointmentResponse,
    NotificationMarkAsReadResponse,
    NotificationResponse,
    BindingResponderRequest,
    BindingResponse,
)
from app.services.coordinacion_service import coordination_service

router = APIRouter(prefix="/api/patient", tags=["Patient"])


@router.get("/requests", response_model=list[BindingResponse])
async def list_pending_requests(
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordination_service.list_pending_patient_requests(current_user["id"])


@router.patch("/requests/{request_id}", response_model=BindingResponse)
async def respond_request(
    request_id: str,
    payload: BindingResponderRequest,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordination_service.respond_patient_request(
        patient_user_id=current_user["id"],
        request_id=request_id,
        action=payload.action,
    )


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordination_service.list_user_notifications(
        user_id=current_user["id"],
        unread_only=unread_only,
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationMarkAsReadResponse)
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    ok = coordination_service.mark_notification_as_read(current_user["id"], notification_id)
    return NotificationMarkAsReadResponse(ok=ok)


@router.get("/appointments", response_model=list[AppointmentResponse])
async def list_patient_appointments(
    status: str | None = None,
    current_user: dict = Depends(require_roles(UserRole.patient.value)),
):
    return coordination_service.list_patient_appointments(current_user["id"], status=status)
