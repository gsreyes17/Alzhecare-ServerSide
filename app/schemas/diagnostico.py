from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    id: str
    result: str
    confidence: float
    image_url: str
    created_at: datetime


class DiagnosisResponse(AnalysisResponse):
    user_id: str
    status: str


class DiagnosisDocument(BaseModel):
    user_id: str
    result: str
    confidence: float
    status: str = "completado"
    image_s3_key: str
    image_url: str
    model_output: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
