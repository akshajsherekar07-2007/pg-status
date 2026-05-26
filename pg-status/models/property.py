from extensions import db
from datetime import datetime


class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True)
    name = db.Column(db.String(200), nullable=False)
    property_type = db.Column(db.String(20),
                              nullable=False)  # 'PG', 'Hostel', 'Flat'
    description = db.Column(db.Text, nullable=True)
    address_line = db.Column(db.String(300), nullable=True)
    locality = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    gender_allowed = db.Column(db.String(10),
                               default='Any')  # 'Male', 'Female', 'Any'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    floors = db.relationship(
        'Floor',
        backref='property',
        lazy='dynamic',
        cascade='all, delete-orphan')
    amenities = db.relationship(
        'Amenity',
        backref='property',
        lazy='dynamic',
        cascade='all, delete-orphan')
    media = db.relationship(
        'PropertyMedia',
        backref='property',
        lazy='dynamic',
        cascade='all, delete-orphan')

    def get_bed_counts(self):
        """Returns dict with green, yellow, red bed counts."""
        counts = {'green': 0, 'yellow': 0, 'red': 0, 'total': 0}
        for floor in self.floors:
            for room in floor.rooms:
                for bed in room.beds:
                    counts[bed.status] = counts.get(bed.status, 0) + 1
                    counts['total'] += 1
        return counts

    def get_min_rent(self):
        """Returns minimum rent per bed across all rooms."""
        min_rent = None
        for floor in self.floors:
            for room in floor.rooms:
                if room.rent_per_bed and (
                        min_rent is None or room.rent_per_bed < min_rent):
                    min_rent = room.rent_per_bed
        return min_rent or 0

    def get_primary_image(self):
        """Returns the primary image path or a default."""
        primary = self.media.filter_by(
            media_type='property', is_primary=True).first()
        if primary:
            return primary.file_path
        first = self.media.filter_by(media_type='property').first()
        return first.file_path if first else None

    def to_dict(self):
        bed_counts = self.get_bed_counts()
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'property_type': self.property_type,
            'description': self.description,
            'address_line': self.address_line,
            'locality': self.locality,
            'city': self.city,
            'pincode': self.pincode,
            'gender_allowed': self.gender_allowed,
            'is_active': self.is_active,
            'min_rent': self.get_min_rent(),
            'bed_counts': bed_counts,
            'primary_image': self.get_primary_image(),
            'amenities': [a.name for a in self.amenities],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Property {self.name}>'
