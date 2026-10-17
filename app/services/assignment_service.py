from sqlalchemy.orm import Session

from app.db.models import ProjectMember, Task


def rank_member_candidates(db: Session, task: Task) -> list[dict]:
    candidates = db.query(ProjectMember).filter(ProjectMember.project_id == task.project_id).all()
    results: list[dict] = []

    for member in candidates:
        score = 0
        domain_match = task.domain.lower() == member.domain.lower()
        if domain_match:
            score += 50
        elif member.domain.lower() in task.domain.lower() or task.domain.lower() in member.domain.lower():
            score += 25

        current_work = db.query(Task).filter(Task.project_id == task.project_id, Task.assignee_id == member.user_id, Task.status != "completed").count()
        score -= current_work * 10

        if member.availability == "busy":
            score -= 40
        elif member.availability == "available":
            score += 10

        results.append({
            "member_id": member.user_id,
            "domain": member.domain,
            "availability": member.availability,
            "score": score,
            "reason": (
                "strong domain match" if domain_match else "adjacent domain match"
                if member.domain.lower() in task.domain.lower() or task.domain.lower() in member.domain.lower() else "fallback candidate"
            ),
            "active_tasks": current_work,
        })

    return sorted(results, key=lambda item: item["score"], reverse=True)
