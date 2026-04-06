from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/form")


def get_current_active_user(token: str = Depends(oauth2_scheme)) -> dict:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = UserRepository().get_by_id(user_id)
    if not user:
        raise credentials_exception

    if not user.get("estado", True):
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    user["id"] = str(user.pop("_id"))
    user.setdefault("role", UserRole.patient.value)
    return user


def require_roles(*allowed_roles: str):
    def dependency(current_user: dict = Depends(get_current_active_user)) -> dict:
        role = current_user.get("role", UserRole.patient.value)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta accion",
            )
        return current_user

    return dependency
