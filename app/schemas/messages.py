from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DispatchMessageRequest(BaseModel):
    task_id: int
    recipient: str = Field(min_length=1)
    content: str = Field(min_length=1)


class SimulateReplyRequest(BaseModel):
    task_id: int
    reply: str = Field(min_length=1)


class MessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    sender_id: int
    recipient: str
    content: str
    direction: str
    status: str
    channel: str
    created_at: datetime
