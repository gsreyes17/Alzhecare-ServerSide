from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    LoginRequest,
    RegisterRequest,
    Token,
    UserDocument,
    UserRole,
    UserProfileUpdateRequest,
)
from app.services.s3_service import s3_service


class AuthService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()

    def _serialize_user(self, user: dict) -> dict:
        serialized = user.copy()
        serialized["id"] = str(serialized.pop("_id"))
        serialized.setdefault("role", UserRole.patient.value)
        profile_key = serialized.pop("profile_image_key", None)
        if profile_key:
            serialized["profile_image_url"] = s3_service.sign_get_url(profile_key)
        else:
            serialized["profile_image_url"] = None
        return serialized

    def get_user_profile(self, user_id: str) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self._serialize_user(user)

    def register(self, payload: RegisterRequest) -> dict:
        if self.user_repo.get_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está registrado",
            )

        if self.user_repo.get_by_email(str(payload.email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        now = datetime.now(timezone.utc)
        user_doc = UserDocument(
            username=payload.username,
            password_hash=get_password_hash(payload.password),
            name=payload.name,
            lastname=payload.lastname,
            email=payload.email,
            role=UserRole.patient,
            status=True,
            created_at=now,
            updated_at=now,
        )

        return self.user_repo.create(user_doc.model_dump(mode="json"))

    def create_user(self, payload: AdminCreateUserRequest) -> dict:
        if self.user_repo.get_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está registrado",
            )

        if self.user_repo.get_by_email(str(payload.email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        now = datetime.now(timezone.utc)
        user_doc = UserDocument(
            username=payload.username,
            password_hash=get_password_hash(payload.password),
            name=payload.name,
            lastname=payload.lastname,
            email=payload.email,
            role=payload.role,
            status=True,
            created_at=now,
            updated_at=now,
        )

        return self.user_repo.create(user_doc.model_dump(mode="json"))

    def list_users(self, role: str | None = None, status: bool | None = None, skip: int = 0, limit: int = 50) -> dict:
        users = self.user_repo.list_users(role=role, status=status, skip=skip, limit=limit)
        return {
            "users": [self._serialize_user(user) for user in users],
            "total": self.user_repo.count_users(role=role, status=status),
        }

    def update_user(self, user_id: str, payload: AdminUpdateUserRequest) -> dict:
        update_data = payload.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        if "role" in update_data and update_data["role"] is not None:
            update_data["role"] = update_data["role"].value

        if update_data.get("role") == UserRole.patient.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Desde gestion administrativa solo se permiten roles doctor o admin",
            )

        if not update_data:
            current = self.user_repo.get_by_id(user_id)
            if not current:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
            return self._serialize_user(current)

        update_data["updated_at"] = datetime.now(timezone.utc)

        updated = self.user_repo.update_by_id(user_id, update_data)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self._serialize_user(updated)

    def update_current_user(self, user_id: str, payload: UserProfileUpdateRequest) -> dict:
        current_user = self.user_repo.get_by_id(user_id)
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        update_data = payload.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] is not None:
            existing_email = self.user_repo.get_by_email(str(update_data["email"]))
            if existing_email and str(existing_email["_id"]) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado",
                )

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        if not update_data:
            return self._serialize_user(current_user)

        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = self.user_repo.update_by_id(user_id, update_data)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self._serialize_user(updated)

    def update_current_user_profile_photo(
        self,
        user_id: str,
        image_content: bytes,
        filename: str,
    ) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        optimized = s3_service.optimize_profile_image(image_content)
        key = s3_service.upload_image(
            data=optimized,
            filename=filename,
            content_type="image/jpeg",
            folder=s3_service.profile_base_path,
        )

        updated = self.user_repo.update_by_id(
            user_id,
            {
                "profile_image_key": key,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self._serialize_user(updated)

    def ensure_initial_admin(self) -> None:
        if self.user_repo.get_by_role(UserRole.admin.value):
            return

        settings = get_settings()
        initial_admin_name = settings.initial_admin_name or settings.initial_admin_nombre
        initial_admin_lastname = settings.initial_admin_lastname or settings.initial_admin_apellido
        required_values = [
            settings.initial_admin_username,
            settings.initial_admin_password,
            initial_admin_name,
            initial_admin_lastname,
            settings.initial_admin_email,
        ]
        if not all(required_values):
            return

        payload = AdminCreateUserRequest(
            username=settings.initial_admin_username,
            password=settings.initial_admin_password,
            name=initial_admin_name,
            lastname=initial_admin_lastname,
            email=settings.initial_admin_email,
            role=UserRole.admin,
        )
        self.create_user(payload)

    def login(self, payload: LoginRequest) -> Token:
        user = self.user_repo.get_by_username(payload.username)
        if not user or not verify_password(payload.password, user.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.get("status", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        token = create_access_token(
            {
                "sub": str(user["_id"]),
                "username": user["username"],
                "role": user.get("role", UserRole.patient.value),
            }
        )
        return Token(access_token=token)


auth_service = AuthService()
