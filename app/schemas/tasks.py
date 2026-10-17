from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    project_id: int
    title: str = Field(min_length=2)
    description: str = Field(min_length=4)
    domain: str = "General"
    priority: str = "medium"
    estimated_effort: str = "1d"
    dependencies: list[int] | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    domain: str | None = None
    priority: str | None = None
    status: str | None = None
    estimated_effort: str | None = None


class TaskAssignRequest(BaseModel):
    member_id: int


class TaskStatusRequest(BaseModel):
    status: str
    note: str | None = None


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str
    domain: str
    priority: str
    status: str
    estimated_effort: str
    dependencies: str | None
    assignee_id: int | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime
