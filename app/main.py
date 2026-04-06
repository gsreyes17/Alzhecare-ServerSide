from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.admin_citas import router as admin_citas_router
from app.routers.admin_users import router as admin_users_router
from app.routers.auth import router as auth_router
from app.routers.diagnostico import router as diagnostico_router
from app.routers.doctor import router as doctor_router
from app.routers.patient import router as patient_router
from app.services.auth_service import auth_service

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(admin_citas_router)
app.include_router(diagnostico_router)
app.include_router(doctor_router)
app.include_router(patient_router)


@app.on_event("startup")
def bootstrap_initial_admin() -> None:
    auth_service.ensure_initial_admin()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
