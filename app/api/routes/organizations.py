from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Organization, OrganizationMembership, User
from app.schemas.organizations import OrganizationCreateRequest, OrganizationMemberPublic, OrganizationPublic

router = APIRouter(prefix="/api/v1", tags=["organizations"])


@router.get("/organizations")
def list_organizations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    org_ids = [membership.organization_id for membership in current_user.memberships]
    if not org_ids:
        return {"items": [], "total": 0, "page": 1, "page_size": 20}
    items = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    return {"items": [OrganizationPublic.model_validate(item).model_dump() for item in items], "total": len(items), "page": 1, "page_size": 20}


@router.post("/organizations", response_model=OrganizationPublic, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Organization:
    org = Organization(name=payload.name, description=payload.description, owner_id=current_user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMembership(organization_id=org.id, user_id=current_user.id, role="admin"))
    db.commit()
    db.refresh(org)
    return org


@router.get("/organizations/{organization_id}", response_model=OrganizationPublic)
def get_organization(organization_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    if not any(m.organization_id == organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return org


@router.get("/organizations/{organization_id}/members", response_model=list[OrganizationMemberPublic])
def list_organization_members(organization_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    if not any(m.organization_id == organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    memberships = db.query(OrganizationMembership).filter(OrganizationMembership.organization_id == organization_id).all()
    rows = []
    for m in memberships:
        user = db.query(User).filter(User.id == m.user_id).first()
        rows.append({
            "id": m.id,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": m.role,
        })
    return rows
