from extensions import db
from datetime import datetime


class BedStatusLog(db.Model):
    __tablename__ = 'bed_status_log'

    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(
        db.Integer,
        db.ForeignKey('beds.id'),
        nullable=False,
        index=True)
    old_status = db.Column(db.String(10), nullable=False)
    new_status = db.Column(db.String(10), nullable=False)
    changed_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True)
    # hold_accepted, manual_mark, override, etc.
    action_type = db.Column(db.String(50), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'bed_id': self.bed_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'action_type': self.action_type,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }

    def __repr__(self):
        return f'<BedStatusLog {self.old_status}→{self.new_status}>'
