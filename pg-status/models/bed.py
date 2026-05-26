from extensions import db
from datetime import datetime


class Bed(db.Model):
    __tablename__ = 'beds'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(
        db.Integer,
        db.ForeignKey('rooms.id'),
        nullable=False,
        index=True)
    bed_label = db.Column(
        db.String(20),
        nullable=False,
        default='Bed A')  # Bed A, Bed B, Bed C
    status = db.Column(
        db.String(10),
        nullable=False,
        default='green')  # green, yellow, red
    occupied_since = db.Column(db.DateTime, nullable=True)
    last_status_change = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    holds = db.relationship('Hold', backref='bed', lazy='dynamic')

    def get_active_hold(self):
        """Returns the currently active hold on this bed, if any."""
        return self.holds.filter_by(status='active').first()

    def get_pending_hold(self):
        """Returns a pending hold on this bed, if any."""
        return self.holds.filter_by(status='pending').first()

    def to_dict(self):
        active_hold = self.get_active_hold()
        pending_hold = self.get_pending_hold()
        result = {
            'id': self.id,
            'room_id': self.room_id,
            'bed_label': self.bed_label,
            'status': self.status,
            'occupied_since': self.occupied_since.isoformat() if self.occupied_since else None,
            'last_status_change': self.last_status_change.isoformat() if self.last_status_change else None,
        }
        if active_hold:
            result['active_hold'] = {
                'id': active_hold.id,
                'student_name': active_hold.student.full_name,
                'student_score': active_hold.student.reliability_score,
                'expires_at': active_hold.expires_at.isoformat() if active_hold.expires_at else None,
                'hold_days': active_hold.hold_days
            }
        if pending_hold:
            result['pending_hold'] = {
                'id': pending_hold.id,
                'student_name': pending_hold.student.full_name,
                'student_score': pending_hold.student.reliability_score,
                'hold_days': pending_hold.hold_days,
                'requested_at': pending_hold.requested_at.isoformat()
            }
        return result

    def __repr__(self):
        return f'<Bed {self.bed_label} ({self.status})>'
