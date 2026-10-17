from pydantic import BaseModel, ConfigDict, Field


class AIPlanRequest(BaseModel):
    goal: str = Field(min_length=8)
    project_id: int | None = None
    context: str | None = None


class AIPlanTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str
    domain: str
    priority: str
    estimated_effort: str
    acceptance_criteria: list[str]
    dependencies: list[int] = []
    suggested_role: str
    rationale: str | None = None


class AIPlanResponse(BaseModel):
    goal: str
    tasks: list[AIPlanTask]
    source: str = "fallback"
    rationale: str | None = None


class AIAssignmentPreviewRequest(BaseModel):
    task_id: int | None = None
    project_id: int | None = None


class AIReplyInterpretationRequest(BaseModel):
    task_id: int
    reply: str = Field(min_length=1)


class AIReplyInterpretation(BaseModel):
    intent: str
    proposed_status: str
    progress_summary: str
    blocker_details: str | None = None
    eta: str | None = None
    confidence: float
    evidence: list[str]
    require_coordinator_confirmation: bool = True
