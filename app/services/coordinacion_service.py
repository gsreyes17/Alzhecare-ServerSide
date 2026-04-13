from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_patient_repository import DoctorPatientRepository
from app.repositories.doctor_request_repository import DoctorRequestRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRole
from app.schemas.coordinacion import AppointmentStatus, NotificationType, RequestStatus
from app.services.diagnostico_service import diagnosis_service


class CoordinationService:
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
            "name": user["name"],
            "lastname": user["lastname"],
            "email": user["email"],
        }

    def _serialize_request(self, doc: dict) -> dict:
        doctor = self.user_repo.get_by_id(doc["doctor_user_id"])
        patient = self.user_repo.get_by_id(doc["patient_user_id"])
        return {
            "id": str(doc["_id"]),
            "doctor_user_id": doc["doctor_user_id"],
            "patient_user_id": doc["patient_user_id"],
            "doctor_name": (
                f"{doctor.get('name', '')} {doctor.get('lastname', '')}".strip() if doctor else None
            ),
            "patient_name": (
                f"{patient.get('name', '')} {patient.get('lastname', '')}".strip() if patient else None
            ),
            "status": doc["status"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _serialize_appointment(self, doc: dict) -> dict:
        payload = {
            "id": str(doc["_id"]),
            "doctor_user_id": doc["doctor_user_id"],
            "patient_user_id": doc["patient_user_id"],
            "title": doc.get("title") or "Cita medica",
            "date_time": doc["date_time"],
            "description": doc["description"],
            "status": doc["status"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

        doctor = self.user_repo.get_by_id(doc["doctor_user_id"])
        patient = self.user_repo.get_by_id(doc["patient_user_id"])
        if doctor:
            payload["doctor_name"] = f"{doctor.get('name', '')} {doctor.get('lastname', '')}".strip()
        if patient:
            payload["patient_name"] = f"{patient.get('name', '')} {patient.get('lastname', '')}".strip()
        return payload

    def _serialize_notification(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "type": doc["type"],
            "title": doc["title"],
            "message": doc["message"],
            "data": doc.get("data", {}),
            "read": doc.get("read", False),
            "created_at": doc["created_at"],
        }

    def search_patients(self, query_text: str) -> list[dict]:
        users = self.user_repo.search_patients(query_text)
        return [self._serialize_user(user) for user in users]

    def create_link_request(self, doctor_user_id: str, patient_user_id: str) -> dict:
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
                "status": RequestStatus.pending.value,
                "created_at": now,
                "updated_at": now,
            }
        )

        doctor = self.user_repo.get_by_id(doctor_user_id)
        doctor_name = doctor.get("name", "Doctor") if doctor else "Doctor"

        self.notification_repo.create(
            {
                "user_id": patient_user_id,
                "type": NotificationType.doctor_request.value,
                "title": "Nueva solicitud medica",
                "message": f"{doctor_name} solicita vincularse como tu doctor.",
                "data": {"request_id": str(created["_id"]), "doctor_user_id": doctor_user_id},
                "read": False,
                "created_at": now,
            }
        )
        return self._serialize_request(created)

    def list_doctor_requests(self, doctor_user_id: str) -> list[dict]:
        docs = self.request_repo.list_by_doctor(doctor_user_id)
        return [self._serialize_request(doc) for doc in docs]

    def list_doctor_patients(self, doctor_user_id: str) -> list[dict]:
        patient_ids = self.link_repo.list_patient_ids_by_doctor(doctor_user_id)
        users = self.user_repo.get_many_by_ids(patient_ids)
        return [self._serialize_user(user) for user in users]

    def _ensure_active_doctor_patient_link(self, doctor_user_id: str, patient_user_id: str) -> None:
        if not self.link_repo.exists_link(doctor_user_id, patient_user_id):
            raise HTTPException(status_code=403, detail="No tienes vínculo activo con este paciente")

    def get_patient_history_for_doctor(
        self,
        doctor_user_id: str,
        patient_user_id: str,
        limit: int = 100,
    ) -> list[dict]:
        self._ensure_active_doctor_patient_link(doctor_user_id, patient_user_id)
        return diagnosis_service.history(user_id=patient_user_id, limit=limit)

    async def analyze_for_patient(
        self,
        doctor_user_id: str,
        patient_user_id: str,
        file_content: bytes,
        filename: str | None,
    ):
        self._ensure_active_doctor_patient_link(doctor_user_id, patient_user_id)
        return await diagnosis_service.analyze(
            user_id=patient_user_id,
            file_content=file_content,
            filename=filename,
        )

    def create_appointment(
        self,
        doctor_user_id: str,
        patient_user_id: str,
        title: str,
        date_time,
        description: str,
    ) -> dict:
        self._ensure_active_doctor_patient_link(doctor_user_id, patient_user_id)

        now = datetime.now(timezone.utc)
        created = self.appointment_repo.create(
            {
                "doctor_user_id": doctor_user_id,
                "patient_user_id": patient_user_id,
                "title": title.strip(),
                "date_time": date_time,
                "description": description,
                "status": AppointmentStatus.scheduled.value,
                "created_at": now,
                "updated_at": now,
            }
        )

        doctor = self.user_repo.get_by_id(doctor_user_id)
        doctor_name = doctor.get("name", "Doctor") if doctor else "Doctor"

        self.notification_repo.create(
            {
                "user_id": patient_user_id,
                "type": NotificationType.scheduled_appointment.value,
                "title": title.strip(),
                "message": f"{doctor_name} programo la cita \"{title.strip()}\" para {date_time}.",
                "data": {
                    "appointment_id": str(created["_id"]),
                    "title": title.strip(),
                    "doctor_user_id": doctor_user_id,
                },
                "read": False,
                "created_at": now,
            }
        )
        return self._serialize_appointment(created)

    def list_doctor_appointments(self, doctor_user_id: str, status: str | None = None) -> list[dict]:
        docs = self.appointment_repo.list_by_doctor(doctor_user_id, status=status)
        return [self._serialize_appointment(doc) for doc in docs]

    def list_patient_appointments(self, patient_user_id: str, status: str | None = None) -> list[dict]:
        docs = self.appointment_repo.list_by_patient(patient_user_id, status=status)
        return [self._serialize_appointment(doc) for doc in docs]

    def update_doctor_appointment_status(self, doctor_user_id: str, appointment_id: str, status: str) -> dict:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment or appointment.get("doctor_user_id") != doctor_user_id:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        updated = self.appointment_repo.update_status(appointment_id, status, datetime.now(timezone.utc))
        if not updated:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        self.notification_repo.create(
            {
                "user_id": updated["patient_user_id"],
                "type": NotificationType.updated_appointment.value,
                "title": updated.get("title") or "Cita actualizada",
                "message": f"La cita \"{updated.get('title') or 'Cita medica'}\" cambio a estado: {status}.",
                "data": {
                    "appointment_id": str(updated["_id"]),
                    "title": updated.get("title") or "Cita medica",
                },
                "read": False,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return self._serialize_appointment(updated)

    def list_pending_patient_requests(self, patient_user_id: str) -> list[dict]:
        docs = self.request_repo.list_pending_by_patient(patient_user_id)
        return [self._serialize_request(doc) for doc in docs]

    def respond_patient_request(self, patient_user_id: str, request_id: str, action: str) -> dict:
        if action not in {"aceptar", "denegar"}:
            raise HTTPException(status_code=400, detail="Acción inválida")

        request_doc = self.request_repo.get_by_id_for_patient(request_id, patient_user_id)
        if not request_doc:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if request_doc.get("status") != RequestStatus.pending.value:
            raise HTTPException(status_code=400, detail="La solicitud ya fue procesada")

        now = datetime.now(timezone.utc)
        new_status = RequestStatus.accepted.value if action == "aceptar" else RequestStatus.denied.value
        updated = self.request_repo.update_status(request_id, new_status, now)
        if not updated:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if action == "aceptar" and not self.link_repo.exists_link(updated["doctor_user_id"], updated["patient_user_id"]):
            self.link_repo.create(
                {
                    "doctor_user_id": updated["doctor_user_id"],
                    "patient_user_id": updated["patient_user_id"],
                    "status": "activo",
                    "created_at": now,
                    "updated_at": now,
                }
            )

        self.notification_repo.create(
            {
                "user_id": updated["doctor_user_id"],
                "type": NotificationType.request_response.value,
                "title": "Respuesta de solicitud",
                "message": f"El paciente ha {action}do tu solicitud.",
                "data": {"request_id": str(updated["_id"]), "status": new_status},
                "read": False,
                "created_at": now,
            }
        )
        return self._serialize_request(updated)

    def list_user_notifications(self, user_id: str, unread_only: bool = False) -> list[dict]:
        docs = self.notification_repo.list_by_user(user_id, unread_only=unread_only)
        return [self._serialize_notification(doc) for doc in docs]

    def mark_notification_as_read(self, user_id: str, notification_id: str) -> bool:
        doc = self.notification_repo.get_by_id_for_user(notification_id, user_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")
        updated = self.notification_repo.mark_as_read(notification_id)
        return updated is not None

    def list_admin_appointments(self, status: str | None = None, skip: int = 0, limit: int = 100) -> dict:
        docs = self.appointment_repo.list_all(status=status, skip=skip, limit=limit)
        return {
            "appointments": [self._serialize_appointment(doc) for doc in docs],
            "total": self.appointment_repo.count_all(status=status),
        }

    def update_admin_appointment_status(self, appointment_id: str, status: str) -> dict:
        updated = self.appointment_repo.update_status(appointment_id, status, datetime.now(timezone.utc))
        if not updated:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        self.notification_repo.create(
            {
                "user_id": updated["patient_user_id"],
                "type": NotificationType.updated_appointment.value,
                "title": updated.get("title") or "Cita actualizada por administracion",
                "message": f"La cita \"{updated.get('title') or 'Cita medica'}\" cambio a estado: {status}.",
                "data": {
                    "appointment_id": str(updated["_id"]),
                    "title": updated.get("title") or "Cita medica",
                    "status": status,
                },
                "read": False,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return self._serialize_appointment(updated)


coordination_service = CoordinationService()
