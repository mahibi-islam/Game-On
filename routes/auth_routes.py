from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models.user import create_user, find_user_by_login, update_last_login, set_reset_token, verify_reset_token, update_password
from models.admin import Admin
from models.settings import Settings
from db import mongo
from utils.email_utils import send_reset_email
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    settings = Settings.find_one()
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
            return render_template('auth/signup.html', settings=settings)

        # Uniqueness checks
        if mongo.db.users.find_one({'email': data['email']}):
            flash('Email already registered', 'error')
            return render_template('auth/signup.html', settings=settings)
        if mongo.db.users.find_one({'phone': data['phone']}):
            flash('Phone already registered', 'error')
            return render_template('auth/signup.html', settings=settings)

        try:
            nomad_id = create_user(data)
        except Exception as e:
            flash(f'Error creating user: {e}', 'error')
            return render_template('auth/signup.html', settings=settings)

        user = mongo.db.users.find_one({'user_id': nomad_id})
        if user:
            session['user_logged_in'] = True
            session['user_id'] = str(user['_id'])
            session['user_name'] = user.get('first_name', 'User')
            flash('Account created successfully!', 'success')
            return redirect(url_for('user.index'))

    return render_template('auth/signup.html', settings=settings)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    settings = Settings.find_one()
    next_url = request.args.get('next') or request.form.get('next') or url_for('user.index')
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
        if not admin:
            try:
                Admin.init_defaults()
                admin = Admin.find_by_username(identifier)
            except Exception:
                admin = None
        if admin and Admin.verify_password(admin, password):
            session['admin_logged_in'] = True
            session['admin_username'] = identifier
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
