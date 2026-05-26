from extensions import db
from datetime import datetime


class Hold(db.Model):
    __tablename__ = 'holds'

    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(
        db.Integer,
        db.ForeignKey('beds.id'),
        nullable=False,
        index=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hold_days = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 5, 7
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(25), nullable=False, default='pending')
    # pending, active, rejected, expired, cancelled_by_student, cancelled_by_override, booked
    reject_reason = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'bed_id': self.bed_id,
            'student_id': self.student_id,
            'owner_id': self.owner_id,
            'hold_days': self.hold_days,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'status': self.status,
            'reject_reason': self.reject_reason,
            'bed_label': self.bed.bed_label if self.bed else None,
            'room_number': self.bed.room.room_number if self.bed and self.bed.room else None,
            'property_name': self.bed.room.floor.property.name if self.bed else None,
            'property_id': self.bed.room.floor.property.id if self.bed else None,
            'student_name': self.student.full_name if self.student else None,
            'student_score': self.student.reliability_score if self.student else None,
            'rent_per_bed': self.bed.room.rent_per_bed if self.bed and self.bed.room else None
        }

    def __repr__(self):
        return f'<Hold {self.id} ({self.status})>'
