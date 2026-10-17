from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ActivityLog, Project, Task, User

router = APIRouter(prefix="/api/v1", tags=["activity"])


@router.get("/activity")
def list_activity(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    org_ids = [membership.organization_id for membership in current_user.memberships]
    project_ids = [project.id for project in db.query(Project).filter(Project.organization_id.in_(org_ids)).all()] if org_ids else []
    task_ids = [task.id for task in db.query(Task).filter(Task.project_id.in_(project_ids)).all()] if project_ids else []
    items = db.query(ActivityLog).filter(ActivityLog.task_id.in_(task_ids)).order_by(ActivityLog.created_at.desc()).all() if task_ids else []
    return {"items": [{"id": item.id, "task_id": item.task_id, "action": item.action, "details": item.details, "created_at": item.created_at.isoformat()} for item in items], "total": len(items), "page": 1, "page_size": 20}
