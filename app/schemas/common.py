from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TimestampedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(TimestampedModel):
    items: list
    total: int = Field(default=0)
    page: int = Field(default=1)
    page_size: int = Field(default=20)


class ErrorResponse(TimestampedModel):
    detail: str
    code: str | None = None


class HealthResponse(TimestampedModel):
    status: str
    app: str
    database: str
    messaging_platform: str
