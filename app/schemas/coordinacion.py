from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RequestStatus(str, Enum):
    pending = "pendiente"
    accepted = "aceptada"
    denied = "denegada"


class AppointmentStatus(str, Enum):
    scheduled = "programada"
    done = "realizada"
    canceled = "cancelada"


class NotificationType(str, Enum):  
    doctor_request = "solicitud_medico"
    request_response = "respuesta_solicitud"
    scheduled_appointment = "cita_programada"
    updated_appointment = "cita_actualizada"


class BasicUserResponse(BaseModel):
    id: str
    username: str
    name: str
    lastname: str
    email: str


class BindingCreateRequest(BaseModel):
    patient_user_id: str


class BindingResponderRequest(BaseModel):
    action: str = Field(description="aceptar o denegar")


class BindingResponse(BaseModel):
    id: str
    doctor_user_id: str
    patient_user_id: str
    doctor_name: str | None = None
    patient_name: str | None = None
    status: RequestStatus
    created_at: datetime
    updated_at: datetime


class AppointmentCreateRequest(BaseModel):
    patient_user_id: str
    title: str = Field(min_length=1, max_length=120)
    date_time: datetime
    description: str = Field(min_length=1, max_length=500)


class AppointmentUpdateStatusRequest(BaseModel):
    status: AppointmentStatus


class AppointmentResponse(BaseModel):
    id: str
    doctor_user_id: str
    patient_user_id: str
    title: str
    date_time: datetime
    description: str
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime
    doctor_name: str | None = None
    patient_name: str | None = None


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: dict = Field(default_factory=dict)
    read: bool
    created_at: datetime


class NotificationMarkAsReadResponse(BaseModel):
    ok: bool
