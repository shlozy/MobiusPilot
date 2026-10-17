from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    description: str | None = None


class OrganizationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    owner_id: int
    created_at: datetime


class OrganizationMemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    full_name: str
    role: str
