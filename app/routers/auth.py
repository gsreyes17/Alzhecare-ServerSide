from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import get_current_active_user
from app.schemas.auth import (
    LoginRequest,
    ProfilePhotoUploadResponse,
    RegisterRequest,
    Token,
    UserProfileUpdateRequest,
    UserResponse,
    UserRole,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> UserResponse:
    user = auth_service.register(payload)
    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        nombre=user["nombre"],
        apellido=user["apellido"],
        email=user["email"],
        role=user.get("role", UserRole.patient.value),
        estado=user["estado"],
        profile_image_url=None,
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest) -> Token:
    return auth_service.login(payload)


@router.post("/login/form", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    payload = LoginRequest(username=form_data.username, password=form_data.password)
    return auth_service.login(payload)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_active_user)) -> UserResponse:
    user = auth_service.get_user_profile(current_user["id"])
    return UserResponse(**user)


@router.patch("/me", response_model=UserResponse)
async def update_users_me(
    payload: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_active_user),
) -> UserResponse:
    user = auth_service.update_current_user(current_user["id"], payload)
    return UserResponse(**user)


@router.post("/me/photo", response_model=ProfilePhotoUploadResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
) -> ProfilePhotoUploadResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        updated_user = auth_service.update_current_user_profile_photo(
            user_id=current_user["id"],
            image_content=raw,
            filename=file.filename or "profile.jpg",
        )
        profile_image_url = updated_user.get("profile_image_url")
        if not profile_image_url:
            raise HTTPException(status_code=500, detail="No se pudo generar URL de perfil")
        return ProfilePhotoUploadResponse(profile_image_url=profile_image_url)
    finally:
        await file.close()
