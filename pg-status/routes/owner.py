"""
Owner routes — Home, Dashboard, Property Add, Bed Manage, Profile
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.property import Property
from models.floor import Floor
from models.room import Room
from models.bed import Bed
from models.hold import Hold
from models.amenity import Amenity
from models.notification import Notification

logger = logging.getLogger(__name__)
owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


def owner_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'owner':
            flash('Access denied. Owners only.', 'error')
            return redirect(url_for('landing'))
        return f(*args, **kwargs)
    return decorated


def verify_ownership(property_id):
    """Verify the current user owns this property."""
    prop = Property.query.get_or_404(property_id)
    if prop.owner_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return None
    return prop


@owner_bp.route('/home')
@login_required
@owner_required
def home():
    properties = Property.query.filter_by(
        owner_id=current_user.id, is_active=True).all()

    # Pending hold requests across all properties
    pending_holds = Hold.query.join(Bed).join(Room).join(Floor).join(Property).filter(
        Property.owner_id == current_user.id,
        Hold.status == 'pending'
    ).order_by(Hold.requested_at.desc()).all()

    # Stats
    total_green = total_yellow = total_red = 0
    for p in properties:
        counts = p.get_bed_counts()
        total_green += counts['green']
        total_yellow += counts['yellow']
        total_red += counts['red']

    unread = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()

    return render_template('owner/home.html',
                           properties=properties,
                           pending_holds=pending_holds,
                           stats={
                               'green': total_green,
                               'yellow': total_yellow,
                               'red': total_red,
                               'pending': len(pending_holds),
                               'unread': unread
                           }
                           )


@owner_bp.route('/dashboard')
@login_required
@owner_required
def dashboard():
    properties = Property.query.filter_by(owner_id=current_user.id).all()

    # Hold statistics
    total_holds = Hold.query.join(Bed).join(Room).join(Floor).join(Property).filter(
        Property.owner_id == current_user.id
    ).count()

    booked = Hold.query.join(Bed).join(Room).join(Floor).join(Property).filter(
        Property.owner_id == current_user.id,
        Hold.status == 'booked'
    ).count()

    return render_template('owner/dashboard.html',
                           properties=properties,
                           stats={
                               'total_holds': total_holds,
                               'booked': booked,
                               'conversion': round((booked / total_holds * 100) if total_holds > 0 else 0, 1)
                           }
                           )


@owner_bp.route('/property/add', methods=['GET', 'POST'])
@login_required
@owner_required
def property_add():
    if request.method == 'POST':
        import json

        # Basic info
        name = request.form.get('name', '').strip()
        prop_type = request.form.get('property_type', '').strip()
        gender = request.form.get('gender_allowed', 'Any').strip()
        description = request.form.get('description', '').strip()
        address_line = request.form.get('address_line', '').strip()
        locality = request.form.get('locality', '').strip()
        city = request.form.get('city', '').strip()
        pincode = request.form.get('pincode', '').strip()

        if not name or not prop_type:
            flash('Property name and type are required.', 'error')
            return render_template('owner/property_add.html')

        prop = Property(
            owner_id=current_user.id, name=name, property_type=prop_type,
            description=description, address_line=address_line,
            locality=locality, city=city, pincode=pincode,
            gender_allowed=gender, is_active=True
        )
        db.session.add(prop)
        db.session.flush()

        # Amenities
        amenities_str = request.form.get('amenities', '[]')
        try:
            amenity_list = json.loads(amenities_str)
        except json.JSONDecodeError:
            amenity_list = []
        for a_name in amenity_list:
            db.session.add(Amenity(property_id=prop.id, name=a_name))

        # Floors, rooms, beds from JSON structure
        structure_str = request.form.get('structure', '[]')
        try:
            floors_data = json.loads(structure_str)
        except json.JSONDecodeError:
            floors_data = []

        bed_labels = ['Bed A', 'Bed B', 'Bed C']
        for fi, floor_data in enumerate(floors_data):
            floor = Floor(
                property_id=prop.id,
                floor_number=fi,
                floor_label=floor_data.get('label', f'Floor {fi}')
            )
            db.session.add(floor)
            db.session.flush()

            for room_data in floor_data.get('rooms', []):
                sharing = int(room_data.get('sharing_type', 1))
                room = Room(
                    floor_id=floor.id,
                    room_number=room_data.get('room_number', f'{fi}01'),
                    sharing_type=sharing,
                    rent_per_bed=int(room_data.get('rent_per_bed', 0)),
                    has_ac=room_data.get('has_ac', False),
                    has_attached_bath=room_data.get('has_attached_bath', False)
                )
                db.session.add(room)
                db.session.flush()

                for bi in range(min(sharing, 3)):
                    bed = Bed(
                        room_id=room.id,
                        bed_label=bed_labels[bi],
                        status='green'
                    )
                    db.session.add(bed)

        db.session.commit()
        logger.info(
            f'Property created: {
                prop.name} by owner {
                current_user.id}')
        flash('Property added successfully!', 'success')
        return redirect(url_for('owner.bed_manage', property_id=prop.id))

    return render_template('owner/property_add.html')


@owner_bp.route('/property/<int:property_id>/beds')
@login_required
@owner_required
def bed_manage(property_id):
    prop = verify_ownership(property_id)
    if not prop:
        return redirect(url_for('owner.home'))

    floors = prop.floors.order_by('floor_number').all()

    # Get pending holds for this property
    pending_holds = Hold.query.join(Bed).join(Room).join(Floor).filter(
        Floor.property_id == property_id,
        Hold.status == 'pending'
    ).all()

    return render_template('owner/bed_manage.html',
                           property=prop,
                           floors=floors,
                           pending_holds=pending_holds
                           )


@owner_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@owner_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get(
            'full_name', current_user.full_name).strip()
        current_user.phone = request.form.get(
            'phone', current_user.phone).strip()
        current_user.bio = request.form.get('bio', '').strip()
        current_user.city = request.form.get('city', '').strip()
        current_user.college_or_work = request.form.get(
            'college_or_work', '').strip()
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('owner.profile'))

    return render_template('owner/profile.html')
