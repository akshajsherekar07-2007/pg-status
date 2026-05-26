from extensions import db
from datetime import datetime


class Floor(db.Model):
    __tablename__ = 'floors'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(
        db.Integer,
        db.ForeignKey('properties.id'),
        nullable=False,
        index=True)
    floor_number = db.Column(
        db.Integer,
        nullable=False,
        default=0)  # 0 = ground
    floor_label = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rooms = db.relationship(
        'Room',
        backref='floor',
        lazy='dynamic',
        cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'floor_number': self.floor_number,
            'floor_label': self.floor_label or f'Floor {self.floor_number}',
            'rooms': [r.to_dict() for r in self.rooms]
        }

    def __repr__(self):
        return f'<Floor {self.floor_label or self.floor_number}>'
