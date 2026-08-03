from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import Notification


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    body: str,
    match_id: int | None = None,
) -> Notification | None:
    """Create a notification, skipping if one of the same type already exists for this match."""

    existing = db.query(Notification).filter_by(
        user_id=user_id, match_id=match_id, type=type,
    ).first()
    if existing is not None:
        return None

    notification = Notification(
        user_id=user_id, match_id=match_id, type=type, title=title, body=body,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(db: Session, user_id: int) -> list[Notification]:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
    ).order_by(Notification.created_at.desc()).limit(50).all()


def mark_read(db: Session, user_id: int, notification_id: int) -> bool:
    notification = db.query(Notification).filter_by(id=notification_id, user_id=user_id).first()
    if notification is None:
        return False
    notification.read_at = datetime.utcnow()
    db.commit()
    return True


def mark_all_read(db: Session, user_id: int) -> None:
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.read_at.is_(None),
    ).update({"read_at": datetime.utcnow()})
    db.commit()
