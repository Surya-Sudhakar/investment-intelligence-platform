from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    service: str
    version: str
    timestamp: datetime
    application: Literal["initialized"]
    database: Literal["connected"]
