from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.analytics import OverviewResponse, WorkloadResponse
from app.services.analytics_service import build_overview, build_project_metrics, build_workload

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview")
def overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return build_overview(db, current_user.id)


@router.get("/workload")
def workload(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {"items": build_workload(db, current_user.id)}


@router.get("/projects")
def projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {"items": build_project_metrics(db, current_user.id)}
