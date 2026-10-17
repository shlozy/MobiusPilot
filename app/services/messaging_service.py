from sqlalchemy.orm import Session

from app.db.models import ActivityLog, Message, Task


class SimulatorMessagingService:
    @staticmethod
    def dispatch(db: Session, task_id: int, sender_id: int, recipient: str, content: str, channel: str = "simulator") -> Message:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        message = Message(
            task_id=task_id,
            sender_id=sender_id,
            recipient=recipient,
            content=content,
            direction="outgoing",
            status="delivered",
            channel=channel,
        )
        db.add(message)
        db.flush()
        db.add(ActivityLog(task_id=task_id, actor_id=sender_id, action="message_sent", details={"recipient": recipient, "content": content}))
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def simulate_reply(db: Session, task_id: int, sender_id: int, raw_reply: str) -> Message:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        message = Message(
            task_id=task_id,
            sender_id=sender_id,
            recipient="coordinator",
            content=raw_reply,
            direction="incoming",
            status="received",
            channel="simulator",
        )
        db.add(message)
        db.flush()
        db.add(ActivityLog(task_id=task_id, actor_id=sender_id, action="reply_received", details={"content": raw_reply}))
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def list_for_task(db: Session, task_id: int) -> list[Message]:
        return db.query(Message).filter(Message.task_id == task_id).order_by(Message.created_at.asc()).all()
