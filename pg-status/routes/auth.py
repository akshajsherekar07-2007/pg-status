"""
Auth routes — Register, Login, Logout, Profile Setup
"""
import logging
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, limiter
from models.user import User

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("30/hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.redirect_home'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', '')

        # Server-side validation
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if not phone or len(phone) < 10:
            errors.append('Valid phone number is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if role not in ('student', 'owner'):
            errors.append('Please select a role.')
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/register.html',
                                   form_data=request.form)

        pw_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name=full_name, email=email, phone=phone,
            password_hash=pw_hash, role=role
        )
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        logger.info(f'User registered: {email} as {role}')
        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.profile_setup'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("50/15minutes")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.redirect_home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode(
                'utf-8'), user.password_hash.encode('utf-8')):
            login_user(user, remember=remember)
            logger.info(f'User logged in: {email}')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('auth.redirect_home'))
        else:
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', email=email)

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logger.info(f'User logged out: {current_user.email}')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))


@auth_bp.route('/profile/setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', '').strip()
        current_user.city = request.form.get('city', '').strip()
        current_user.college_or_work = request.form.get(
            'college_or_work', '').strip()
        current_user.is_profile_complete = True
        db.session.commit()
        flash('Profile setup complete!', 'success')
        return redirect(url_for('auth.redirect_home'))

    return render_template('auth/profile_setup.html')


@auth_bp.route('/home')
@login_required
def redirect_home():
    if current_user.role == 'student':
        return redirect(url_for('student.home'))
    return redirect(url_for('owner.home'))
