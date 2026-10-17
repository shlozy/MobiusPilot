from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import AIExecution, Project, Task, User
from app.schemas.ai import AIPlanRequest, AIPlanResponse, AIReplyInterpretation, AIReplyInterpretationRequest
from app.services.ai_service import generate_task_plan

router = APIRouter(prefix="/api/v1", tags=["ai"])


@router.post("/ai/plan", response_model=AIPlanResponse)
def plan_goal(payload: AIPlanRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project = None
    if payload.project_id is not None:
        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        if not any(m.organization_id == project.organization_id for m in current_user.memberships):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    plan = generate_task_plan(db, payload.goal, payload.project_id, payload.context)
    db.add(AIExecution(goal=payload.goal, model="openai/gpt-oss-120b", status="completed", payload=str(plan)))
    db.commit()
    return plan


@router.post("/ai/assignments/preview")
def preview_assignments(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    task_candidates = db.query(Task).filter(Task.project_id == project_id).all()
    suggestions = []
    for task in task_candidates:
        from app.services.assignment_service import rank_member_candidates

        suggestions.append({"task_id": task.id, "title": task.title, "candidates": rank_member_candidates(db, task)})
    return {"project_id": project_id, "suggestions": suggestions}


@router.post("/ai/dispatch")
def dispatch_plan() -> dict:
    return {"status": "approval_required", "message": "The plan is generated and ready for coordinator approval before task dispatch."}


@router.post("/ai/replies/interpret", response_model=AIReplyInterpretation)
def interpret_reply(payload: AIReplyInterpretationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if not any(m.organization_id == (db.query(Project).filter(Project.id == task.project_id).first().organization_id) for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    reply = payload.reply.lower()
    status = "pending"
    if "done" in reply or "finished" in reply or "completed" in reply:
        status = "completed"
    elif "blocked" in reply or "waiting on" in reply or "need" in reply and "credentials" in reply:
        status = "blocked"
    elif "started" in reply or "in progress" in reply:
        status = "in_progress"
    elif "cancel" in reply:
        status = "cancelled"

    evidence = ["Message text was parsed."]
    if "tests" in reply:
        evidence.append("Test mention detected in reply.")
    if "credentials" in reply:
        evidence.append("Dependency blocker mention detected.")

    require_confirmation = status in {"completed", "blocked"}
    return {
        "intent": "status_update",
        "proposed_status": status,
        "progress_summary": payload.reply,
        "blocker_details": "Missing credentials or dependency risk." if "credentials" in reply else None,
        "eta": "2d" if "two hours" in reply or "another two hours" in reply else None,
        "confidence": 0.82 if status != "pending" else 0.46,
        "evidence": evidence,
        "require_coordinator_confirmation": require_confirmation,
    }
