import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import get_settings
from app.db.sql import init_sql_schema_if_enabled, verify_and_bootstrap_database

from app.routers.admin_appointments import router as admin_citas_router
from app.routers.admin_users import router as admin_users_router
from app.routers.auth import router as auth_router
from app.routers.diagnosis import router as diagnostico_router
from app.routers.doctor import router as doctor_router
from app.routers.patient import router as patient_router

from fastapi.security import OAuth2PasswordBearer

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=503, content={"detail": "Base de datos no disponible"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})

app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(admin_citas_router)
app.include_router(diagnostico_router)
app.include_router(doctor_router)
app.include_router(patient_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login/form")

@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

@app.on_event("startup")
def bootstrap_initial_admin() -> None:
    init_sql_schema_if_enabled()
    verify_and_bootstrap_database()

@app.get("/")
async def root() -> dict:
    return {"message": "Bienvenido a la API de AlzheCare CNN"}

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
