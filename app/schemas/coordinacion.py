from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EstadoSolicitud(str, Enum):
    pendiente = "pendiente"
    aceptada = "aceptada"
    denegada = "denegada"


class EstadoCita(str, Enum):
    programada = "programada"
    efectuada = "efectuada"
    cancelada = "cancelada"


class TipoNotificacion(str, Enum):
    solicitud_medico = "solicitud_medico"
    respuesta_solicitud = "respuesta_solicitud"
    cita_programada = "cita_programada"
    cita_actualizada = "cita_actualizada"


class UsuarioBasicoResponse(BaseModel):
    id: str
    username: str
    nombre: str
    apellido: str
    email: str


class SolicitudVinculacionCreateRequest(BaseModel):
    patient_user_id: str


class SolicitudVinculacionResponderRequest(BaseModel):
    accion: str = Field(description="aceptar o denegar")


class SolicitudVinculacionResponse(BaseModel):
    id: str
    doctor_user_id: str
    patient_user_id: str
    doctor_nombre: str | None = None
    patient_nombre: str | None = None
    estado: EstadoSolicitud
    created_at: datetime
    updated_at: datetime


class CitaCreateRequest(BaseModel):
    patient_user_id: str
    titulo: str = Field(min_length=1, max_length=120)
    fecha_hora: datetime
    descripcion: str = Field(min_length=1, max_length=500)


class CitaUpdateEstadoRequest(BaseModel):
    estado: EstadoCita


class CitaResponse(BaseModel):
    id: str
    doctor_user_id: str
    patient_user_id: str
    titulo: str
    fecha_hora: datetime
    descripcion: str
    estado: EstadoCita
    created_at: datetime
    updated_at: datetime
    doctor_nombre: str | None = None
    patient_nombre: str | None = None


class NotificacionResponse(BaseModel):
    id: str
    user_id: str
    tipo: TipoNotificacion
    titulo: str
    mensaje: str
    data: dict = Field(default_factory=dict)
    leida: bool
    created_at: datetime


class NotificacionMarcarLeidaResponse(BaseModel):
    ok: bool
