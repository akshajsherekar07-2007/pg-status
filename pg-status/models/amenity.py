from extensions import db


class Amenity(db.Model):
    __tablename__ = 'amenities'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(
        db.Integer,
        db.ForeignKey('properties.id'),
        nullable=False,
        index=True)
    name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'name': self.name
        }

    def __repr__(self):
        return f'<Amenity {self.name}>'
