from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=128)
    nombre: str = Field(min_length=1, max_length=80)
    apellido: str = Field(min_length=1, max_length=80)
    email: EmailStr


class AdminCreateUserRequest(RegisterRequest):
    role: UserRole = Field(description="Rol del nuevo usuario")

    @field_validator("role")
    @classmethod
    def role_must_be_doctor_or_admin(cls, value: UserRole) -> UserRole:
        if value not in {UserRole.doctor, UserRole.admin}:
            raise ValueError("Solo se pueden crear usuarios doctor o admin")
        return value


class AdminUpdateUserRequest(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=80)
    apellido: Optional[str] = Field(default=None, min_length=1, max_length=80)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    estado: Optional[bool] = None
    role: Optional[UserRole] = None


class UserProfileUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=80)
    apellido: Optional[str] = Field(default=None, min_length=1, max_length=80)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    nombre: str
    apellido: str
    email: EmailStr
    role: UserRole
    estado: bool
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UsersListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class UserDocument(BaseModel):
    username: str
    password_hash: str
    nombre: str
    apellido: str
    email: EmailStr
    role: UserRole = UserRole.patient
    estado: bool = True
    created_at: datetime
    updated_at: datetime


class TokenData(BaseModel):
    sub: Optional[str] = None


class ProfilePhotoUploadResponse(BaseModel):
    profile_image_url: str
