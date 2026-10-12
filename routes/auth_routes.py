from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models.user import create_user, find_user_by_login, update_last_login, set_reset_token, verify_reset_token, update_password
from models.admin import Admin
from models.settings import Settings
from db import mongo, limiter
from utils.email_utils import send_reset_email
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


def safe_next_url(default_endpoint='user.index'):
    """Return the ?next= target only if it is a local path, so login can't
    be used to redirect visitors to another site."""
    target = (request.args.get('next') or request.form.get('next') or '').strip()
    if target.startswith('/') and not target.startswith('//') and '\\' not in target:
        return target
    return url_for(default_endpoint)


@auth_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit('5 per hour', methods=['POST'])
def signup():
    settings = Settings.find_one()
    next_url = safe_next_url()
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'dob': request.form.get('dob'),
            'nid': request.form.get('nid', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'phone': request.form.get('phone', '').strip(),
            'password': request.form.get('password'),
            'role': 'user'
        }

        # Basic validation
        required = ['first_name', 'last_name', 'email', 'phone', 'password']
        if any(not data[k] for k in required):
            flash('Please fill in all required fields', 'error')
            return render_template('auth/signup.html', settings=settings, next=next_url)

        # Uniqueness checks
        if mongo.db.users.find_one({'email': data['email']}):
            flash('Email already registered', 'error')
            return render_template('auth/signup.html', settings=settings, next=next_url)
        if mongo.db.users.find_one({'phone': data['phone']}):
            flash('Phone already registered', 'error')
            return render_template('auth/signup.html', settings=settings, next=next_url)

        try:
            nomad_id = create_user(data)
        except Exception as e:
            flash(f'Error creating user: {e}', 'error')
            return render_template('auth/signup.html', settings=settings, next=next_url)

        user = mongo.db.users.find_one({'user_id': nomad_id})
        if user:
            session['user_logged_in'] = True
            session['user_id'] = str(user['_id'])
            session['user_name'] = user.get('first_name', 'User')
            flash('Account created successfully!', 'success')
            return redirect(next_url)

    return render_template('auth/signup.html', settings=settings, next=next_url)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute;50 per hour', methods=['POST'])
def login():
    settings = Settings.find_one()
    next_url = safe_next_url()
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        # Try user login first (email or user_id)
        user = find_user_by_login(identifier)
        if user:
            try:
                if not check_password_hash(user['password'], password):
                    raise ValueError('bad-password')
            except Exception:
                flash('Invalid login credentials', 'error')
                return render_template('auth/login.html', settings=settings, next=next_url)

            session['user_logged_in'] = True
            session['user_id'] = str(user['_id'])
            session['user_name'] = user.get('first_name', 'User')
            update_last_login(user.get('user_id'))
            return redirect(next_url or url_for('user.index'))

        # Fallback: admin login via same form using username
        admin = Admin.find_by_username(identifier)
        if admin and Admin.verify_password(admin, password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin.get('username', identifier)
            session['admin_role'] = admin.get('role', 'branch_admin' if admin.get('location_id') else 'superadmin')
            session['admin_location_id'] = str(admin['location_id']) if admin.get('location_id') else None
            if admin.get('location_id'):
                from models.location import Location
                loc = Location.find_by_id(str(admin['location_id']))
                session['admin_location_name'] = loc.get('name') if loc else None
            else:
                session['admin_location_name'] = None
            return redirect(url_for('admin.dashboard'))

        flash('Invalid login credentials', 'error')
        return render_template('auth/login.html', settings=settings, next=next_url)

    return render_template('auth/login.html', settings=settings, next=next_url)


@auth_bp.route('/logout')
def logout():
    session_keys = ['user_logged_in', 'user_id', 'user_name']
    for k in session_keys:
        session.pop(k, None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('user.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('5 per hour', methods=['POST'])
def forgot_password():
    settings = Settings.find_one()
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = mongo.db.users.find_one({'email': email})
        
        if user:
            token = secrets.token_urlsafe(32)
            expiration = datetime.utcnow() + timedelta(hours=1)
            set_reset_token(email, token, expiration)
            send_reset_email(email, token)
            
        # Always flash success to avoid account enumeration
        flash('If that email is registered, a reset link has been sent.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', settings=settings)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit('10 per hour', methods=['POST'])
def reset_password(token):
    settings = Settings.find_one()
    user = verify_reset_token(token)
    
    if not user:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', settings=settings, token=token)
            
        update_password(user['_id'], password)
        flash('Password has been reset successfully.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', settings=settings, token=token)
