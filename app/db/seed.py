from sqlalchemy.orm import Session

from app.db.models import Organization, OrganizationMembership, Project, ProjectMember, Task, User
from app.core.security import get_password_hash


def seed_demo_data(db: Session) -> None:
    from app.core.config import get_settings

    if get_settings().app_env == "test":
        return

    demo_email = "admin@kurukshetra.local"
    existing_user = db.query(User).filter(User.email == demo_email).first()
    if existing_user is None:
        demo_user = User(
            email=demo_email,
            full_name="Demo Coordinator",
            password_hash=get_password_hash("DemoPass!123"),
            is_active=True,
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        existing_user = demo_user

    existing_org = db.query(Organization).filter(Organization.name == "Demo Workspace").first()
    if existing_org is None:
        org = Organization(name="Demo Workspace", description="Default demo workspace", owner_id=existing_user.id)
        db.add(org)
        db.commit()
        db.refresh(org)
        existing_org = org

    existing_membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == existing_org.id,
        OrganizationMembership.user_id == existing_user.id,
    ).first()
    if existing_membership is None:
        db.add(OrganizationMembership(organization_id=existing_org.id, user_id=existing_user.id, role="admin"))

    if db.query(Project).filter(Project.name == "Launch Sprint").count() == 0:
        project = Project(name="Launch Sprint", description="Demo project", organization_id=existing_org.id, created_by=existing_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)

        for user_email, domain, role in [
            ("frontend@kurukshetra.local", "Frontend", "member"),
            ("backend@kurukshetra.local", "Backend", "member"),
            ("product@kurukshetra.local", "Product", "member"),
        ]:
            user = db.query(User).filter(User.email == user_email).first()
            if user is None:
                user = User(
                    email=user_email,
                    full_name=user_email.split("@")[0].title(),
                    password_hash=get_password_hash("DemoPass!123"),
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            if not db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id).first():
                db.add(ProjectMember(project_id=project.id, user_id=user.id, role=role, domain=domain, availability="available"))

        if db.query(Task).filter(Task.title == "Set up authentication flow").count() == 0:
            db.add(
                Task(
                    project_id=project.id,
                    title="Set up authentication flow",
                    description="Build secure login and session handling for the first release.",
                    domain="Backend",
                    priority="high",
                    status="pending",
                    estimated_effort="2d",
                    created_by_id=existing_user.id,
                    assignee_id=db.query(User).filter(User.email == "backend@kurukshetra.local").first().id,
                )
            )
            db.add(
                Task(
                    project_id=project.id,
                    title="Design the login experience",
                    description="Create the login interface content and responsiveness for launch.",
                    domain="Frontend",
                    priority="high",
                    status="pending",
                    estimated_effort="1d",
                    created_by_id=existing_user.id,
                    assignee_id=db.query(User).filter(User.email == "frontend@kurukshetra.local").first().id,
                )
            )
    db.commit()
