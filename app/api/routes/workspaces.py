from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Organization, OrganizationMembership, User

router = APIRouter(prefix="/api/v1", tags=["workspaces"])


@router.get("/workspaces")
def list_workspaces(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    memberships = db.query(OrganizationMembership).filter(OrganizationMembership.user_id == current_user.id).all()
    org_ids = [membership.organization_id for membership in memberships]
    if not org_ids:
        return []
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    return [{"id": org.id, "name": org.name, "description": org.description, "owner_id": org.owner_id} for org in orgs]


@router.post("/workspaces")
def create_workspace(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    org = Organization(name=name, description="Workspace", owner_id=current_user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMembership(organization_id=org.id, user_id=current_user.id, role="admin"))
    db.commit()
    db.refresh(org)
    return {"id": org.id, "name": org.name}
