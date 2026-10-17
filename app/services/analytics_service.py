from sqlalchemy.orm import Session

from app.db.models import Organization, OrganizationMembership, Project, ProjectMember, Task, User


def build_overview(db: Session, user_id: int) -> dict:
    project_ids = [project.id for project in db.query(Project).join(Organization).join(OrganizationMembership).filter(OrganizationMembership.user_id == user_id).all()]
    tasks = db.query(Task).filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    return {
        "project_count": len(project_ids),
        "task_count": len(tasks),
        "active_tasks": sum(1 for task in tasks if task.status in {"pending", "in_progress", "blocked"}),
        "completed_tasks": sum(1 for task in tasks if task.status == "completed"),
        "blocked_tasks": sum(1 for task in tasks if task.status == "blocked"),
        "messages_sent": 0,
        "workload": [],
    }


def build_workload(db: Session, user_id: int) -> list[dict]:
    members = db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
    items = []
    for member in members:
        tasks = db.query(Task).filter(Task.project_id == member.project_id, Task.assignee_id == member.user_id).all()
        items.append({
            "member_id": member.user_id,
            "project_id": member.project_id,
            "domain": member.domain,
            "assigned_tasks": len(tasks),
            "availability": member.availability,
        })
    return items


def build_project_metrics(db: Session, user_id: int) -> list[dict]:
    project_ids = [project.id for project in db.query(Project).join(Organization).join(OrganizationMembership).filter(OrganizationMembership.user_id == user_id).all()]
    if not project_ids:
        return []
    rows = []
    for project in db.query(Project).filter(Project.id.in_(project_ids)).all():
        tasks = db.query(Task).filter(Task.project_id == project.id).all()
        rows.append({
            "project_id": project.id,
            "project_name": project.name,
            "task_count": len(tasks),
            "completed": sum(1 for task in tasks if task.status == "completed"),
            "in_progress": sum(1 for task in tasks if task.status == "in_progress"),
        })
    return rows
