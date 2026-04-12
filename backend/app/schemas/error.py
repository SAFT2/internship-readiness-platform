from typing import Any

from pydantic import BaseModel


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorEnvelope
