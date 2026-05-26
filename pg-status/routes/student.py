"""
Student routes — Home, Browse, Property Detail, Dashboard, Profile
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.property import Property
from models.hold import Hold
from models.notification import Notification

logger = logging.getLogger(__name__)
student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    """Decorator to ensure user is a student."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied. Students only.', 'error')
            return redirect(url_for('landing'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/home')
@login_required
@student_required
def home():
    # Active holds
    active_holds = Hold.query.filter(
        Hold.student_id == current_user.id,
        Hold.status.in_(['pending', 'active'])
    ).all()

    # Featured properties
    properties = Property.query.filter_by(is_active=True).limit(6).all()

    # Stats
    total_holds = Hold.query.filter_by(student_id=current_user.id).count()
    active_count = len(active_holds)

    unread_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    return render_template('student/home.html',
                           active_holds=active_holds,
                           properties=properties,
                           stats={
                               'total_holds': total_holds,
                               'active_holds': active_count,
                               'score': current_user.reliability_score,
                               'unread': unread_count
                           }
                           )


@student_bp.route('/browse')
@login_required
@student_required
def browse():
    # Get filter parameters
    search = request.args.get('search', '').strip()
    prop_type = request.args.get('type', '')
    gender = request.args.get('gender', '')
    min_budget = request.args.get('min_budget', type=int)
    max_budget = request.args.get('max_budget', type=int)
    sharing = request.args.get('sharing', type=int)
    amenities_filter = request.args.getlist('amenities')

    query = Property.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            db.or_(
                Property.name.ilike(f'%{search}%'),
                Property.locality.ilike(f'%{search}%'),
                Property.city.ilike(f'%{search}%')
            )
        )
    if prop_type:
        query = query.filter_by(property_type=prop_type)
    if gender:
        query = query.filter(Property.gender_allowed.in_([gender, 'Any']))

    properties = query.order_by(Property.created_at.desc()).all()

    # Post-query filters (budget, sharing, amenities require joining)
    if min_budget or max_budget or sharing or amenities_filter:
        filtered = []
        for p in properties:
            min_rent = p.get_min_rent()
            if min_budget and min_rent < min_budget:
                continue
            if max_budget and min_rent > max_budget:
                continue
            if amenities_filter:
                prop_amenities = {a.name for a in p.amenities}
                if not set(amenities_filter).issubset(prop_amenities):
                    continue
            filtered.append(p)
        properties = filtered

    return render_template('student/browse.html',
                           properties=properties,
                           filters={
                               'search': search,
                               'type': prop_type,
                               'gender': gender,
                               'min_budget': min_budget,
                               'max_budget': max_budget,
                               'sharing': sharing,
                               'amenities': amenities_filter
                           }
                           )


@student_bp.route('/property/<int:property_id>')
@login_required
@student_required
def property_detail(property_id):
    prop = Property.query.get_or_404(property_id)
    floors = prop.floors.order_by('floor_number').all()

    # Get student's active holds
    student_holds = Hold.query.filter(
        Hold.student_id == current_user.id,
        Hold.status.in_(['pending', 'active'])
    ).all()
    held_bed_ids = {h.bed_id for h in student_holds}

    return render_template('student/property_detail.html',
                           property=prop,
                           floors=floors,
                           held_bed_ids=held_bed_ids,
                           active_hold_count=len(student_holds)
                           )


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    active_holds = Hold.query.filter(
        Hold.student_id == current_user.id,
        Hold.status.in_(['pending', 'active'])
    ).order_by(Hold.requested_at.desc()).all()

    history = Hold.query.filter(
        Hold.student_id == current_user.id,
        Hold.status.in_(['expired', 'cancelled_by_student',
                        'cancelled_by_override', 'booked', 'rejected'])
    ).order_by(Hold.requested_at.desc()).limit(20).all()

    return render_template('student/dashboard.html',
                           active_holds=active_holds,
                           history=history,
                           score=current_user.reliability_score
                           )


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
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
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html')
