from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_patient_repository import DoctorPatientRepository
from app.repositories.doctor_request_repository import DoctorRequestRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRole
from app.schemas.coordinacion import AppointmentStatus, RequestStatus, NotificationType
from app.services.diagnostico_service import diagnostico_service


class CoordinacionService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.request_repo = DoctorRequestRepository()
        self.link_repo = DoctorPatientRepository()
        self.appointment_repo = AppointmentRepository()
        self.notification_repo = NotificationRepository()

    def _serialize_user(self, user: dict) -> dict:
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "nombre": user["nombre"],
            "apellido": user["apellido"],
            "email": user["email"],
        }

    def _serialize_request(self, doc: dict) -> dict:
        doctor = self.user_repo.get_by_id(doc["doctor_user_id"])
        patient = self.user_repo.get_by_id(doc["patient_user_id"])
        return {
            "id": str(doc["_id"]),
            "doctor_user_id": doc["doctor_user_id"],
            "patient_user_id": doc["patient_user_id"],
            "doctor_nombre": (
                f"{doctor.get('nombre', '')} {doctor.get('apellido', '')}".strip() if doctor else None
            ),
            "patient_nombre": (
                f"{patient.get('nombre', '')} {patient.get('apellido', '')}".strip() if patient else None
            ),
            "estado": doc["estado"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _serialize_cita(self, doc: dict) -> dict:
        payload = {
            "id": str(doc["_id"]),
            "doctor_user_id": doc["doctor_user_id"],
            "patient_user_id": doc["patient_user_id"],
            "titulo": doc.get("titulo") or "Cita medica",
            "fecha_hora": doc["fecha_hora"],
            "descripcion": doc["descripcion"],
            "estado": doc["estado"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

        doctor = self.user_repo.get_by_id(doc["doctor_user_id"])
        patient = self.user_repo.get_by_id(doc["patient_user_id"])
        if doctor:
            payload["doctor_nombre"] = f"{doctor.get('nombre', '')} {doctor.get('apellido', '')}".strip()
        if patient:
            payload["patient_nombre"] = f"{patient.get('nombre', '')} {patient.get('apellido', '')}".strip()
        return payload

    def _serialize_notification(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "tipo": doc["tipo"],
            "titulo": doc["titulo"],
            "mensaje": doc["mensaje"],
            "data": doc.get("data", {}),
            "leida": doc.get("leida", False),
            "created_at": doc["created_at"],
        }

    def buscar_pacientes(self, texto: str) -> list[dict]:
        users = self.user_repo.search_patients(texto)
        return [self._serialize_user(user) for user in users]

    def crear_solicitud_vinculacion(self, doctor_user_id: str, patient_user_id: str) -> dict:
        patient = self.user_repo.get_by_id(patient_user_id)
        if not patient or patient.get("role") != UserRole.patient.value:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        if self.link_repo.exists_link(doctor_user_id, patient_user_id):
            raise HTTPException(status_code=400, detail="El paciente ya está vinculado a este doctor")

        if self.request_repo.get_pending(doctor_user_id, patient_user_id):
            raise HTTPException(status_code=400, detail="Ya existe una solicitud pendiente para este paciente")

        now = datetime.now(timezone.utc)
        created = self.request_repo.create(
            {
                "doctor_user_id": doctor_user_id,
                "patient_user_id": patient_user_id,
                "estado": RequestStatus.pending.value,
                "created_at": now,
                "updated_at": now,
            }
        )

        doctor = self.user_repo.get_by_id(doctor_user_id)
        doctor_name = doctor.get("nombre", "Doctor") if doctor else "Doctor"

        self.notification_repo.create(
            {
                "user_id": patient_user_id,
                "tipo": NotificationType.doctor_request.value,
                "titulo": "Nueva solicitud médica",
                "mensaje": f"{doctor_name} solicita vincularse como tu doctor.",
                "data": {"request_id": str(created["_id"]), "doctor_user_id": doctor_user_id},
                "leida": False,
                "created_at": now,
            }
        )
        return self._serialize_request(created)

    def listar_solicitudes_doctor(self, doctor_user_id: str) -> list[dict]:
        docs = self.request_repo.list_by_doctor(doctor_user_id)
        return [self._serialize_request(doc) for doc in docs]

    def listar_pacientes_doctor(self, doctor_user_id: str) -> list[dict]:
        patient_ids = self.link_repo.list_patient_ids_by_doctor(doctor_user_id)
        users = self.user_repo.get_many_by_ids(patient_ids)
        return [self._serialize_user(user) for user in users]

    def _ensure_doctor_patient_link(self, doctor_user_id: str, patient_user_id: str) -> None:
        if not self.link_repo.exists_link(doctor_user_id, patient_user_id):
            raise HTTPException(status_code=403, detail="No tienes vínculo activo con este paciente")

    def historial_paciente_para_doctor(self, doctor_user_id: str, patient_user_id: str, limit: int = 100) -> list[dict]:
        self._ensure_doctor_patient_link(doctor_user_id, patient_user_id)
        return diagnostico_service.historial(user_id=patient_user_id, limit=limit)

    async def analizar_para_paciente(self, doctor_user_id: str, patient_user_id: str, file_content: bytes, filename: str | None):
        self._ensure_doctor_patient_link(doctor_user_id, patient_user_id)
        return await diagnostico_service.analizar(
            user_id=patient_user_id,
            file_content=file_content,
            filename=filename,
        )

    def crear_cita(self, doctor_user_id: str, patient_user_id: str, titulo: str, fecha_hora, descripcion: str) -> dict:
        self._ensure_doctor_patient_link(doctor_user_id, patient_user_id)

        now = datetime.now(timezone.utc)
        created = self.appointment_repo.create(
            {
                "doctor_user_id": doctor_user_id,
                "patient_user_id": patient_user_id,
                "titulo": titulo.strip(),
                "fecha_hora": fecha_hora,
                "descripcion": descripcion,
                "estado": AppointmentStatus.scheduled.value,
                "created_at": now,
                "updated_at": now,
            }
        )

        doctor = self.user_repo.get_by_id(doctor_user_id)
        doctor_name = doctor.get("nombre", "Doctor") if doctor else "Doctor"

        self.notification_repo.create(
            {
                "user_id": patient_user_id,
                "tipo": NotificationType.scheduled_appointment.value,
                "titulo": titulo.strip(),
                "mensaje": f"{doctor_name} programo la cita \"{titulo.strip()}\" para {fecha_hora}.",
                "data": {
                    "cita_id": str(created["_id"]),
                    "titulo": titulo.strip(),
                    "doctor_user_id": doctor_user_id,
                },
                "leida": False,
                "created_at": now,
            }
        )
        return self._serialize_cita(created)

    def listar_citas_doctor(self, doctor_user_id: str, estado: str | None = None) -> list[dict]:
        docs = self.appointment_repo.list_by_doctor(doctor_user_id, estado=estado)
        return [self._serialize_cita(doc) for doc in docs]

    def listar_citas_paciente(self, patient_user_id: str, estado: str | None = None) -> list[dict]:
        docs = self.appointment_repo.list_by_patient(patient_user_id, estado=estado)
        return [self._serialize_cita(doc) for doc in docs]

    def actualizar_estado_cita_doctor(self, doctor_user_id: str, cita_id: str, estado: str) -> dict:
        cita = self.appointment_repo.get_by_id(cita_id)
        if not cita or cita.get("doctor_user_id") != doctor_user_id:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        updated = self.appointment_repo.update_estado(cita_id, estado, datetime.now(timezone.utc))
        if not updated:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        self.notification_repo.create(
            {
                "user_id": updated["patient_user_id"],
                "tipo": NotificationType.updated_appointment.value,
                "titulo": updated.get("titulo") or "Cita actualizada",
                "mensaje": f"La cita \"{updated.get('titulo') or 'Cita medica'}\" cambio a estado: {estado}.",
                "data": {
                    "cita_id": str(updated["_id"]),
                    "titulo": updated.get("titulo") or "Cita medica",
                },
                "leida": False,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return self._serialize_cita(updated)

    def listar_solicitudes_pendientes_paciente(self, patient_user_id: str) -> list[dict]:
        docs = self.request_repo.list_pending_by_patient(patient_user_id)
        return [self._serialize_request(doc) for doc in docs]

    def responder_solicitud_paciente(self, patient_user_id: str, request_id: str, accion: str) -> dict:
        if accion not in {"aceptar", "denegar"}:
            raise HTTPException(status_code=400, detail="Acción inválida")

        request_doc = self.request_repo.get_by_id_for_patient(request_id, patient_user_id)
        if not request_doc:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if request_doc.get("estado") != RequestStatus.pending.value:
            raise HTTPException(status_code=400, detail="La solicitud ya fue procesada")

        now = datetime.now(timezone.utc)
        nuevo_estado = RequestStatus.accepted.value if accion == "aceptar" else RequestStatus.denied.value
        updated = self.request_repo.update_status(request_id, nuevo_estado, now)
        if not updated:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if accion == "aceptar" and not self.link_repo.exists_link(updated["doctor_user_id"], updated["patient_user_id"]):
            self.link_repo.create(
                {
                    "doctor_user_id": updated["doctor_user_id"],
                    "patient_user_id": updated["patient_user_id"],
                    "estado": "activo",
                    "created_at": now,
                    "updated_at": now,
                }
            )

        self.notification_repo.create(
            {
                "user_id": updated["doctor_user_id"],
                "tipo": NotificationType.request_response.value,
                "titulo": "Respuesta de solicitud",
                "mensaje": f"El paciente ha {accion}do tu solicitud.",
                "data": {"request_id": str(updated["_id"]), "estado": nuevo_estado},
                "leida": False,
                "created_at": now,
            }
        )
        return self._serialize_request(updated)

    def listar_notificaciones_usuario(self, user_id: str, solo_no_leidas: bool = False) -> list[dict]:
        docs = self.notification_repo.list_by_user(user_id, solo_no_leidas=solo_no_leidas)
        return [self._serialize_notification(doc) for doc in docs]

    def marcar_notificacion_leida(self, user_id: str, notification_id: str) -> bool:
        doc = self.notification_repo.get_by_id_for_user(notification_id, user_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")
        updated = self.notification_repo.mark_as_read(notification_id)
        return updated is not None

    def listar_citas_admin(self, estado: str | None = None, skip: int = 0, limit: int = 100) -> dict:
        docs = self.appointment_repo.list_all(estado=estado, skip=skip, limit=limit)
        return {
            "citas": [self._serialize_cita(doc) for doc in docs],
            "total": self.appointment_repo.count_all(estado=estado),
        }

    def actualizar_estado_cita_admin(self, cita_id: str, estado: str) -> dict:
        updated = self.appointment_repo.update_estado(cita_id, estado, datetime.now(timezone.utc))
        if not updated:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        self.notification_repo.create(
            {
                "user_id": updated["patient_user_id"],
                "tipo": NotificationType.updated_appointment.value,
                "titulo": updated.get("titulo") or "Cita actualizada por administracion",
                "mensaje": f"La cita \"{updated.get('titulo') or 'Cita medica'}\" cambio a estado: {estado}.",
                "data": {
                    "cita_id": str(updated["_id"]),
                    "titulo": updated.get("titulo") or "Cita medica",
                    "estado": estado,
                },
                "leida": False,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return self._serialize_cita(updated)


coordinacion_service = CoordinacionService()
