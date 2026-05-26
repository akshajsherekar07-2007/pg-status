"""
Status Service — Enforces valid bed status transitions.
"""
import logging
from datetime import datetime
from extensions import db, socketio
from models.bed import Bed
from models.bed_status_log import BedStatusLog

logger = logging.getLogger(__name__)

# Valid transitions: (old_status, new_status)
VALID_TRANSITIONS = {
    ('green', 'yellow'),   # Via accepted hold
    ('green', 'red'),      # Owner manual after offline payment
    ('yellow', 'red'),     # Owner manual (cancels hold, notifies student)
    ('yellow', 'green'),   # Hold expired / cancelled / rejected
    ('red', 'green'),      # Owner marks tenant moved out
}

# BLOCKED: ('red', 'yellow') — must go red→green→yellow


def change_bed_status(bed_id, new_status, changed_by, action_type='manual'):
    """Change bed status with transition validation."""
    bed = Bed.query.get(bed_id)
    if not bed:
        return {'success': False, 'error': 'Bed not found.', 'code': 404}

    old_status = bed.status
    if old_status == new_status:
        return {'success': False,
                'error': 'Bed is already in this status.', 'code': 409}

    if (old_status, new_status) not in VALID_TRANSITIONS:
        return {
            'success': False,
            'error': f'Invalid transition: {old_status} → {new_status}. '
            f'{"Must go Red → Green first." if old_status == "red" and new_status == "yellow" else ""}',
            'code': 400
        }

    # If moving to red, set occupied_since
    if new_status == 'red':
        bed.occupied_since = datetime.utcnow()
    elif new_status == 'green':
        bed.occupied_since = None

    bed.status = new_status
    bed.last_status_change = datetime.utcnow()

    log = BedStatusLog(
        bed_id=bed.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        action_type=action_type
    )
    db.session.add(log)

    # If yellow → red, cancel any active holds
    if old_status == 'yellow' and new_status == 'red':
        from models.hold import Hold
        active_holds = Hold.query.filter_by(
            bed_id=bed_id, status='active').all()
        for hold in active_holds:
            hold.status = 'cancelled_by_override'
            hold.responded_at = datetime.utcnow()

            from services.notification_service import create_notification
            create_notification(
                user_id=hold.student_id,
                title='Room Taken',
                message=f'{
                    bed.bed_label}, Room {
                    bed.room.room_number} has been booked. Your score is not affected.',
                notif_type='room_taken',
                related_hold_id=hold.id
            )
            socketio.emit('room_taken_hold_override', {
                'hold_id': hold.id,
                'bed_id': bed.id,
                'bed_label': bed.bed_label,
                'property_name': bed.room.floor.property.name,
                'property_id': bed.room.floor.property.id
            }, room=f'user_{hold.student_id}')

    db.session.commit()

    room = bed.room
    floor = room.floor
    prop = floor.property

    logger.info(
        f'Bed status changed: bed={bed_id}, {old_status}→{new_status}, by={changed_by}, action={action_type}')

    # Broadcast to property room
    socketio.emit('bed_status_changed', {
        'bed_id': bed.id,
        'new_status': new_status,
        'old_status': old_status,
        'bed_label': bed.bed_label,
        'room_number': room.room_number,
        'floor_number': floor.floor_number,
        'property_id': prop.id
    }, room=f'property_{prop.id}')

    return {'success': True, 'data': bed.to_dict()}
