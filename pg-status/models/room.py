from extensions import db
from datetime import datetime


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    floor_id = db.Column(
        db.Integer,
        db.ForeignKey('floors.id'),
        nullable=False,
        index=True)
    room_number = db.Column(db.String(20), nullable=False)
    sharing_type = db.Column(
        db.Integer,
        nullable=False,
        default=1)  # 1, 2, or 3
    rent_per_bed = db.Column(db.Integer, nullable=True)
    has_ac = db.Column(db.Boolean, default=False)
    has_attached_bath = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    beds = db.relationship(
        'Bed',
        backref='room',
        lazy='dynamic',
        cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'floor_id': self.floor_id,
            'room_number': self.room_number,
            'sharing_type': self.sharing_type,
            'rent_per_bed': self.rent_per_bed,
            'has_ac': self.has_ac,
            'has_attached_bath': self.has_attached_bath,
            'beds': [b.to_dict() for b in self.beds]
        }

    def __repr__(self):
        return f'<Room {self.room_number}>'
