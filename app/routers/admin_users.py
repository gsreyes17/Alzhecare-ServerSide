from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import require_roles
from app.schemas.auth import AdminCreateUserRequest, AdminUpdateUserRequest, UserResponse, UsersListResponse, UserRole
from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/admin/users", tags=["User Administration"])


@router.get("", response_model=UsersListResponse)
async def list_users(
    role: UserRole | None = Query(default=None),
    status: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
) -> Dict[str, Any]:
    return auth_service.list_users(role=role.value if role else None, status=status, skip=skip, limit=limit)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminCreateUserRequest,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
) -> UserResponse:
    user = auth_service.create_user(payload)
    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        name=user["name"],
        lastname=user["lastname"],
        email=user["email"],
        role=user.get("role", UserRole.patient.value),
        status=user["status"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
) -> UserResponse:
    user = auth_service.user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user["id"] = str(user.pop("_id"))
    return UserResponse(
        id=user["id"],
        username=user["username"],
        name=user["name"],
        lastname=user["lastname"],
        email=user["email"],
        role=user.get("role", UserRole.patient.value),
        status=user["status"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: AdminUpdateUserRequest,
    current_user: dict = Depends(require_roles(UserRole.admin.value)),
) -> UserResponse:
    user = auth_service.update_user(user_id, payload)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        name=user["name"],
        lastname=user["lastname"],
        email=user["email"],
        role=user.get("role", UserRole.patient.value),
        status=user["status"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )