from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ActivityLog, Project, Task, User
from app.schemas.tasks import TaskAssignRequest, TaskCreateRequest, TaskPublic, TaskStatusRequest, TaskUpdateRequest

router = APIRouter(prefix="/api/v1", tags=["tasks"])

VALID_TASK_STATUSES = {"pending", "in_progress", "blocked", "completed", "cancelled"}


@router.get("/tasks")
def list_tasks(project_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    org_ids = [membership.organization_id for membership in current_user.memberships]
    project_ids = [project.id for project in db.query(Project).filter(Project.organization_id.in_(org_ids)).all()] if org_ids else []
    query = db.query(Task).filter(Task.project_id.in_(project_ids)) if project_ids else db.query(Task).filter(Task.id == -1)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    items = query.order_by(Task.created_at.desc()).all()
    return {"items": [TaskPublic.model_validate(item).model_dump() for item in items], "total": len(items), "page": 1, "page_size": 20}


@router.post("/tasks", response_model=TaskPublic, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    task = Task(
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        domain=payload.domain,
        priority=payload.priority,
        estimated_effort=payload.estimated_effort,
        dependencies=",".join(str(dep) for dep in (payload.dependencies or [])),
        created_by_id=current_user.id,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return task


@router.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(task_id: int, payload: TaskUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name == "status" and value not in VALID_TASK_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task status.")
        setattr(task, field_name, value)
    db.add(ActivityLog(task_id=task.id, actor_id=current_user.id, action="task_updated", details=payload.model_dump(exclude_unset=True)))
    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks/{task_id}/assign", response_model=TaskPublic)
def assign_task(task_id: int, payload: TaskAssignRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    task.assignee_id = payload.member_id
    db.add(ActivityLog(task_id=task.id, actor_id=current_user.id, action="task_assigned", details={"member_id": payload.member_id}))
    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks/{task_id}/status", response_model=TaskPublic)
def update_task_status(task_id: int, payload: TaskStatusRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if payload.status not in VALID_TASK_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status.")
    task.status = payload.status
    db.add(ActivityLog(task_id=task.id, actor_id=current_user.id, action="status_changed", details={"status": payload.status, "note": payload.note}))
    db.commit()
    db.refresh(task)
    return task
