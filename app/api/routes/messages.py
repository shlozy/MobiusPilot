from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Message, Project, Task, User
from app.schemas.messages import DispatchMessageRequest, MessagePublic, SimulateReplyRequest
from app.services.messaging_service import SimulatorMessagingService

router = APIRouter(prefix="/api/v1", tags=["messages"])


@router.post("/messages/dispatch", response_model=MessagePublic, status_code=status.HTTP_201_CREATED)
def dispatch_message(payload: DispatchMessageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Message:
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    message = SimulatorMessagingService.dispatch(db, payload.task_id, current_user.id, payload.recipient, payload.content)
    return message


@router.get("/messages", response_model=list[MessagePublic])
def list_messages(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Message]:
    org_ids = [m.organization_id for m in current_user.memberships]
    project_ids = [project.id for project in db.query(Project).filter(Project.organization_id.in_(org_ids)).all()] if org_ids else []
    if not project_ids:
        return []
    task_ids = [task.id for task in db.query(Task).filter(Task.project_id.in_(project_ids)).all()]
    return db.query(Message).filter(Message.task_id.in_(task_ids)).order_by(Message.created_at.desc()).all() if task_ids else []


@router.post("/messages/simulate-reply", response_model=MessagePublic, status_code=status.HTTP_201_CREATED)
def simulate_reply(payload: SimulateReplyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Message:
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return SimulatorMessagingService.simulate_reply(db, payload.task_id, current_user.id, payload.reply)


@router.get("/tasks/{task_id}/messages", response_model=list[MessagePublic])
def list_task_messages(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Message]:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return db.query(Message).filter(Message.task_id == task_id).order_by(Message.created_at.asc()).all()
