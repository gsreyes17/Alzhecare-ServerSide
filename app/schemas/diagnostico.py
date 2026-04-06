from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AnalisisResponse(BaseModel):
    id: str
    resultado: str
    confianza: float
    clase_original: str
    imagen_original_url: str
    created_at: datetime


class DiagnosticoResponse(AnalisisResponse):
    user_id: str
    estado: str


class DiagnosticoDocument(BaseModel):
    user_id: str
    resultado: str
    confianza: float
    clase_original: str
    estado: str = "completado"
    imagen_original_s3_key: str
    imagen_original_url: str
    datos_roboflow: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
