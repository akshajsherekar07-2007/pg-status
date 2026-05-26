"""
Notification Service — Creates DB records and emits socket events.
"""
import logging
from datetime import datetime
from extensions import db, socketio
from models.notification import Notification

logger = logging.getLogger(__name__)


def create_notification(user_id, title, message,
                        notif_type, related_hold_id=None):
    """Create a notification record and emit to user's socket room."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notif_type=notif_type,
        related_hold_id=related_hold_id,
        created_at=datetime.utcnow()
    )
    db.session.add(notif)
    db.session.commit()

    logger.info(f'Notification created: type={notif_type}, user={user_id}')

    # Emit notification via socket
    socketio.emit('notification', notif.to_dict(), room=f'user_{user_id}')

    return notif


def get_unread_count(user_id):
    """Get count of unread notifications."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def get_notifications(user_id, limit=20, offset=0):
    """Get paginated notifications for a user."""
    notifications = Notification.query.filter_by(user_id=user_id)\
        .order_by(Notification.created_at.desc())\
        .offset(offset).limit(limit).all()
    return [n.to_dict() for n in notifications]


def mark_read(notification_id, user_id):
    """Mark a single notification as read."""
    notif = Notification.query.get(notification_id)
    if not notif or notif.user_id != user_id:
        return False
    notif.is_read = True
    db.session.commit()
    return True


def mark_all_read(user_id):
    """Mark all notifications as read for a user."""
    Notification.query.filter_by(user_id=user_id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return True
