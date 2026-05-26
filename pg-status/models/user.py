from extensions import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'student' or 'owner'
    profile_photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    college_or_work = db.Column(db.String(200), nullable=True)
    reliability_score = db.Column(db.Integer, default=100)
    is_profile_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    properties = db.relationship('Property', backref='owner', lazy='dynamic')
    student_holds = db.relationship(
        'Hold',
        foreign_keys='Hold.student_id',
        backref='student',
        lazy='dynamic')
    owner_holds = db.relationship(
        'Hold',
        foreign_keys='Hold.owner_id',
        backref='owner_user',
        lazy='dynamic')
    notifications = db.relationship(
        'Notification',
        backref='user',
        lazy='dynamic',
        order_by='Notification.created_at.desc()')

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'profile_photo': self.profile_photo,
            'bio': self.bio,
            'city': self.city,
            'college_or_work': self.college_or_work,
            'reliability_score': self.reliability_score,
            'is_profile_complete': self.is_profile_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
