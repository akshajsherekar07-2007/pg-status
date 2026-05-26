"""
Hold Service — All hold business logic enforced server-side.
"""
import logging
from datetime import datetime, timedelta
from extensions import db, socketio
from models.bed import Bed
from models.hold import Hold
from models.user import User
from models.bed_status_log import BedStatusLog

logger = logging.getLogger(__name__)

VALID_HOLD_DAYS = {1, 2, 3, 5, 7}
MAX_ACTIVE_HOLDS = 3


def request_hold(student_id, bed_id, hold_days):
    """Student requests a hold on a green bed."""
    if hold_days not in VALID_HOLD_DAYS:
        return {'success': False,
                'error': 'Invalid hold duration. Choose 1, 2, 3, 5, or 7 days.', 'code': 400}

    student = User.query.get(student_id)
    if not student or student.role != 'student':
        return {'success': False, 'error': 'Invalid student account.', 'code': 403}

    bed = Bed.query.get(bed_id)
    if not bed:
        return {'success': False, 'error': 'Bed not found.', 'code': 404}

    if bed.status != 'green':
        return {'success': False,
                'error': 'This bed is not available for hold requests.', 'code': 409}

    # Check max active holds
    active_count = Hold.query.filter(
        Hold.student_id == student_id,
        Hold.status.in_(['pending', 'active'])
    ).count()
    if active_count >= MAX_ACTIVE_HOLDS:
        return {'success': False,
                'error': f'Maximum {MAX_ACTIVE_HOLDS} active holds allowed.', 'code': 429}

    # Check if student already has a hold on this bed
    existing = Hold.query.filter(
        Hold.bed_id == bed_id,
        Hold.student_id == student_id,
        Hold.status.in_(['pending', 'active'])
    ).first()
    if existing:
        return {'success': False,
                'error': 'You already have an active hold on this bed.', 'code': 409}

    # Check if another active/pending hold exists on this bed
    other_hold = Hold.query.filter(
        Hold.bed_id == bed_id,
        Hold.status.in_(['pending', 'active'])
    ).first()
    if other_hold:
        return {'success': False,
                'error': 'Another student already has a hold on this bed.', 'code': 409}

    # Get owner from bed -> room -> floor -> property
    room = bed.room
    floor = room.floor
    prop = floor.property
    owner_id = prop.owner_id

    hold = Hold(
        bed_id=bed_id,
        student_id=student_id,
        owner_id=owner_id,
        hold_days=hold_days,
        status='pending',
        requested_at=datetime.utcnow()
    )
    db.session.add(hold)
    db.session.commit()

    logger.info(
        f'Hold requested: student={student_id}, bed={bed_id}, days={hold_days}')

    # Notify owner via socket
    from services.notification_service import create_notification
    create_notification(
        user_id=owner_id,
        title='New Hold Request',
        message=f'{
            student.full_name} (Score: {
            student.reliability_score}) requested a {hold_days}-day hold on {
            bed.bed_label}, Room {
                room.room_number}',
        notif_type='new_hold_request',
        related_hold_id=hold.id
    )

    socketio.emit('new_hold_request', {
        'hold_id': hold.id,
        'student_name': student.full_name,
        'student_score': student.reliability_score,
        'bed_label': bed.bed_label,
        'room_number': room.room_number,
        'property_name': prop.name,
        'property_id': prop.id,
        'hold_days': hold_days,
        'requested_at': hold.requested_at.isoformat()
    }, room=f'user_{owner_id}')

    return {'success': True, 'data': hold.to_dict()}


def accept_hold(hold_id, owner_id):
    """Owner accepts a pending hold request."""
    hold = Hold.query.get(hold_id)
    if not hold:
        return {'success': False, 'error': 'Hold not found.', 'code': 404}

    if hold.owner_id != owner_id:
        return {'success': False, 'error': 'Unauthorized.', 'code': 403}

    if hold.status != 'pending':
        return {'success': False,
                'error': f'Cannot accept a hold with status: {hold.status}', 'code': 409}

    bed = hold.bed
    now = datetime.utcnow()

    # Update hold
    hold.status = 'active'
    hold.responded_at = now
    hold.expires_at = now + timedelta(days=hold.hold_days)

    # Update bed status
    old_status = bed.status
    bed.status = 'yellow'
    bed.last_status_change = now

    # Log status change
    log = BedStatusLog(
        bed_id=bed.id,
        old_status=old_status,
        new_status='yellow',
        changed_by=owner_id,
        action_type='hold_accepted'
    )
    db.session.add(log)
    db.session.commit()

    logger.info(f'Hold accepted: hold={hold_id}, bed={bed.id}')

    room = bed.room
    floor = room.floor
    prop = floor.property

    # Notify student
    from services.notification_service import create_notification
    create_notification(
        user_id=hold.student_id,
        title='Hold Accepted! 🎉',
        message=f'Your hold on {
            bed.bed_label}, Room {
            room.room_number} at {
            prop.name} has been accepted. Expires {
                hold.expires_at.strftime("%b %d, %Y %I:%M %p")}',
        notif_type='hold_accepted',
        related_hold_id=hold.id
    )

    socketio.emit('hold_accepted', {
        'hold_id': hold.id,
        'bed_id': bed.id,
        'bed_label': bed.bed_label,
        'property_name': prop.name,
        'property_id': prop.id,
        'expires_at': hold.expires_at.isoformat()
    }, room=f'user_{hold.student_id}')

    # Broadcast bed status change to property room
    socketio.emit('bed_status_changed', {
        'bed_id': bed.id,
        'new_status': 'yellow',
        'old_status': old_status,
        'bed_label': bed.bed_label,
        'room_number': room.room_number,
        'floor_number': floor.floor_number,
        'property_id': prop.id,
        'hold_expires_at': hold.expires_at.isoformat(),
        'student_name': hold.student.full_name
    }, room=f'property_{prop.id}')

    return {'success': True, 'data': hold.to_dict()}


def reject_hold(hold_id, owner_id, reason=''):
    """Owner rejects a pending hold request."""
    hold = Hold.query.get(hold_id)
    if not hold:
        return {'success': False, 'error': 'Hold not found.', 'code': 404}

    if hold.owner_id != owner_id:
        return {'success': False, 'error': 'Unauthorized.', 'code': 403}

    if hold.status != 'pending':
        return {'success': False,
                'error': f'Cannot reject a hold with status: {hold.status}', 'code': 409}

    hold.status = 'rejected'
    hold.responded_at = datetime.utcnow()
    hold.reject_reason = reason or 'No reason provided'
    db.session.commit()

    logger.info(f'Hold rejected: hold={hold_id}, reason={reason}')

    bed = hold.bed
    room = bed.room
    prop = room.floor.property

    from services.notification_service import create_notification
    create_notification(
        user_id=hold.student_id,
        title='Hold Rejected',
        message=f'Your hold request for {
            bed.bed_label}, Room {
            room.room_number} at {
            prop.name} was rejected. Reason: {
                hold.reject_reason}',
        notif_type='hold_rejected',
        related_hold_id=hold.id
    )

    socketio.emit('hold_rejected', {
        'hold_id': hold.id,
        'bed_id': bed.id,
        'bed_label': bed.bed_label,
        'property_name': prop.name,
        'reason': hold.reject_reason
    }, room=f'user_{hold.student_id}')

    return {'success': True, 'data': hold.to_dict()}


def cancel_hold(hold_id, student_id):
    """Student cancels their own hold."""
    hold = Hold.query.get(hold_id)
    if not hold:
        return {'success': False, 'error': 'Hold not found.', 'code': 404}

    if hold.student_id != student_id:
        return {'success': False, 'error': 'Unauthorized.', 'code': 403}

    if hold.status not in ('pending', 'active'):
        return {'success': False,
                'error': f'Cannot cancel a hold with status: {hold.status}', 'code': 409}

    bed = hold.bed
    room = bed.room
    prop = room.floor.property

    # Score adjustment
    from services.score_service import adjust_score_cancel
    adjust_score_cancel(hold)

    hold.status = 'cancelled_by_student'
    hold.responded_at = datetime.utcnow()

    # Revert bed status if it was yellow due to this hold
    if bed.status == 'yellow' and hold.status == 'cancelled_by_student':
        old_status = bed.status
        bed.status = 'green'
        bed.last_status_change = datetime.utcnow()

        log = BedStatusLog(
            bed_id=bed.id,
            old_status=old_status,
            new_status='green',
            changed_by=student_id,
            action_type='hold_cancelled'
        )
        db.session.add(log)

        socketio.emit('bed_status_changed', {
            'bed_id': bed.id,
            'new_status': 'green',
            'old_status': old_status,
            'bed_label': bed.bed_label,
            'room_number': room.room_number,
            'floor_number': room.floor.floor_number,
            'property_id': prop.id
        }, room=f'property_{prop.id}')

    db.session.commit()
    logger.info(f'Hold cancelled by student: hold={hold_id}')

    return {'success': True, 'data': hold.to_dict()}


def override_hold(hold_id, owner_id):
    """Owner overrides an active hold for immediate walk-in booking."""
    hold = Hold.query.get(hold_id)
    if not hold:
        return {'success': False, 'error': 'Hold not found.', 'code': 404}

    if hold.owner_id != owner_id:
        return {'success': False, 'error': 'Unauthorized.', 'code': 403}

    if hold.status != 'active':
        return {'success': False,
                'error': 'Can only override active holds.', 'code': 409}

    bed = hold.bed
    room = bed.room
    floor = room.floor
    prop = floor.property

    # Cancel the hold (no score penalty — not student's fault)
    hold.status = 'cancelled_by_override'
    hold.responded_at = datetime.utcnow()

    # Mark bed as red
    old_status = bed.status
    bed.status = 'red'
    bed.occupied_since = datetime.utcnow()
    bed.last_status_change = datetime.utcnow()

    log = BedStatusLog(
        bed_id=bed.id,
        old_status=old_status,
        new_status='red',
        changed_by=owner_id,
        action_type='immediate_override'
    )
    db.session.add(log)
    db.session.commit()

    logger.info(f'Hold overridden: hold={hold_id}, bed={bed.id}')

    # Urgent notification to student
    from services.notification_service import create_notification
    create_notification(
        user_id=hold.student_id,
        title='Room Taken — Hold Overridden',
        message=f'A walk-in student took {
            bed.bed_label}, Room {
            room.room_number} at {
            prop.name}. Your reliability score is NOT affected.',
        notif_type='room_taken',
        related_hold_id=hold.id
    )

    socketio.emit('room_taken_hold_override', {
        'hold_id': hold.id,
        'bed_id': bed.id,
        'bed_label': bed.bed_label,
        'property_name': prop.name,
        'property_id': prop.id
    }, room=f'user_{hold.student_id}')

    socketio.emit('bed_status_changed', {
        'bed_id': bed.id,
        'new_status': 'red',
        'old_status': old_status,
        'bed_label': bed.bed_label,
        'room_number': room.room_number,
        'floor_number': floor.floor_number,
        'property_id': prop.id
    }, room=f'property_{prop.id}')

    return {'success': True, 'data': hold.to_dict()}
