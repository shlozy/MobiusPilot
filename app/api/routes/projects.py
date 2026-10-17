from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import OrganizationMembership, Project, ProjectMember, User
from app.schemas.projects import ProjectCreateRequest, ProjectMemberPublic, ProjectMemberRequest, ProjectPublic, ProjectUpdateRequest

router = APIRouter(prefix="/api/v1", tags=["projects"])


@router.get("/projects")
def list_projects(organization_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    org_ids = [membership.organization_id for membership in current_user.memberships]
    if not org_ids:
        return {"items": [], "total": 0, "page": 1, "page_size": 20}
    query = db.query(Project).filter(Project.organization_id.in_(org_ids))
    if organization_id is not None:
        query = query.filter(Project.organization_id == organization_id)
    items = query.order_by(Project.created_at.desc()).all()
    return {"items": [ProjectPublic.model_validate(item).model_dump() for item in items], "total": len(items), "page": 1, "page_size": 20}


@router.post("/projects", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Project:
    has_access = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == payload.organization_id,
        OrganizationMembership.user_id == current_user.id,
    ).first()
    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this organization.")
    project = Project(name=payload.name, description=payload.description, organization_id=payload.organization_id, created_by=current_user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role="lead", domain="Product", availability="available"))
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectPublic)
def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectPublic)
def patch_project(project_id: int, payload: ProjectUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}/members")
def list_project_members(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    rows = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        rows.append({
            "id": member.id,
            "project_id": project_id,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": member.role,
            "domain": member.domain,
            "availability": member.availability,
        })
    return {"items": rows, "total": len(rows), "page": 1, "page_size": 20}


@router.post("/projects/{project_id}/members", status_code=status.HTTP_201_CREATED)
def add_project_member(project_id: int, payload: ProjectMemberRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if not any(m.organization_id == project.organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    member = ProjectMember(project_id=project_id, user_id=payload.user_id, role=payload.role, domain=payload.domain, availability="available")
    db.add(member)
    db.commit()
    db.refresh(member)
    return {
        "id": member.id,
        "project_id": project_id,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": member.role,
        "domain": member.domain,
        "availability": member.availability,
    }
