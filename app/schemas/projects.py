from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    description: str | None = None
    organization_id: int


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectMemberRequest(BaseModel):
    user_id: int
    role: str = "member"
    domain: str = "General"


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    description: str | None
    created_by: int
    created_at: datetime


class ProjectMemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    email: str
    full_name: str
    role: str
    domain: str
    availability: str
