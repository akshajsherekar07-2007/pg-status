"""
Scheduler Service — Hold expiry and auto-accept jobs (runs every 5 minutes).
"""
import logging
from datetime import datetime, timedelta
from extensions import db, socketio

logger = logging.getLogger(__name__)


def check_expired_holds(app):
    """Check and expire holds past their expiry time."""
    with app.app_context():
        from models.hold import Hold
        from models.bed_status_log import BedStatusLog
        from services.score_service import adjust_score_expire
        from services.notification_service import create_notification

        now = datetime.utcnow()

        # Expire active holds
        expired_holds = Hold.query.filter(
            Hold.status == 'active',
            Hold.expires_at < now
        ).all()

        for hold in expired_holds:
            hold.status = 'expired'
            bed = hold.bed
            room = bed.room
            floor = room.floor
            prop = floor.property

            # Check if any other active holds on this bed
            other_active = Hold.query.filter(
                Hold.bed_id == bed.id,
                Hold.status == 'active',
                Hold.id != hold.id
            ).first()

            if not other_active and bed.status == 'yellow':
                old_status = bed.status
                bed.status = 'green'
                bed.last_status_change = now
                log_entry = BedStatusLog(
                    bed_id=bed.id,
                    old_status=old_status,
                    new_status='green',
                    changed_by=None,
                    action_type='hold_expired'
                )
                db.session.add(log_entry)

                socketio.emit('bed_status_changed', {
                    'bed_id': bed.id,
                    'new_status': 'green',
                    'old_status': old_status,
                    'bed_label': bed.bed_label,
                    'room_number': room.room_number,
                    'floor_number': floor.floor_number,
                    'property_id': prop.id
                }, room=f'property_{prop.id}')

            # Score penalty
            adjust_score_expire(hold.student)

            # Notification
            create_notification(
                user_id=hold.student_id,
                title='Hold Expired',
                message=f'Your hold on {
                    bed.bed_label}, Room {
                    room.room_number} at {
                    prop.name} has expired. -5 reliability score.',
                notif_type='hold_expired',
                related_hold_id=hold.id
            )

            socketio.emit('hold_expired', {
                'hold_id': hold.id,
                'property_name': prop.name,
                'property_id': prop.id,
                'score_change': -5
            }, room=f'user_{hold.student_id}')

            logger.info(
                f'Hold expired: hold={
                    hold.id}, student={
                    hold.student_id}')

        # Auto-accept pending holds older than 24 hours
        auto_accept_cutoff = now - timedelta(hours=24)
        pending_holds = Hold.query.filter(
            Hold.status == 'pending',
            Hold.requested_at < auto_accept_cutoff
        ).all()

        for hold in pending_holds:
            from services.hold_service import accept_hold
            result = accept_hold(hold.id, hold.owner_id)
            if result['success']:
                logger.info(f'Hold auto-accepted: hold={hold.id}')

        # Check holds expiring soon (within 6 hours)
        expiring_soon = Hold.query.filter(
            Hold.status == 'active',
            Hold.expires_at > now,
            Hold.expires_at < now + timedelta(hours=6)
        ).all()

        for hold in expiring_soon:
            hours_remaining = (hold.expires_at - now).total_seconds() / 3600
            bed = hold.bed
            prop = bed.room.floor.property

            socketio.emit('hold_expiring_soon', {
                'hold_id': hold.id,
                'hours_remaining': round(hours_remaining, 1),
                'property_name': prop.name
            }, room=f'user_{hold.student_id}')

        db.session.commit()
        logger.info(
            f'Scheduler run: {
                len(expired_holds)} expired, {
                len(pending_holds)} auto-accepted, {
                len(expiring_soon)} expiring soon')


def init_scheduler(scheduler, app):
    """Initialize the APScheduler with hold expiry job."""
    scheduler.add_job(
        func=check_expired_holds,
        trigger='interval',
        minutes=5,
        args=[app],
        id='check_expired_holds',
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    logger.info('Scheduler started: checking holds every 5 minutes')
