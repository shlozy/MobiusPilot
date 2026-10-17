from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import OrganizationMembership, ProjectMember, User

router = APIRouter(prefix="/api/v1", tags=["members"])


@router.get("/members")
def list_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    org_ids = [membership.organization_id for membership in current_user.memberships]
    if not org_ids:
        return {"items": [], "total": 0, "page": 1, "page_size": 20}
    rows = []
    for member in db.query(OrganizationMembership).filter(OrganizationMembership.organization_id.in_(org_ids)).all():
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            rows.append({
                "id": member.id,
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": member.role,
                "organization_id": member.organization_id,
            })
    return {"items": rows, "total": len(rows), "page": 1, "page_size": 20}


@router.post("/members", status_code=status.HTTP_201_CREATED)
def create_member(email: str, role: str = "member", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    org_ids = [membership.organization_id for membership in current_user.memberships]
    if not org_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of any organization.")
    primary_org = org_ids[0]
    existing = db.query(OrganizationMembership).filter(OrganizationMembership.organization_id == primary_org, OrganizationMembership.user_id == user.id).first()
    if existing:
        return {"id": existing.id, "user_id": user.id, "email": user.email, "full_name": user.full_name, "role": existing.role}
    membership = OrganizationMembership(organization_id=primary_org, user_id=user.id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return {"id": membership.id, "user_id": user.id, "email": user.email, "full_name": user.full_name, "role": membership.role}


@router.patch("/members/{member_id}")
def update_member(member_id: int, role: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership = db.query(OrganizationMembership).filter(OrganizationMembership.id == member_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    if not any(m.organization_id == membership.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if role is not None:
        membership.role = role
    db.commit()
    user = db.query(User).filter(User.id == membership.user_id).first()
    return {"id": membership.id, "user_id": user.id, "email": user.email, "full_name": user.full_name, "role": membership.role}
