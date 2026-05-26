"""
Score Service — Reliability score adjustments.
"""
import logging
from datetime import datetime, timedelta
from extensions import db

logger = logging.getLogger(__name__)

SCORE_FLOOR = 0
SCORE_CEILING = 100


def clamp_score(score):
    return max(SCORE_FLOOR, min(SCORE_CEILING, score))


def adjust_score_expire(student):
    """Hold expired: -5 points."""
    old = student.reliability_score
    student.reliability_score = clamp_score(old - 5)
    db.session.commit()
    logger.info(
        f'Score adjusted (expire): user={student.id}, {old}->{student.reliability_score}')


def adjust_score_cancel(hold):
    """Cancel hold: -10 if < 6hrs into hold, +5 if 48h+ remaining."""
    student = hold.student
    old = student.reliability_score
    if hold.status == 'active' and hold.expires_at:
        remaining = (hold.expires_at - datetime.utcnow()).total_seconds()
        total = timedelta(days=hold.hold_days).total_seconds()
        elapsed = total - remaining
        if elapsed < 6 * 3600:
            student.reliability_score = clamp_score(old - 10)
        elif remaining > 48 * 3600:
            student.reliability_score = clamp_score(old + 5)
    db.session.commit()
    logger.info(
        f'Score adjusted (cancel): user={student.id}, {old}->{student.reliability_score}')


def adjust_score_booking(student):
    """Hold to booking: +10 points."""
    old = student.reliability_score
    student.reliability_score = clamp_score(old + 10)
    db.session.commit()
    logger.info(
        f'Score adjusted (booking): user={student.id}, {old}->{student.reliability_score}')
