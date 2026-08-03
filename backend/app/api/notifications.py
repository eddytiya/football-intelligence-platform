from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.session import get_db
from app.models.user import User
from app.services.notifications.notification_service import (
    list_notifications,
    mark_all_read,
    mark_read,
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


def notification_payload(notification):
    return {
        "id": notification.id,
        "type": notification.type,
        "match_id": notification.match_id,
        "title": notification.title,
        "body": notification.body,
        "created_at": notification.created_at,
        "read_at": notification.read_at,
    }


@router.get("")
def get_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [notification_payload(item) for item in list_notifications(db, user.id)]


@router.post("/{notification_id}/read")
def read_notification(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not mark_read(db, user.id, notification_id):
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"message": "Notification marked as read."}


@router.post("/read-all")
def read_all_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    mark_all_read(db, user.id)
    return {"message": "All notifications marked as read."}
