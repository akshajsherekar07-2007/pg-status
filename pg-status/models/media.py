from extensions import db
from datetime import datetime


class PropertyMedia(db.Model):
    __tablename__ = 'property_media'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(
        db.Integer,
        db.ForeignKey('properties.id'),
        nullable=False,
        index=True)
    floor_id = db.Column(db.Integer, db.ForeignKey('floors.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=True)
    media_type = db.Column(db.String(20), nullable=False, default='property')
    # property, floor, room, bed
    file_path = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'floor_id': self.floor_id,
            'room_id': self.room_id,
            'bed_id': self.bed_id,
            'media_type': self.media_type,
            'file_path': self.file_path,
            'is_primary': self.is_primary,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

    def __repr__(self):
        return f'<PropertyMedia {self.media_type} - {self.file_path}>'
