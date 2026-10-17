from pydantic import BaseModel, ConfigDict


class OverviewResponse(BaseModel):
    project_count: int
    task_count: int
    active_tasks: int
    completed_tasks: int
    blocked_tasks: int
    messages_sent: int
    workload: list[dict]


class WorkloadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[dict]
